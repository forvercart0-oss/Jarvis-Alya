import pytest
from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_chat_empty():
    resp = client.post("/api/chat", json={"message": ""})
    assert resp.status_code == 400
