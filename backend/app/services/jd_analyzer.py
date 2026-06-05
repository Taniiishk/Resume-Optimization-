"""Job-description analyzer: extract role, required skills, keywords, etc."""

from __future__ import annotations

import logging
import re

from app.core.llm import generate_json
from app.models.schemas import JDAnalysis

logger = logging.getLogger(__name__)


_JD_PROMPT = """You are a precise job-description analyzer. Extract the following from the job description and return ONLY valid JSON.

Rules:
- Lowercase all skills/keywords internally but keep them in their canonical form
  (e.g., "Python", "TensorFlow", "scikit-learn", "SQL", "Natural Language Processing").
- `required_skills` = must-have skills explicitly or implicitly required.
- `preferred_skills` = nice-to-have / good-to-have.
- `keywords` = high-signal phrases and nouns that an ATS would scan for
  (e.g., "machine learning", "data preprocessing", "model evaluation",
   "deep learning", "computer vision", "predictive analytics").
  Include 15-30 keywords. Avoid generic words like "team", "good", "work".
- `responsibilities` = 3-7 short imperative phrases summarizing the role.
- `role_title` = the job title as written.
- Output strict JSON. No commentary, no fences.

JSON schema:
{{
  "role_title": "",
  "required_skills": [],
  "preferred_skills": [],
  "keywords": [],
  "responsibilities": []
}}

Job description:
\"\"\"
{jd_text}
\"\"\"
"""


def _normalize_skill(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def analyze_jd(jd_text: str) -> JDAnalysis:
    if not jd_text or not jd_text.strip():
        raise ValueError("Job description text is empty")

    prompt = _JD_PROMPT.format(jd_text=jd_text[:10000])
    raw = generate_json(prompt, temperature=0.2)

    analysis = JDAnalysis(
        role_title=_normalize_skill(raw.get("role_title", "")),
        required_skills=[_normalize_skill(s) for s in (raw.get("required_skills") or []) if s],
        preferred_skills=[_normalize_skill(s) for s in (raw.get("preferred_skills") or []) if s],
        keywords=[_normalize_skill(k) for k in (raw.get("keywords") or []) if k],
        responsibilities=[_normalize_skill(r) for r in (raw.get("responsibilities") or []) if r],
        raw_text=jd_text,
    )

    # De-duplicate while preserving order
    def _dedupe(items: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for x in items:
            key = x.lower()
            if key not in seen:
                seen.add(key)
                out.append(x)
        return out

    analysis.required_skills = _dedupe(analysis.required_skills)
    analysis.preferred_skills = _dedupe(analysis.preferred_skills)
    analysis.keywords = _dedupe(analysis.keywords)
    analysis.responsibilities = _dedupe(analysis.responsibilities)

    return analysis
