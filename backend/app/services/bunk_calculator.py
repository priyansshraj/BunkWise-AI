import math
from datetime import date, timedelta
from typing import Dict, Iterable, List, Optional, Set
import holidays
from app.models.holiday import CustomHoliday
from app.models.subject import Subject
from app.models.timetable import TimetableSlot
from app.services.holiday_service import build_custom_holiday_map, is_college_working_day

def calculate_subject_bunk_plan(
    subject: Subject,
    slots: Iterable[TimetableSlot],
    exam_date: date,
    state_code: str = "BR",
    is_saturday_working: bool = True,
    custom_holidays: Iterable[CustomHoliday] = (),
    planned_absent_dates: Optional[Set[date]] = None,
    start_date: Optional[date] = None,
) -> Dict:
    """
    Calculates exact remaining lectures, required attendance, and safe bunks
    for a single subject between start_date (defaults to tomorrow) and exam_date.
    """
    planned_absent = planned_absent_dates or set()
    current_day = start_date or (date.today() + timedelta(days=1))

    # Map weekday (0=Mon..6=Sun) -> number of classes for this subject
    weekday_classes: Dict[int, int] = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    for slot in slots:
        if slot.subject_id == subject.id:
            weekday_classes[slot.day_of_week] += slot.classes_count

    years = list({current_day.year, exam_date.year})
    official_holidays = holidays.country_holidays("IN", subdiv=state_code, years=years)
    custom_map = build_custom_holiday_map(custom_holidays)

    remaining_classes = 0
    planned_absent_classes = 0
    upcoming_class_dates: List[str] = []

    # Loop day-by-day from current_day up to exam_date (inclusive)
    cursor = current_day
    while cursor <= exam_date:
        if is_college_working_day(
            cursor, state_code, is_saturday_working, custom_map, official_holidays
        ):
            lectures_today = weekday_classes.get(cursor.weekday(), 0)
            if lectures_today > 0:
                remaining_classes += lectures_today
                upcoming_class_dates.append(str(cursor))
                if cursor in planned_absent:
                    planned_absent_classes += lectures_today
        cursor += timedelta(days=1)

    attended = subject.classes_attended
    conducted = subject.classes_conducted
    target_fraction = subject.target_pct / 100.0

    current_pct = round((attended / conducted) * 100.0, 2) if conducted > 0 else 100.0
    final_total_classes = conducted + remaining_classes

    # math.ceil ensures we never round down below the required target percentage
    min_total_attended_needed = math.ceil(target_fraction * final_total_classes)
    additional_must_attend = max(0, min_total_attended_needed - attended)
    safe_bunks_total = remaining_classes - additional_must_attend
    safe_bunks_after_planned = safe_bunks_total - planned_absent_classes
    max_possible_pct = (
        round(((attended + remaining_classes) / final_total_classes) * 100.0, 2)
        if final_total_classes > 0
        else 100.0
    )

    if safe_bunks_after_planned >= 0:
        status = "SAFE_TO_BUNK" if safe_bunks_after_planned > 0 else "ON_THE_EDGE"
    else:
        status = "SHORTAGE_WARNING"

    return {
        "subject_id": subject.id,
        "subject_name": subject.name,
        "current_attended": attended,
        "current_conducted": conducted,
        "current_percentage": current_pct,
        "target_percentage": subject.target_pct,
        "remaining_Scheduled_classes": remaining_classes,
        "projected_total_classes": final_total_classes,
        "additional_classes_must_attend": additional_must_attend,
        "safe_bunks_available": safe_bunks_total,
        "planned_leave_classes_lost": planned_absent_classes,
        "safe_bunks_after_planned_leave": safe_bunks_after_planned,
        "max_achievable_percentage": max_possible_pct,
        "status": status,
    }
