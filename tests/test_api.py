import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client

def test_health(client):
    assert client.get("/health").json()["status"] == "ok"

def test_enquiry_workflow(client):
    response = client.post("/webhooks/enquiry", json={
        "message": "URGENT: the app has an error",
        "customer_name": "Example Customer"
    })
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["category"] == "technical"
    assert body["priority"] == "high"
    assert [step["name"] for step in body["steps"]][:3] == [
        "receive_enquiry", "classify_enquiry", "route_request"
    ]

def test_missing_run_returns_404(client):
    assert client.get("/runs/99999").status_code == 404
