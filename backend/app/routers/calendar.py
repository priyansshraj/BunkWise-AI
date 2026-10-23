from datetime import date
from fastapi import APIRouter, Depends, HTTPException
import holidays
from sqlmodel import Session, select
from app.db import get_session
from app.models import CustomHoliday, CustomHolidayCreate, StudentProfile

router = APIRouter(prefix="/api/v1/holidays", tags=["Calendar & Holidays"])

@router.post("/custom", response_model=CustomHoliday, status_code=201)
def add_custom_holiday(payload: CustomHolidayCreate, session: Session = Depends(get_session)):
    custom = CustomHoliday.model_validate(payload)
    session.add(custom)
    session.commit()
    session.refresh(custom)
    return custom

@router.get("/student/{student_id}")
def get_merged_holidays(student_id: int, session: Session = Depends(get_session)):
    student = session.get(StudentProfile, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    today = date.today()
    years = [today.year, today.year + 1]
    official = holidays.country_holidays("IN", subdiv=student.state_code, years=years)
    upcoming_official = {
        str(k): v for k, v in sorted(official.items()) if k >= today
    }

    custom_rows = session.exec(
        select(CustomHoliday).where(CustomHoliday.student_id == student_id)
    ).all()

    return {
        "student_id": student_id,
        "state_code": student.state_code,
        "official_upcoming_holidays": upcoming_official,
        "custom_college_holidays": [
            {
                "id": row.id,
                "date": str(row.holiday_date),
                "title": row.title,
                "is_working_override": row.is_working_override,
            }
            for row in custom_rows
        ],
    }
