from datetime import date
from typing import Optional
from sqlmodel import Field, SQLModel

class CustomHolidayBase(SQLModel):
    student_id: int = Field(foreign_key="student_profiles.id", index=True)
    holiday_date: date = Field(index=True)
    title: str = Field(max_length=120, description="e.g., Chhath Puja Break, College Fest")
    is_working_override: bool = Field(
        default=False,
        description="False = Holiday/No class; True = Extra working day on a Sunday/Holiday",
    )

class CustomHoliday(CustomHolidayBase, table=True):
    __tablename__ = "custom_holidays"
    id: Optional[int] = Field(default=None, primary_key=True)

class CustomHolidayCreate(CustomHolidayBase):
    pass
