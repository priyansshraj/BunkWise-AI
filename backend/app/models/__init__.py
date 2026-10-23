from app.models.user import StudentProfile, StudentProfileCreate, StudentProfileUpdate
from app.models.subject import Subject, SubjectCreate, AttendanceMarkRequest
from app.models.timetable import TimetableSlot, TimetableSlotCreate
from app.models.holiday import CustomHoliday, CustomHolidayCreate

__all__ = [
    "StudentProfile",
    "StudentProfileCreate",
    "StudentProfileUpdate",
    "Subject",
    "SubjectCreate",
    "AttendanceMarkRequest",
    "TimetableSlot",
    "TimetableSlotCreate",
    "CustomHoliday",
    "CustomHolidayCreate",
]
