from datetime import date
from typing import Dict, Iterable
import holidays
from app.models.holiday import CustomHoliday

def build_custom_holiday_map(custom_holidays: Iterable[CustomHoliday]) -> Dict[date, CustomHoliday]:
    """Converts a list of CustomHoliday rows into a fast O(1) dictionary lookup by date."""
    return {item.holiday_date: item for item in custom_holidays}

def is_college_working_day(
    target_date: date,
    state_code: str,
    is_saturday_working: bool,
    custom_map: Dict[date, CustomHoliday],
    official_holidays: holidays.HolidayBase,
) -> bool:
    """
    Determines if college is open on target_date using a 3-tier priority rule:
    1. Student's CustomHoliday override (highest priority)
    2. Official Indian + State government holiday
    3. Standard weekday/weekend rule (Sunday off, Saturday configurable)
    """
    # Priority 1: Check if the student added a custom override for this exact date
    if target_date in custom_map:
        return custom_map[target_date].is_working_override

    # Priority 2: Check if it is an official Indian / State holiday (e.g., Diwali)
    if target_date in official_holidays:
        return False

    # Priority 3: Check weekday (0=Monday ... 5=Saturday, 6=Sunday)
    weekday = target_date.weekday()
    if weekday == 6:  # Sunday is always a holiday unless overridden in Priority 1
        return False
    if weekday == 5 and not is_saturday_working:
        return False

    return True
