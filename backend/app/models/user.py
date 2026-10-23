from datetime import date
from typing import Optional
from sqlmodel import Field, SQLModel

class StudentProfileBase(SQLModel):
    name: str = Field(index=True, max_length=100)
    state_code: str = Field(default="BR", max_length=5, description="Indian state code for holidays")
    default_target_pct: float = Field(default=75.0, ge=1.0, le=100.0)
    is_saturday_working: bool = Field(default=True)
    expected_exam_date: Optional[date] = Field(default=None)

class StudentProfile(StudentProfileBase, table=True):
    __tablename__ = "student_profiles"
    id: Optional[int] = Field(default=None, primary_key=True)

class StudentProfileCreate(StudentProfileBase):
    pass

class StudentProfileUpdate(SQLModel):
    name: Optional[str] = None
    state_code: Optional[str] = None
    default_target_pct: Optional[float] = Field(default=None, ge=1.0, le=100.0)
    is_saturday_working: Optional[bool] = None
    expected_exam_date: Optional[date] = None
