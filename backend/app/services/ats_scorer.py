"""ATS scoring: deterministic, transparent, weighted 100-point scale.

Components:
  - Keyword match       35%
  - Skills coverage     30%
  - Section completeness 10%
  - Title alignment     10%
  - Action verbs        10%
  - Format health        5%
"""

from __future__ import annotations

import re
from typing import Iterable

from app.models.schemas import ATSScore, ATSScoreBreakdown, JDAnalysis, Resume


ACTION_VERBS = {
    "achieved", "analyzed", "architected", "authored", "automated", "built",
    "collaborated", "created", "cut", "delivered", "deployed", "designed",
    "developed", "directed", "drove", "engineered", "enhanced", "established",
    "executed", "expanded", "generated", "implemented", "improved", "increased",
    "initiated", "integrated", "launched", "led", "managed", "mentored",
    "migrated", "modeled", "modernized", "monitored", "optimized", "orchestrated",
    "organized", "performed", "pioneered", "planned", "produced", "programmed",
    "prototyped", "published", "reduced", "refactored", "released", "researched",
    "resolved", "restructured", "reviewed", "scaled", "shipped", "spearheaded",
    "streamlined", "supported", "tested", "trained", "transformed", "tuned",
    "validated", "wrote",
}

W_KEYWORD = 35
W_SKILLS = 30
W_SECTIONS = 10
W_TITLE = 10
W_VERBS = 10
W_FORMAT = 5


def _flatten_text(resume: Resume) -> str:
    parts: list[str] = [resume.summary or ""]
    parts.extend(resume.skills or [])
    for job in resume.experience or []:
        parts.append(job.title or "")
        parts.append(job.company or "")
        parts.extend(job.bullets or [])
    for proj in resume.projects or []:
        parts.append(proj.name or "")
        parts.extend(proj.tech or [])
        parts.extend(proj.bullets or [])
    for edu in resume.education or []:
        parts.append(edu.degree or "")
        parts.append(edu.school or "")
        parts.extend(edu.details or [])
    return "\n".join(parts).lower()


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _contains_token(haystack: str, needle: str) -> bool:
    """Whole-token (or whole-phrase) containment, case-insensitive."""
    n = _norm(needle)
    if not n:
        return False
    # word boundary for short tokens, substring for multi-word phrases
    if " " in n or any(ch in n for ch in "+#./-"):
        return n in haystack
    pattern = r"(?<![a-z0-9])" + re.escape(n) + r"(?![a-z0-9])"
    return re.search(pattern, haystack) is not None


def _classify(total: float) -> str:
    if total >= 85:
        return "Excellent"
    if total >= 70:
        return "Good"
    if total >= 50:
        return "Medium"
    return "Low"


def _keyword_score(resume_text: str, keywords: Iterable[str]) -> tuple[float, list[str], list[str]]:
    keywords = [k for k in keywords if k]
    if not keywords:
        return 0.0, [], []
    matched, missing = [], []
    for kw in keywords:
        if _contains_token(resume_text, kw):
            matched.append(kw)
        else:
            missing.append(kw)
    pct = (len(matched) / len(keywords)) * 100
    return pct, matched, missing


def _skills_score(resume_text: str, jd: JDAnalysis) -> tuple[float, list[str], list[str]]:
    required = jd.required_skills or []
    if not required:
        return 0.0, [], []
    matched, missing = [], []
    for s in required:
        if _contains_token(resume_text, s):
            matched.append(s)
        else:
            missing.append(s)
    pct = (len(matched) / len(required)) * 100
    return pct, matched, missing


def _section_score(resume: Resume) -> float:
    have = 0
    total = 5
    if (resume.contact.name or resume.contact.email) and (resume.summary or "").strip():
        have += 1
    if resume.skills:
        have += 1
    if resume.experience:
        have += 1
    if resume.education:
        have += 1
    if resume.projects or resume.certifications:
        have += 1
    return (have / total) * 100


def _title_score(resume: Resume, jd: JDAnalysis) -> float:
    if not jd.role_title:
        return 0.0
    role = _norm(jd.role_title)
    if not role:
        return 0.0
    text = _flatten_text(resume)
    if _contains_token(text, role):
        return 100.0
    # partial: any role-word appears
    words = [w for w in role.split() if len(w) > 3]
    if not words:
        return 0.0
    hits = sum(1 for w in words if _contains_token(text, w))
    return (hits / len(words)) * 100


def _action_verbs_score(resume: Resume) -> float:
    bullets: list[str] = []
    for job in resume.experience or []:
        bullets.extend(job.bullets or [])
    for proj in resume.projects or []:
        bullets.extend(proj.bullets or [])
    bullets = [b for b in bullets if b and b.strip()]
    if not bullets:
        return 0.0
    starts = 0
    for b in bullets:
        first = re.sub(r"^[\s\-\u2022\*]+", "", b).strip().lower().split()
        if not first:
            continue
        verb = re.sub(r"[^a-z]", "", first[0])
        if verb in ACTION_VERBS:
            starts += 1
    return (starts / len(bullets)) * 100


def _format_score(resume: Resume) -> float:
    """Heuristics: contact info present, summary present, no obvious issues."""
    score = 0.0
    c = resume.contact
    if c.email and "@" in c.email:
        score += 30
    if c.phone and re.search(r"\d", c.phone):
        score += 20
    if (c.name or "").strip():
        score += 20
    if (resume.summary or "").strip() and len(resume.summary) >= 80:
        score += 15
    if resume.skills:
        score += 15
    return min(score, 100.0)


def _recommendations(jd: JDAnalysis, missing_kw: list[str], missing_skills: list[str],
                     section_pct: float, title_pct: float, verb_pct: float) -> list[str]:
    recs: list[str] = []
    if missing_skills:
        recs.append(
            "Add these required skills (if applicable) to your Skills section: "
            + ", ".join(missing_skills[:8])
        )
    if missing_kw:
        recs.append(
            "Naturally weave these keywords into your summary and bullets: "
            + ", ".join(missing_kw[:8])
        )
    if section_pct < 80:
        recs.append("Add missing standard sections (Projects / Certifications) for completeness.")
    if title_pct < 50 and jd.role_title:
        recs.append(f"Mirror the role title '{jd.role_title}' somewhere in your resume.")
    if verb_pct < 60:
        recs.append("Start more bullet points with strong action verbs (Built, Designed, Optimized, ...).")
    if not recs:
        recs.append("Looks great — keep iterating on quantified metrics in your bullets.")
    return recs


def score_resume(resume: Resume, jd: JDAnalysis) -> ATSScore:
    text = _flatten_text(resume)

    kw_pct, matched_kw, missing_kw = _keyword_score(text, jd.keywords)
    sk_pct, matched_sk, missing_sk = _skills_score(text, jd)
    sec_pct = _section_score(resume)
    title_pct = _title_score(resume, jd)
    verb_pct = _action_verbs_score(resume)
    fmt_pct = _format_score(resume)

    total = (
        kw_pct * W_KEYWORD
        + sk_pct * W_SKILLS
        + sec_pct * W_SECTIONS
        + title_pct * W_TITLE
        + verb_pct * W_VERBS
        + fmt_pct * W_FORMAT
    ) / 100.0
    total = round(min(total, 100.0), 1)

    return ATSScore(
        total=total,
        breakdown=ATSScoreBreakdown(
            keyword_match=round(kw_pct, 1),
            skills_coverage=round(sk_pct, 1),
            section_completeness=round(sec_pct, 1),
            title_alignment=round(title_pct, 1),
            action_verbs=round(verb_pct, 1),
            format_health=round(fmt_pct, 1),
        ),
        matched_keywords=matched_kw,
        missing_keywords=missing_kw,
        matched_skills=matched_sk,
        missing_skills=missing_sk,
        recommendations=_recommendations(jd, missing_kw, missing_sk, sec_pct, title_pct, verb_pct),
        level=_classify(total),
    )
