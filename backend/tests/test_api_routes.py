from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from app.db import get_session
from app.main import app

def test_full_student_bunk_plan_api_flow():
    # 1. Create an isolated in-memory SQLite database just for this test
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)

    def get_test_session():
        with Session(test_engine) as session:
            yield session

    # 2. Override FastAPI's database session dependency with our in-memory session
    app.dependency_overrides[get_session] = get_test_session
    client = TestClient(app)

    # 3. Create a student profile via POST /api/v1/students
    student_res = client.post(
        "/api/v1/students",
        json={
            "name": "Priyansh",
            "state_code": "BR",
            "default_target_pct": 75.0,
            "is_saturday_working": True,
            "expected_exam_date": "2026-12-15",
        },
    )
    assert student_res.status_code == 201
    student_id = student_res.json()["id"]

    # 4. Create a subject via POST /api/v1/subjects
    subj_res = client.post(
        "/api/v1/subjects",
        json={
            "student_id": student_id,
            "name": "Machine Learning",
            "code": "MCA-401",
            "classes_attended": 18,
            "classes_conducted": 20,
            "target_pct": 75.0,
        },
    )
    assert subj_res.status_code == 201
    subject_id = subj_res.json()["id"]

    # 5. Add a timetable slot (Monday = 0, 2 lectures)
    slot_res = client.post(
        "/api/v1/timetable",
        json={"subject_id": subject_id, "day_of_week": 0, "classes_count": 2},
    )
    assert slot_res.status_code == 201

    # 6. Fetch the computed bunk plan via GET /api/v1/students/{id}/bunk-plan
    plan_res = client.get(f"/api/v1/students/{student_id}/bunk-plan")
    assert plan_res.status_code == 200
    data = plan_res.json()
    assert data["student_name"] == "Priyansh"
    assert len(data["subjects_report"]) == 1
    assert data["subjects_report"][0]["subject_name"] == "Machine Learning"

    # Clean up override after test
    app.dependency_overrides.clear()
