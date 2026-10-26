from fastapi.testclient import TestClient
from app.main import app

def test_agent_asks_clarification_for_unknown_student():
    client = TestClient(app)
    res = client.post(
        "/api/v1/agent/chat",
        json={
            "student_id": 9999,
            "message": "Can I bunk tomorrow?",
            "planned_absent_dates": ["string"],
            "thread_id": "test-thread",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["needs_clarification"] is True
    assert data["planned_absent_dates"] == []
    assert "student_profile" in data["missing_fields"][0]
