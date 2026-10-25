from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db import get_session
from app.models import (
    AttendanceMarkRequest,
    StudentProfile,
    StudentProfileCreate,
    StudentProfileUpdate,
    Subject,
    SubjectCreate,
    TimetableSlot,
    TimetableSlotCreate,
)

router = APIRouter(prefix="/api/v1", tags=["Attendance & Timetable"])

@router.post("/students", response_model=StudentProfile, status_code=201)
def create_student(payload: StudentProfileCreate, session: Session = Depends(get_session)):
    student = StudentProfile.model_validate(payload)
    session.add(student)
    session.commit()
    session.refresh(student)
    return student

@router.get("/students/{student_id}", response_model=StudentProfile)
def get_student(student_id: int, session: Session = Depends(get_session)):
    student = session.get(StudentProfile, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return student

@router.patch("/students/{student_id}", response_model=StudentProfile)
def update_student(
    student_id: int, payload: StudentProfileUpdate, session: Session = Depends(get_session)
):
    student = session.get(StudentProfile, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    update_data = payload.model_dump(exclude_unset=True)
    student.sqlmodel_update(update_data)
    session.add(student)
    session.commit()
    session.refresh(student)
    return student

@router.post("/subjects", response_model=Subject, status_code=201)
def create_subject(payload: SubjectCreate, session: Session = Depends(get_session)):
    if payload.classes_attended > payload.classes_conducted:
        raise HTTPException(
            status_code=400,
            detail="classes_attended cannot be greater than classes_conducted",
        )
    subject = Subject.model_validate(payload)
    session.add(subject)
    session.commit()
    session.refresh(subject)
    return subject

@router.get("/students/{student_id}/subjects", response_model=List[Subject])
def list_subjects(student_id: int, session: Session = Depends(get_session)):
    statement = select(Subject).where(Subject.student_id == student_id)
    return list(session.exec(statement).all())

@router.post("/subjects/{subject_id}/mark", response_model=Subject)
def mark_attendance(
    subject_id: int, payload: AttendanceMarkRequest, session: Session = Depends(get_session)
):
    subject = session.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    status_clean = payload.status.strip().lower()
    if status_clean not in ("present", "absent"):
        raise HTTPException(status_code=400, detail="status must be 'present' or 'absent'")
    subject.classes_conducted += payload.classes_count
    if status_clean == "present":
        subject.classes_attended += payload.classes_count
    session.add(subject)
    session.commit()
    session.refresh(subject)
    return subject

@router.post("/timetable", response_model=TimetableSlot, status_code=201)
def add_timetable_slot(payload: TimetableSlotCreate, session: Session = Depends(get_session)):
    slot = TimetableSlot.model_validate(payload)
    session.add(slot)
    session.commit()
    session.refresh(slot)
    return slot

@router.get("/students/{student_id}/timetable", response_model=List[TimetableSlot])
def get_student_timetable(student_id: int, session: Session = Depends(get_session)):
    statement = (
        select(TimetableSlot)
        .join(Subject, TimetableSlot.subject_id == Subject.id)
        .where(Subject.student_id == student_id)
    )
    return list(session.exec(statement).all())

@router.get("/students/{student_id}/bunk-plan")
def get_student_bunk_plan(student_id: int, session: Session = Depends(get_session)):
    from datetime import date as dt_date
    from app.models.holiday import CustomHoliday
    from app.services.bunk_calculator import calculate_subject_bunk_plan

    student = session.get(StudentProfile, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    if not student.expected_exam_date:
        raise HTTPException(
            status_code=400,
            detail="expected_exam_date is not set on StudentProfile. Update it first.",
        )

    subjects = session.exec(select(Subject).where(Subject.student_id == student_id)).all()
    slots = session.exec(
        select(TimetableSlot)
        .join(Subject, TimetableSlot.subject_id == Subject.id)
        .where(Subject.student_id == student_id)
    ).all()
    custom_holidays = session.exec(
        select(CustomHoliday).where(CustomHoliday.student_id == student_id)
    ).all()

    reports = [
        calculate_subject_bunk_plan(
            subject=sub,
            slots=slots,
            exam_date=student.expected_exam_date,
            state_code=student.state_code,
            is_saturday_working=student.is_saturday_working,
            custom_holidays=custom_holidays,
        )
        for sub in subjects
    ]
    return {
        "student_id": student.id,
        "student_name": student.name,
        "expected_exam_date": str(student.expected_exam_date),
        "subjects_report": reports,
    }
