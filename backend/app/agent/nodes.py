from datetime import date
from typing import List, Literal
from langchain_core.messages import AIMessage
from sqlmodel import Session, select
from app.agent.state import BunkAgentState
from app.agent.tools import extract_iso_dates
from app.db import engine
from app.models import CustomHoliday, StudentProfile, Subject, TimetableSlot
from app.services.bunk_calculator import calculate_subject_bunk_plan

def sanitize_iso_dates(raw_dates: List[str]) -> List[str]:
    """Filters a list of strings to keep only valid YYYY-MM-DD calendar dates."""
    valid: List[str] = []
    for item in raw_dates:
        for match in extract_iso_dates(str(item)):
            try:
                date.fromisoformat(match)
                if match not in valid:
                    valid.append(match)
            except ValueError:
                continue
    return valid

def context_loader_node(state: BunkAgentState) -> dict:
    """
    Node 1: Validates dates, auto-fills missing exam date if the student
    provides one in chat, and checks if any required database slots are still missing.
    """
    student_id = state["student_id"]
    latest_text = str(state["messages"][-1].content) if state.get("messages") else ""
    chat_dates = sanitize_iso_dates([latest_text])
    explicit_dates = sanitize_iso_dates(state.get("planned_absent_dates", []))

    missing: list[str] = []
    with Session(engine) as session:
        student = session.get(StudentProfile, student_id)
        if not student:
            missing.append("student_profile (Create your student profile first)")
            return {
                "missing_fields": missing,
                "needs_clarification": True,
                "planned_absent_dates": explicit_dates,
            }

        # Auto-fill expected_exam_date if it was missing and the student just sent a date in chat
        if not student.expected_exam_date and chat_dates and "exam" in latest_text.lower():
            student.expected_exam_date = date.fromisoformat(chat_dates[0])
            session.add(student)
            session.commit()
            session.refresh(student)
            chat_dates = chat_dates[1:]

        if not student.expected_exam_date:
            missing.append("expected_exam_date (When do your exams start? Reply e.g. 'My exam is on 2026-12-15')")

        subjects = session.exec(select(Subject).where(Subject.student_id == student_id)).all()
        if not subjects:
            missing.append("subjects (Add at least one subject with attended and conducted classes)")

        slots = session.exec(
            select(TimetableSlot)
            .join(Subject, TimetableSlot.subject_id == Subject.id)
            .where(Subject.student_id == student_id)
        ).all()
        if subjects and not slots:
            missing.append("weekly_timetable (Add your weekly class schedule in Timetable)")

    merged_planned = sanitize_iso_dates(explicit_dates + chat_dates)
    return {
        "missing_fields": missing,
        "needs_clarification": len(missing) > 0,
        "planned_absent_dates": merged_planned,
    }

def clarification_router(
    state: BunkAgentState,
) -> Literal["ask_clarification_node", "bunk_planner_node"]:
    if state.get("needs_clarification"):
        return "ask_clarification_node"
    return "bunk_planner_node"

def ask_clarification_node(state: BunkAgentState) -> dict:
    missing = state.get("missing_fields", [])
    bullet_questions = "\n".join(f"- {item}" for item in missing)
    question_msg = (
        "To calculate your exact safe bunks before exams, I need a few missing details:\n"
        f"{bullet_questions}\n\n"
        "Please update these or reply with the details so I can generate your bunk plan!"
    )
    return {
        "messages": [AIMessage(content=question_msg)],
        "final_answer": question_msg,
        "bunk_reports": [],
    }

def bunk_planner_node(state: BunkAgentState) -> dict:
    student_id = state["student_id"]
    planned_dates = sanitize_iso_dates(state.get("planned_absent_dates", []))
    absent_set = {date.fromisoformat(d) for d in planned_dates}

    with Session(engine) as session:
        student = session.get(StudentProfile, student_id)
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
                planned_absent_dates=absent_set,
            )
            for sub in subjects
        ]

    lines = [
        f"Here is your BunkWise-AI Attendance Plan up to your exam date ({student.expected_exam_date}):"
    ]
    if planned_dates:
        lines.append(f"Simulated Planned Leave Dates: {', '.join(sorted(planned_dates))}")

    for rep in reports:
        if rep["status"] == "SAFE_TO_BUNK":
            verdict = f"Safe to bunk {rep['safe_bunks_after_planned_leave']} more lecture(s)"
        elif rep["status"] == "ON_THE_EDGE":
            verdict = "0 bunks left — you must attend every remaining lecture"
        else:
            verdict = (
                f"Attendance shortage! Even if you attend all {rep['remaining_Scheduled_classes']} "
                f"remaining classes, max reachable is {rep['max_achievable_percentage']}%"
            )
        lines.append(
            f"- {rep['subject_name']}: Currently {rep['current_percentage']}% "
            f"({rep['current_attended']}/{rep['current_conducted']}). "
            f"Remaining classes: {rep['remaining_Scheduled_classes']}. "
            f"Must attend: {rep['additional_classes_must_attend']}. Verdict: {verdict}."
        )

    summary = "\n".join(lines)
    return {
        "messages": [AIMessage(content=summary)],
        "bunk_reports": reports,
        "final_answer": summary,
    }
