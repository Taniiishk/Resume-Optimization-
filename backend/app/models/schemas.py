from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ---------- Resume (structured) ----------

class ContactInfo(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""


class ExperienceItem(BaseModel):
    title: str = ""
    company: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    bullets: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    degree: str = ""
    school: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    gpa: str = ""
    details: list[str] = Field(default_factory=list)


class ProjectItem(BaseModel):
    name: str = ""
    link: str = ""
    tech: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)


class CertificationItem(BaseModel):
    name: str = ""
    issuer: str = ""
    date: str = ""


class Resume(BaseModel):
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    certifications: list[CertificationItem] = Field(default_factory=list)
    raw_text: str = ""


# ---------- Job Description analysis ----------

class JDAnalysis(BaseModel):
    role_title: str = ""
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    raw_text: str = ""


# ---------- ATS scoring ----------

class ATSScoreBreakdown(BaseModel):
    keyword_match: float = 0.0
    skills_coverage: float = 0.0
    section_completeness: float = 0.0
    title_alignment: float = 0.0
    action_verbs: float = 0.0
    format_health: float = 0.0


class ATSScore(BaseModel):
    total: float = 0.0
    breakdown: ATSScoreBreakdown = Field(default_factory=ATSScoreBreakdown)
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    level: Literal["Low", "Medium", "Good", "Excellent"] = "Low"


# ---------- Optimize request/response ----------

class OptimizeRequest(BaseModel):
    resume: Resume
    jd_text: str
    extra_skills: list[str] = Field(default_factory=list)
    extra_keywords: list[str] = Field(default_factory=list)


class OptimizeResponse(BaseModel):
    optimized_resume: Resume
    before_score: ATSScore
    after_score: ATSScore
    changes_summary: list[str] = Field(default_factory=list)
