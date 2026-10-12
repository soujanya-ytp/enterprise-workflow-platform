from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_health():
 assert client.get("/health").json()=={"status":"ok"}
def test_login_rejects_missing_credentials():
 r=client.post("/api/auth/login",json={"email":"missing@example.com","password":"bad-password"})
 assert r.status_code==401
def test_protected_route_requires_token():
 r=client.get("/api/dashboard") if "enterprise-workflow-platform"!="supply-chain-platform" else client.post("/api/products",json={"sku":"T-1","name":"Test"})
 assert r.status_code==401
