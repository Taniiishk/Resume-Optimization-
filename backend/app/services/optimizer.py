from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.core.llm import generate_json
from app.models.schemas import JDAnalysis, OptimizeResponse, Resume
from app.services.ats_scorer import score_resume, ACTION_VERBS

logger = logging.getLogger(__name__)

_VERBS_STR = ", ".join(sorted(ACTION_VERBS))

_SYSTEM = f"""You are an elite resume strategist and ATS (Applicant Tracking System) \
optimization specialist. You rewrite resumes to maximize the ATS score against a \
specific job description while remaining 100% truthful to the candidate's \
actual background. You NEVER invent employers, degrees, technologies, metrics, \
or numbers the candidate has not actually used. You write concise, \
action-verb-led bullets using verbs from this approved list: {_VERBS_STR}. \
You always return strict JSON."""


_PROMPT = """You are optimizing a resume for an ATS (Applicant Tracking System). Follow every instruction below precisely.

INPUTS

JOB DESCRIPTION (analysis):
{analysis_json}

ORIGINAL RESUME (JSON):
{resume_json}

SCORING COMPONENTS (maximize each):
1. Keyword match (35%) — every keyword from the JD must appear naturally in the summary, skills, or bullets.
2. Skills coverage (30%) — every required_skill must appear in the skills list; add skills ONLY if the resume supports them.
3. Section completeness (10%) — ALL sections must be present: contact+summary, skills, experience, education, AND projects OR certifications.
4. Title alignment (10%) — the JD role_title must appear verbatim somewhere in the resume (e.g. in the summary).
5. Action verbs (10%) — EVERY bullet MUST start with a strong action verb from the approved list.
6. Format health (5%) — summary must be 80+ characters, email must include @, phone must have digits.

EXECUTION RULES
- Rewrite SUMMARY (2-4 sentences, 80-150 chars) mirroring the JD's value proposition; weave in 6-10 high-priority keywords naturally.
- Reorder SKILLS so JD-required skills come first. You may add skills ONLY if the original resume supports them.
- For each EXPERIENCE role, rewrite ALL bullets to start with an approved action verb and naturally include 1-2 missing keywords. NEVER fabricate metrics, dates, or numbers.
- For each PROJECT, align tech tags and the first bullet with the JD.
- Preserve contact info, dates, employers, education exactly.
- Ensure the output JSON has ALL sections (contact, summary, skills, experience, education, projects, certifications) even if some are empty.
- CRITICAL: Do NOT add numbers or metrics that were not in the original resume. Do NOT change dates, job titles, or company names.

OUTPUT (strict JSON, no commentary, no fences):
{{
  "optimized_resume": {{
    "contact": {{
      "name": "", "email": "", "phone": "", "location": "",
      "linkedin": "", "github": "", "portfolio": ""
    }},
    "summary": "",
    "skills": [],
    "experience": [
      {{
        "title": "", "company": "", "location": "",
        "start_date": "", "end_date": "",
        "bullets": []
      }}
    ],
    "education": [
      {{
        "degree": "", "school": "", "location": "",
        "start_date": "", "end_date": "", "gpa": "",
        "details": []
      }}
    ],
    "projects": [
      {{
        "name": "", "link": "", "tech": [],
        "bullets": []
      }}
    ],
    "certifications": [
      {{
        "name": "", "issuer": "", "date": ""
      }}
    ]
  }},
  "changes_summary": [
    "Short user-facing bullet describing what changed (3-7 items)."
  ]
}}
"""


def _safe_dump(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def _first_word(s: str) -> str:
    return re.sub(r"^[\s\-\u2022\*]+", "", s).strip().split()[0].lower() if s.strip() else ""


def _has_action_verb(bullet: str) -> bool:
    word = re.sub(r"[^a-z]", "", _first_word(bullet))
    return word in ACTION_VERBS


def _fix_bullet_verb(bullet: str, fallback: str = "Built") -> str:
    """Prepend a default action verb if the bullet doesn't start with one."""
    if _has_action_verb(bullet):
        return bullet
    cleaned = re.sub(r"^[\s\-\u2022\*]+", "", bullet).strip()
    first = re.sub(r"[^a-z]", "", cleaned.split()[0].lower()) if cleaned.split() else ""
    if first in ("the", "a", "an", "for", "with", "to", "by", "in", "on", "at", "and", "our", "this", "that"):
        return f"{fallback} {cleaned[0].lower() + cleaned[1:] if cleaned else cleaned}"
    return f"{fallback} {cleaned[0].lower() + cleaned[1:] if cleaned else cleaned}"


def optimize_resume(
    resume: Resume, jd_text: str,
    extra_skills: list[str] | None = None,
    extra_keywords: list[str] | None = None,
) -> tuple[Resume, JDAnalysis, list[str]]:
    extra_skills = extra_skills or []
    extra_keywords = extra_keywords or []

    from app.services.jd_analyzer import analyze_jd
    jd = analyze_jd(jd_text)

    if extra_skills:
        jd.required_skills = list(dict.fromkeys([*extra_skills, *jd.required_skills]))
    if extra_keywords:
        jd.keywords = list(dict.fromkeys([*extra_keywords, *jd.keywords]))

    resume_for_prompt = resume.model_dump()
    resume_for_prompt.pop("raw_text", None)

    prompt = _PROMPT.format(
        analysis_json=_safe_dump({
            "role_title": jd.role_title,
            "required_skills": jd.required_skills,
            "preferred_skills": jd.preferred_skills,
            "keywords": jd.keywords,
            "responsibilities": jd.responsibilities,
        }),
        resume_json=_safe_dump(resume_for_prompt),
    )

    raw = generate_json(prompt, system=_SYSTEM, temperature=0.45)

    opt_data = raw.get("optimized_resume", raw)
    changes = raw.get("changes_summary") or []

    opt_data.setdefault("contact", {})
    for k, v in resume.contact.model_dump().items():
        opt_data["contact"].setdefault(k, v)

    opt_data["raw_text"] = resume.raw_text

    optimized = Resume.model_validate(opt_data)

    # Force-inject extra skills
    seen: set[str] = set()
    deduped_skills: list[str] = []
    for s in [*extra_skills, *optimized.skills]:
        key = s.strip().lower()
        if key and key not in seen:
            seen.add(key)
            deduped_skills.append(s)
    optimized.skills = deduped_skills

    # Post-process: fix bullets without action verbs
    for job in optimized.experience:
        if job.bullets:
            fixed = []
            for b in job.bullets:
                b = b.strip()
                if b:
                    fixed.append(_fix_bullet_verb(b))
            job.bullets = fixed

    return optimized, jd, changes


def _ensure_format_health(opt: Resume) -> None:
    """Post-process to guarantee format score points."""
    # Summary >= 80 chars
    if len((opt.summary or "").strip()) < 80 and opt.summary:
        opt.summary = opt.summary + " Dedicated to delivering high-quality results through collaboration and continuous improvement."

    # Ensure skills list is populated
    if not opt.skills and hasattr(opt, "skills"):
        opt.skills = []

    # Ensure projects/certifications section exists for section completeness
    if not opt.projects and not opt.certifications:
        pass  # cannot fabricate


def run_full_optimization(
    resume: Resume, jd_text: str,
    extra_skills: list[str] | None = None,
    extra_keywords: list[str] | None = None,
) -> OptimizeResponse:
    optimized, jd, changes = optimize_resume(resume, jd_text, extra_skills, extra_keywords)
    _ensure_format_health(optimized)

    before = score_resume(resume, jd)
    after = score_resume(optimized, jd)

    if not changes:
        changes = _auto_changes(resume, optimized, before, after)
    return OptimizeResponse(
        optimized_resume=optimized,
        before_score=before,
        after_score=after,
        changes_summary=changes,
    )


def _auto_changes(orig: Resume, opt: Resume, before, after) -> list[str]:
    out: list[str] = []
    if (opt.summary or "").strip() and opt.summary != orig.summary:
        out.append("Rewrote the professional summary to mirror the JD's value proposition.")
    if [s.lower() for s in opt.skills] != [s.lower() for s in orig.skills]:
        added = [s for s in opt.skills if s.lower() not in {x.lower() for x in orig.skills}]
        if added:
            out.append(f"Added/aligned skills: {', '.join(added[:8])}.")
        out.append("Reordered skills to lead with JD-required ones.")
    if before.missing_keywords and not after.missing_keywords:
        out.append(f"Covered all {len(before.missing_keywords)} previously missing keywords.")
    elif before.missing_keywords and after.missing_keywords:
        covered = len(before.missing_keywords) - len(after.missing_keywords)
        if covered > 0:
            out.append(f"Covered {covered} previously missing keywords.")
    if before.breakdown.action_verbs < after.breakdown.action_verbs:
        out.append("Reformatted bullets to start with strong action verbs.")
    if not out:
        out.append("Polished wording and aligned phrasing with the JD.")
    return out
