from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
 __tablename__="users"
 id:Mapped[int]=mapped_column(primary_key=True)
 email:Mapped[str]=mapped_column(String(255),unique=True,index=True)
 password_hash:Mapped[str]=mapped_column(String(255))
 role:Mapped[str]=mapped_column(String(30),default="member")
 department:Mapped[str]=mapped_column(String(100),default="Operations")
class WorkflowDefinition(Base):
 __tablename__="workflow_definitions"
 id:Mapped[int]=mapped_column(primary_key=True)
 name:Mapped[str]=mapped_column(String(150))
 category:Mapped[str]=mapped_column(String(80),index=True)
 approval_roles_json:Mapped[str]=mapped_column(Text,default='["manager","admin"]')
 active:Mapped[bool]=mapped_column(Boolean,default=True)
class ServiceRequest(Base):
 __tablename__="service_requests"
 id:Mapped[int]=mapped_column(primary_key=True)
 title:Mapped[str]=mapped_column(String(200))
 category:Mapped[str]=mapped_column(String(80),index=True)
 priority:Mapped[str]=mapped_column(String(20),default="normal",index=True)
 status:Mapped[str]=mapped_column(String(30),default="pending_approval",index=True)
 requester_id:Mapped[int]=mapped_column(ForeignKey("users.id"))
 workflow_id:Mapped[int]=mapped_column(ForeignKey("workflow_definitions.id"))
 current_step:Mapped[int]=mapped_column(Integer,default=0)
 created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class Approval(Base):
 __tablename__="approvals"
 id:Mapped[int]=mapped_column(primary_key=True)
 request_id:Mapped[int]=mapped_column(ForeignKey("service_requests.id"),index=True)
 step_number:Mapped[int]=mapped_column(Integer)
 approver_role:Mapped[str]=mapped_column(String(30))
 approver_id:Mapped[int|None]=mapped_column(ForeignKey("users.id"),nullable=True)
 status:Mapped[str]=mapped_column(String(20),default="pending",index=True)
 decision_note:Mapped[str|None]=mapped_column(Text,nullable=True)
 decided_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
class Comment(Base):
 __tablename__="comments"
 id:Mapped[int]=mapped_column(primary_key=True)
 request_id:Mapped[int]=mapped_column(ForeignKey("service_requests.id"),index=True)
 author_id:Mapped[int]=mapped_column(ForeignKey("users.id"))
 body:Mapped[str]=mapped_column(Text)
 created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class AuditEvent(Base):
 __tablename__="audit_events"
 id:Mapped[int]=mapped_column(primary_key=True)
 request_id:Mapped[int]=mapped_column(ForeignKey("service_requests.id"),index=True)
 actor_id:Mapped[int]=mapped_column(ForeignKey("users.id"))
 event_type:Mapped[str]=mapped_column(String(80))
 details_json:Mapped[str]=mapped_column(Text,default="{}")
 created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
