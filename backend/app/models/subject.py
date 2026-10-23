from typing import Optional
from sqlmodel import Field, SQLModel

class SubjectBase(SQLModel):
    student_id: int = Field(foreign_key="student_profiles.id", index=True)
    name: str = Field(index=True, max_length=120)
    code: Optional[str] = Field(default=None, max_length=30)
    classes_attended: int = Field(default=0, ge=0)
    classes_conducted: int = Field(default=0, ge=0)
    target_pct: float = Field(default=75.0, ge=1.0, le=100.0)

class Subject(SubjectBase, table=True):
    __tablename__ = "subjects"
    id: Optional[int] = Field(default=None, primary_key=True)

class SubjectCreate(SubjectBase):
    pass

class AttendanceMarkRequest(SQLModel):
    status: str = Field(description="'present' or 'absent'")
    classes_count: int = Field(default=1, ge=1, le=10)
