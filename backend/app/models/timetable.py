from typing import Optional
from sqlmodel import Field, SQLModel

class TimetableSlotBase(SQLModel):
    subject_id: int = Field(foreign_key="subjects.id", index=True)
    day_of_week: int = Field(ge=0, le=6, description="0=Monday through 6=Sunday")
    classes_count: int = Field(default=1, ge=1, le=8)

class TimetableSlot(TimetableSlotBase, table=True):
    __tablename__ = "timetable_slots"
    id: Optional[int] = Field(default=None, primary_key=True)

class TimetableSlotCreate(TimetableSlotBase):
    pass
