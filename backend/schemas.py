from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from models import JobStatus


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    location: Optional[str] = None
    headline: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    github_url: Optional[str] = None
    resume_url: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    location: Optional[str] = None
    headline: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    github_url: Optional[str] = None
    resume_url: Optional[str] = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    profile_summary: Optional[str] = None
    profile_updated_at: Optional[datetime] = None


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    location: Optional[str] = None
    headline: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    github_url: Optional[str] = None
    resume_url: Optional[str] = None
    resume_text: Optional[str] = None


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    profile_summary: str
    profile_updated_at: datetime


class RankingRuleBase(BaseModel):
    user_id: int
    name: str = Field(min_length=1, max_length=255)
    attribute: str = Field(min_length=1, max_length=64)
    condition: str = Field(min_length=1, max_length=16)
    match_value: str = Field(min_length=0, max_length=255)
    weight: float = Field(ge=0, le=100)
    is_active: bool = True


class RankingRuleCreate(RankingRuleBase):
    pass


class RankingRuleUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    attribute: Optional[str] = Field(default=None, min_length=1, max_length=64)
    condition: Optional[str] = Field(default=None, min_length=1, max_length=16)
    match_value: Optional[str] = Field(default=None, min_length=0, max_length=255)
    weight: Optional[float] = Field(default=None, ge=0, le=100)
    is_active: Optional[bool] = None


class RankingRuleRead(RankingRuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class RSSSourceBase(BaseModel):
    user_id: int
    name: Optional[str] = None
    url: str = Field(min_length=1)
    is_active: bool = True


class RSSSourceCreate(RSSSourceBase):
    pass


class RSSSourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    is_active: Optional[bool] = None
    last_fetched_at: Optional[datetime] = None


class RSSSourceRead(RSSSourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    last_fetched_at: Optional[datetime]


class JobBase(BaseModel):
    user_id: int
    rss_source_id: Optional[int] = None
    ranking_rule_id: Optional[int] = None

    title: str = Field(min_length=1, max_length=255)
    company: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None

    status: JobStatus = JobStatus.saved
    rank_score: float = 0.0
    applied_at: Optional[datetime] = None


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    rss_source_id: Optional[int] = None
    ranking_rule_id: Optional[int] = None

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    company: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None

    status: Optional[JobStatus] = None
    rank_score: Optional[float] = None
    applied_at: Optional[datetime] = None


class JobRead(JobBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date_added: datetime
    updated_at: datetime

