from fastapi import FastAPI
from fastapi.testclient import TestClient

from trackreco_platform.services.permissions import require_permission


app = FastAPI()


@app.get("/secure")
def secure(_: object = require_permission("publish")):
    return {"ok": True}


def test_permission_enforced():
    client = TestClient(app)
    denied = client.get("/secure", headers={"x-user-role": "viewer"})
    assert denied.status_code == 403
    ok = client.get("/secure", headers={"x-user-role": "admin"})
    assert ok.status_code == 200
