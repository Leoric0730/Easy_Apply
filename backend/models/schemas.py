from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    Enum, JSON, ForeignKey, LargeBinary, Time
)
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    contact_info = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    resume_profiles = relationship("ResumeProfile", back_populates="user")
    search_configs = relationship("SearchConfig", back_populates="user")


class ResumeProfile(Base):
    __tablename__ = "resume_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    label = Column(String(50), nullable=False)
    resume_file_path = Column(String(500))
    parsed_content = Column(JSON)
    target_keywords = Column(JSON)
    preferences = Column(JSON)
    embedding = Column(LargeBinary)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="resume_profiles")
    applications = relationship("Application", back_populates="resume_profile")
    preference_signals = relationship("PreferenceSignal", back_populates="resume_profile")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False)
    external_url = Column(String(1000))
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255))
    description = Column(Text)
    salary_range = Column(String(100))
    embedding = Column(LargeBinary)
    match_score = Column(Float)
    status = Column(
        Enum("new", "selected", "rejected", "applied", "expired", name="job_status"),
        default="new"
    )
    scraped_at = Column(DateTime, default=datetime.utcnow)

    applications = relationship("Application", back_populates="job")
    preference_signals = relationship("PreferenceSignal", back_populates="job")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    resume_profile_id = Column(Integer, ForeignKey("resume_profiles.id"), nullable=False)
    filled_data = Column(JSON)
    browser_session_id = Column(String(100))
    status = Column(
        Enum("filling", "ready_to_review", "submitted", name="app_status"),
        default="filling"
    )
    applied_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="applications")
    resume_profile = relationship("ResumeProfile", back_populates="applications")


class PreferenceSignal(Base):
    __tablename__ = "preference_signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_profile_id = Column(Integer, ForeignKey("resume_profiles.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    action = Column(
        Enum("selected", "rejected", "bookmarked", name="signal_action"),
        nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    resume_profile = relationship("ResumeProfile", back_populates="preference_signals")
    job = relationship("Job", back_populates="preference_signals")


class SearchConfig(Base):
    __tablename__ = "search_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_profile_id = Column(Integer, ForeignKey("resume_profiles.id"))
    platforms = Column(JSON)
    filters = Column(JSON)
    auto_search_enabled = Column(Boolean, default=False)
    auto_search_time = Column(Time)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="search_configs")
