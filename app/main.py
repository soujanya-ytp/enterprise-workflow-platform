from datetime import datetime, timedelta
import json, os, hmac, hashlib, base64, time
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import init_db, get_db
from app.models import User, WorkflowDefinition, ServiceRequest, Approval, Comment, AuditEvent
from app.security import hash_password, verify_password, issue_token
app=FastAPI(title="Enterprise Workflow & Operations Platform",version="1.0.0",description="Service request workflows, approval chains, audit and SLA operations")
@app.on_event("startup")
def startup():
 init_db(); db=next(get_db())
 try:
  if not db.query(WorkflowDefinition).first():
   db.add_all([WorkflowDefinition(name="Standard request",category="general",approval_roles_json='["manager","admin"]'),WorkflowDefinition(name="Urgent request",category="urgent",approval_roles_json='["admin"]')]); db.commit()
 finally: db.close()
class Register(BaseModel): email:str; password:str=Field(min_length=10); role:str="member"; department:str="Operations"
class Login(BaseModel): email:str; password:str
class RequestIn(BaseModel): title:str=Field(min_length=3,max_length=200); category:str="general"; priority:str="normal"
class Decision(BaseModel): decision:str; note:str=""
class CommentIn(BaseModel): body:str=Field(min_length=1,max_length=4000)
def current(auth,db):
 if not auth or not auth.startswith("Bearer "): raise HTTPException(401,"Bearer token required")
 try:
  payload,sig=auth[7:].split(".",1); expected=hmac.new(os.getenv("APP_SECRET","dev-only-change-this-secret").encode(),payload.encode(),hashlib.sha256).hexdigest()
  if not hmac.compare_digest(sig,expected): raise ValueError()
  d=json.loads(base64.urlsafe_b64decode(payload+"="*(-len(payload)%4)))
  if d["exp"]<time.time(): raise ValueError()
  u=db.get(User,int(d["sub"]))
  if not u: raise ValueError()
  return u
 except Exception: raise HTTPException(401,"Invalid or expired token")
@app.get("/health")
def health(): return {"status":"ok"}
@app.post("/api/auth/register",status_code=201)
def register(b:Register,db:Session=Depends(get_db)):
 email=b.email.lower().strip()
 if db.query(User).filter_by(email=email).first(): raise HTTPException(409,"Email already registered")
 u=User(email=email,password_hash=hash_password(b.password),role=b.role,department=b.department); db.add(u); db.commit(); db.refresh(u); return {"id":u.id,"email":u.email,"role":u.role}
@app.post("/api/auth/login")
def login(b:Login,db:Session=Depends(get_db)):
 u=db.query(User).filter_by(email=b.email.lower().strip()).first()
 if not u or not verify_password(b.password,u.password_hash): raise HTTPException(401,"Invalid credentials")
 return {"access_token":issue_token(u.id,u.role),"token_type":"bearer","user":{"id":u.id,"email":u.email,"role":u.role}}
@app.get("/api/workflows")
def workflows(db:Session=Depends(get_db)):
 return [{"id":x.id,"name":x.name,"category":x.category,"approval_roles":json.loads(x.approval_roles_json)} for x in db.query(WorkflowDefinition).filter_by(active=True).all()]
@app.post("/api/requests",status_code=201)
def create_request(b:RequestIn,authorization:str|None=Header(default=None),db:Session=Depends(get_db)):
 u=current(authorization,db)
 if b.priority not in ("low","normal","high","critical"): raise HTTPException(422,"Unsupported priority")
 wf=db.query(WorkflowDefinition).filter_by(category=b.category,active=True).first() or db.query(WorkflowDefinition).filter_by(category="general",active=True).first(); roles=json.loads(wf.approval_roles_json)
 r=ServiceRequest(title=b.title,category=b.category,priority=b.priority,requester_id=u.id,workflow_id=wf.id,status="pending_approval",current_step=0); db.add(r); db.flush()
 for i,role in enumerate(roles): db.add(Approval(request_id=r.id,step_number=i,approver_role=role))
 db.add(AuditEvent(request_id=r.id,actor_id=u.id,event_type="request.created",details_json=json.dumps({"title":b.title}))); db.commit(); db.refresh(r)
 return {"id":r.id,"title":r.title,"status":r.status,"current_step":r.current_step,"approval_steps":len(roles)}
@app.get("/api/requests")
def list_requests(status:str|None=None,priority:str|None=None,limit:int=50,offset:int=0,authorization:str|None=Header(default=None),db:Session=Depends(get_db)):
 u=current(authorization,db); q=db.query(ServiceRequest)
 if u.role not in ("admin","manager"): q=q.filter(ServiceRequest.requester_id==u.id)
 if status: q=q.filter(ServiceRequest.status==status)
 if priority: q=q.filter(ServiceRequest.priority==priority)
 return [{"id":r.id,"title":r.title,"category":r.category,"priority":r.priority,"status":r.status,"current_step":r.current_step} for r in q.order_by(ServiceRequest.created_at.desc()).offset(max(0,offset)).limit(min(max(1,limit),100)).all()]
@app.post("/api/requests/{rid}/decision")
def decide(rid:int,b:Decision,authorization:str|None=Header(default=None),db:Session=Depends(get_db)):
 u=current(authorization,db); r=db.get(ServiceRequest,rid)
 if not r: raise HTTPException(404,"Request not found")
 if b.decision not in ("approve","reject"): raise HTTPException(422,"decision must be approve or reject")
 steps=db.query(Approval).filter_by(request_id=rid).order_by(Approval.step_number).all()
 if r.status!="pending_approval" or r.current_step>=len(steps): raise HTTPException(409,"Request is not awaiting approval")
 step=steps[r.current_step]
 if u.role not in (step.approver_role,"admin"): raise HTTPException(403,"Not authorized for this approval step")
 step.status=b.decision; step.approver_id=u.id; step.decision_note=b.note; step.decided_at=datetime.utcnow()
 if b.decision=="reject": r.status="rejected"
 elif r.current_step+1>=len(steps): r.status="approved"
 else: r.current_step+=1
 db.add(AuditEvent(request_id=rid,actor_id=u.id,event_type="approval."+b.decision,details_json=json.dumps({"step":step.step_number,"note":b.note}))); db.commit(); return {"id":r.id,"status":r.status,"current_step":r.current_step}
@app.post("/api/requests/{rid}/comments",status_code=201)
def comment(rid:int,b:CommentIn,authorization:str|None=Header(default=None),db:Session=Depends(get_db)):
 u=current(authorization,db); r=db.get(ServiceRequest,rid)
 if not r: raise HTTPException(404,"Request not found")
 if u.role not in ("admin","manager") and r.requester_id!=u.id: raise HTTPException(403,"Forbidden")
 c=Comment(request_id=rid,author_id=u.id,body=b.body); db.add(c); db.add(AuditEvent(request_id=rid,actor_id=u.id,event_type="comment.created")); db.commit(); db.refresh(c); return {"id":c.id,"body":c.body,"created_at":c.created_at}
@app.get("/api/requests/{rid}/audit")
def audit(rid:int,authorization:str|None=Header(default=None),db:Session=Depends(get_db)):
 u=current(authorization,db); r=db.get(ServiceRequest,rid)
 if not r: raise HTTPException(404,"Request not found")
 if u.role not in ("admin","manager") and r.requester_id!=u.id: raise HTTPException(403,"Forbidden")
 return [{"id":e.id,"actor_id":e.actor_id,"event_type":e.event_type,"details":json.loads(e.details_json),"created_at":e.created_at} for e in db.query(AuditEvent).filter_by(request_id=rid).order_by(AuditEvent.created_at).all()]
@app.get("/api/dashboard")
def dashboard(authorization:str|None=Header(default=None),db:Session=Depends(get_db)):
 current(authorization,db); return {"requests_by_status":dict(db.query(ServiceRequest.status,func.count(ServiceRequest.id)).group_by(ServiceRequest.status).all()),"pending_approvals":db.query(Approval).filter_by(status="pending").count()}
@app.get("/api/escalations")
def escalations(hours:int=24,authorization:str|None=Header(default=None),db:Session=Depends(get_db)):
 u=current(authorization,db)
 if u.role not in ("admin","manager"): raise HTTPException(403,"Manager or admin required")
 cutoff=datetime.utcnow()-timedelta(hours=max(1,hours)); rows=db.query(Approval,ServiceRequest).join(ServiceRequest,Approval.request_id==ServiceRequest.id).filter(Approval.status=="pending",ServiceRequest.created_at<cutoff).all()
 return [{"approval_id":a.id,"request_id":r.id,"title":r.title,"age_hours":round((datetime.utcnow()-r.created_at).total_seconds()/3600,1)} for a,r in rows]
