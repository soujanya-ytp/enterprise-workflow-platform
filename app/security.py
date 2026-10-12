import os,hashlib,hmac,secrets,time,base64,json
SECRET=os.getenv("APP_SECRET","dev-only-change-this-secret")
def hash_password(password:str)->str:
 salt=secrets.token_bytes(16); digest=hashlib.pbkdf2_hmac("sha256",password.encode(),salt,180000); return base64.b64encode(salt+digest).decode()
def verify_password(password:str,encoded:str)->bool:
 try:
  raw=base64.b64decode(encoded); actual=hashlib.pbkdf2_hmac("sha256",password.encode(),raw[:16],180000); return hmac.compare_digest(actual,raw[16:])
 except Exception:return False
def issue_token(user_id:int,role:str)->str:
 payload=base64.urlsafe_b64encode(json.dumps({"sub":user_id,"role":role,"exp":int(time.time())+3600}).encode()).decode().rstrip("="); sig=hmac.new(os.getenv("APP_SECRET","dev-only-change-this-secret").encode(),payload.encode(),hashlib.sha256).hexdigest(); return payload+"."+sig
