from contextlib import asynccontextmanager
from datetime import date
import holidays
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db import create_db_and_tables
from app.routers import agent_chat, attendance, calendar

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(
    title=settings.app_name,
    description="Agentic AI Attendance Tracker & Smart Bunk Planner API",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(attendance.router)
app.include_router(calendar.router)
app.include_router(agent_chat.router)

@app.get("/health", tags=["System"])
async def health_check(state_code: str = settings.default_state_code):
    current_year = date.today().year
    in_holidays = holidays.country_holidays("IN", subdiv=state_code, years=current_year)
    upcoming = {str(k): v for k, v in sorted(in_holidays.items()) if k >= date.today()}
    return {
        "status": "healthy",
        "database": "connected",
        "state_code": state_code,
        "upcoming_holidays_count": len(upcoming),
        "next_3_holidays": dict(list(upcoming.items())[:3]),
    }
