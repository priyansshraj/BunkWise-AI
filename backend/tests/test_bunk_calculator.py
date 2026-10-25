from datetime import date
from app.models.holiday import CustomHoliday
from app.models.subject import Subject
from app.models.timetable import TimetableSlot
from app.services.bunk_calculator import calculate_subject_bunk_plan

def test_safe_bunk_calculation_with_holidays():
    subject = Subject(
        id=1,
        student_id=1,
        name="Artificial Intelligence",
        classes_attended=15,
        classes_conducted=20,
        target_pct=75.0,
    )
    # 1 lecture every Monday (0) and Wednesday (2)
    slots = [
        TimetableSlot(id=1, subject_id=1, day_of_week=0, classes_count=1),
        TimetableSlot(id=2, subject_id=1, day_of_week=2, classes_count=1),
    ]
    # Custom holiday on Monday, Nov 16, 2026 (Chhath Puja break)
    custom_holidays = [
        CustomHoliday(
            id=1,
            student_id=1,
            holiday_date=date(2026, 11, 16),
            title="Chhath Puja",
            is_working_override=False,
        )
    ]

    report = calculate_subject_bunk_plan(
        subject=subject,
        slots=slots,
        start_date=date(2026, 11, 1),
        exam_date=date(2026, 11, 30),
        state_code="BR",
        is_saturday_working=True,
        custom_holidays=custom_holidays,
    )

    # In Nov 2026: Mondays are Nov 2, 9, 16, 23, 30 (5 Mondays, minus Nov 16 Chhath = 4)
    # Wednesdays are Nov 4, 11, 18, 25 (4 Wednesdays) -> Total 8 remaining classes
    assert report["remaining_Scheduled_classes"] == 8
    assert report["projected_total_classes"] == 28
    # 75% of 28 = 21 total needed -> 21 - 15 attended = 6 must attend -> 8 - 6 = 2 safe bunks!
    assert report["additional_classes_must_attend"] == 6
    assert report["safe_bunks_available"] == 2
    assert report["status"] == "SAFE_TO_BUNK"

def test_shortage_warning_when_target_unreachable():
    subject = Subject(
        id=2,
        student_id=1,
        name="Compiler Design",
        classes_attended=5,
        classes_conducted=20,
        target_pct=75.0,
    )
    slots = [TimetableSlot(id=2, subject_id=2, day_of_week=0, classes_count=1)]

    report = calculate_subject_bunk_plan(
        subject=subject,
        slots=slots,
        start_date=date(2026, 11, 1),
        exam_date=date(2026, 11, 15),
        state_code="BR",
    )

    assert report["safe_bunks_available"] < 0
    assert report["status"] == "SHORTAGE_WARNING"
