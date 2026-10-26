import re
from datetime import date
from typing import Any, Dict, List
from langchain_core.tools import tool
from sqlmodel import Session, select
from app.models import CustomHoliday, StudentProfile, Subject, TimetableSlot
from app.services.bunk_calculator import calculate_subject_bunk_plan

def extract_iso_dates(text: str) -> List[str]:
    """Extracts any YYYY-MM-DD dates mentioned by the student in their chat message."""
    return re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text)

@tool
def run_student_bunk_simulation(
    student_id: int, planned_absent_dates: List[str], session: Session
) -> List[Dict[str, Any]]:
    """
    Runs the deterministic bunk calculator across all subjects for a student,
    factoring in Indian state holidays, custom college holidays, and planned_absent_dates.
    """
    student = session.get(StudentProfile, student_id)
    if not student or not student.expected_exam_date:
        return []

    subjects = session.exec(select(Subject).where(Subject.student_id == student_id)).all()
    slots = session.exec(
        select(TimetableSlot)
        .join(Subject, TimetableSlot.subject_id == Subject.id)
        .where(Subject.student_id == student_id)
    ).all()
    custom_holidays = session.exec(
        select(CustomHoliday).where(CustomHoliday.student_id == student_id)
    ).all()

    absent_set = {date.fromisoformat(d) for d in planned_absent_dates}

    return [
        calculate_subject_bunk_plan(
            subject=sub,
            slots=slots,
            exam_date=student.expected_exam_date,
            state_code=student.state_code,
            is_saturday_working=student.is_saturday_working,
            custom_holidays=custom_holidays,
            planned_absent_dates=absent_set,
        )
        for sub in subjects
    ]
