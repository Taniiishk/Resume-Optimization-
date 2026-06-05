from __future__ import annotations

import io
import re
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
)

from app.models.schemas import Resume

DARK = colors.HexColor("#1e293b")
MEDIUM = colors.HexColor("#475569")
ACCENT = colors.HexColor("#2563eb")

LEFT_MARGIN = 0.75 * inch
RIGHT_MARGIN = 0.75 * inch
TOP_MARGIN = 0.5 * inch
BOTTOM_MARGIN = 0.5 * inch


def _name_style():
    return ParagraphStyle("Name", fontName="Helvetica-Bold", fontSize=20, leading=24, alignment=TA_CENTER, spaceAfter=1, textColor=DARK)


def _contact_style():
    return ParagraphStyle("Contact", fontName="Helvetica", fontSize=9, leading=13, alignment=TA_CENTER, textColor=MEDIUM, spaceAfter=4)


def _section_title_style():
    return ParagraphStyle("SectionTitle", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=DARK, spaceBefore=12, spaceAfter=2)


def _item_main_style():
    return ParagraphStyle("ItemMain", fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=DARK, spaceAfter=1)


def _item_sub_style():
    return ParagraphStyle("ItemSub", fontName="Helvetica-Oblique", fontSize=9, leading=12, textColor=MEDIUM, spaceAfter=2)


def _summary_style():
    return ParagraphStyle("Summary", fontName="Helvetica", fontSize=10, leading=14, alignment=TA_JUSTIFY, textColor=DARK, spaceAfter=4)


def _bullet_style():
    return ParagraphStyle("Bullet", fontName="Helvetica", fontSize=9.5, leading=13, leftIndent=20, firstLineIndent=0, spaceAfter=2, textColor=DARK)


def _skills_style():
    return ParagraphStyle("Skills", fontName="Helvetica", fontSize=9.5, leading=14, textColor=DARK, spaceAfter=4)


def _scrub(text: str) -> str:
    """Replace non-WinAnsi chars (which Helvetica can't render) with ASCII."""
    if not text:
        return ""
    # Common problematic Unicode → ASCII map
    m = {
        0x2013: "-", 0x2014: "-", 0x2015: "-",
        0x2018: "'", 0x2019: "'", 0x201A: "'", 0x201B: "'",
        0x201C: '"', 0x201D: '"', 0x201E: '"', 0x201F: '"',
        0x2022: "-", 0x2026: "...",
        0x00A0: " ", 0x202F: " ",
        0x00B7: "-", 0x2219: "-",
        0x2028: " ", 0x2029: " ",
        0x25CF: "o", 0x25CB: "o", 0x2713: "v",
    }
    out = []
    for c in text:
        cp = ord(c)
        if cp < 128:
            out.append(c)
        elif cp in m:
            out.append(m[cp])
        elif 0x00C0 <= cp <= 0x00FF:
            out.append(c)
        elif cp == 0x00A0:
            out.append(" ")
        elif cp == 0x00B7:
            out.append("-")
        else:
            out.append("-")
    return "".join(out)


def _esc(text: str) -> str:
    if not text:
        return ""
    return _scrub(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _section_header(text: str) -> list[Any]:
    return [
        Paragraph(f"<b>{_esc(text)}</b>", _section_title_style()),
        HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=4),
    ]


def _contact_line(resume: Resume) -> str:
    parts: list[str] = []
    c = resume.contact
    if c.location:
        parts.append(_esc(c.location))
    if c.phone:
        parts.append(_esc(c.phone))
    if c.email:
        parts.append(_esc(c.email))
    if c.linkedin:
        parts.append(_esc(c.linkedin))
    if c.github:
        parts.append(_esc(c.github))
    if c.portfolio:
        parts.append(_esc(c.portfolio))
    return " | ".join(parts)


def _format_date(start: str, end: str) -> str:
    s = start.strip() or ""
    e = end.strip() or ""
    if s and e:
        return f"{s} - {e}"
    return s or e


def _build_story(resume: Resume) -> list[Any]:
    story: list[Any] = []

    story.append(Paragraph(_esc(resume.contact.name or "Resume"), _name_style()))
    cl = _contact_line(resume)
    if cl:
        story.append(Paragraph(cl, _contact_style()))
    story.append(Spacer(1, 6))

    section_item_style = ParagraphStyle("SI", fontName="Helvetica", fontSize=10, leading=14)
    inline_right_style = ParagraphStyle("IR", fontName="Helvetica-Oblique", fontSize=9.5, leading=13, textColor=MEDIUM)

    def heading_line(left_bold: str, right_text: str = ""):
        if right_text:
            return Paragraph(f"<b>{left_bold}</b>&nbsp;&nbsp;&nbsp;<font color=\"#475569\"><i>{_esc(right_text)}</i></font>", section_item_style)
        return Paragraph(f"<b>{left_bold}</b>", _item_main_style())

    def sub_line(text: str):
        if text:
            story.append(Paragraph(f"<i>{_esc(text)}</i>", _item_sub_style()))

    def add_bullets(bullets: list[str]):
        for b in bullets:
            if b.strip():
                story.append(Paragraph(f"- {_esc(b.strip())}", _bullet_style()))

    # Summary
    if resume.summary and resume.summary.strip():
        story.extend(_section_header("Professional Summary"))
        story.append(Paragraph(_esc(resume.summary.strip()), _summary_style()))

    # Skills
    if resume.skills:
        story.extend(_section_header("Skills"))
        story.append(Paragraph((" \u2022 ".join(_esc(s) for s in resume.skills if s)), _skills_style()))

    # Experience
    if resume.experience:
        story.extend(_section_header("Experience"))
        for job in resume.experience:
            if not job.title and not job.company:
                continue
            parts = [_esc(p) for p in [job.title, job.company] if p]
            left = " - ".join(parts)
            date_str = _format_date(job.start_date, job.end_date)
            story.append(heading_line(left, date_str))
            sub_line(job.location)
            if job.bullets:
                add_bullets(job.bullets)
            story.append(Spacer(1, 3))

    # Projects
    if resume.projects:
        story.extend(_section_header("Projects"))
        for pj in resume.projects:
            if not pj.name:
                continue
            pj_parts = [_esc(pj.name)]
            if pj.link:
                pj_parts.append(f"<i>{_esc(pj.link)}</i>")
                story.append(Paragraph(" - ".join(pj_parts), _item_main_style()))
            else:
                story.append(Paragraph(pj_parts[0], _item_main_style()))
            if pj.tech:
                sub_line(f"Technologies: {_esc(', '.join(pj.tech))}")
            if pj.bullets:
                add_bullets(pj.bullets)

    # Education
    if resume.education:
        story.extend(_section_header("Education"))
        for edu in resume.education:
            if not edu.degree and not edu.school:
                continue
            parts = [_esc(p) for p in [edu.degree, edu.school] if p]
            left = " - ".join(parts)
            date_str = _format_date(edu.start_date, edu.end_date)
            story.append(heading_line(left, date_str))
            details = []
            if edu.location:
                details.append(_esc(edu.location))
            if edu.gpa:
                details.append(f"GPA: {_esc(edu.gpa)}")
            sub_line(" | ".join(details))
            if edu.details:
                add_bullets(edu.details)

    # Certifications
    if resume.certifications:
        story.extend(_section_header("Certifications"))
        for cert in resume.certifications:
            if cert.name:
                parts = [_esc(cert.name)]
                if cert.issuer:
                    parts.append(f"<i>{_esc(cert.issuer)}</i>")
                if cert.date:
                    parts.append(f"(<i>{_esc(cert.date)}</i>)")
                story.append(Paragraph(" - ".join(parts), ParagraphStyle("CertBullet", fontName="Helvetica", fontSize=9.5, leading=13, leftIndent=20, spaceAfter=2, textColor=DARK)))

    return story


def render_resume_pdf(resume: Resume) -> bytes:
    buf = io.BytesIO()
    frame = Frame(
        LEFT_MARGIN, BOTTOM_MARGIN,
        letter[0] - LEFT_MARGIN - RIGHT_MARGIN,
        letter[1] - TOP_MARGIN - BOTTOM_MARGIN,
        id="body", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    doc = BaseDocTemplate(
        buf, pagesize=letter,
        leftMargin=LEFT_MARGIN, rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN, bottomMargin=BOTTOM_MARGIN,
        title=(resume.contact.name or "Resume") + " - ATS Optimized",
        author=resume.contact.name or "",
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])
    doc.build(_build_story(resume))
    return buf.getvalue()


def safe_filename(name: str) -> str:
    name = (name or "resume").strip()
    name = re.sub(r"[^A-Za-z0-9_-]+", "_", name)
    return (name or "resume") + "_ATS.pdf"
