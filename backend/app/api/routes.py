"""API routes for the ATS Resume Optimizer.

All endpoints are mounted under /api.
"""

from __future__ import annotations

import logging
import traceback

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response

from app.models.schemas import OptimizeRequest
from app.services.ats_scorer import score_resume
from app.services.jd_analyzer import analyze_jd
from app.services.optimizer import run_full_optimization, optimize_resume
from app.services.pdf_renderer import render_resume_pdf, safe_filename as pdf_filename
from app.services.docx_renderer import render_resume_docx, safe_filename as docx_filename
from app.services.resume_parser import extract_text, parse_resume_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/parse-resume")
async def parse_resume(file: UploadFile = File(...)) -> dict:
    try:
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Empty file")
        text = extract_text(file.filename or "", file.content_type or "", data)
        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract any text from the file")
        resume = parse_resume_text(text)
        return {
            "filename": file.filename,
            "char_count": len(text),
            "resume": resume.model_dump(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("parse-resume failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {e}")


@router.post("/analyze-jd")
async def analyze_jd_route(payload: dict) -> dict:
    jd_text = (payload or {}).get("jd_text", "").strip()
    if not jd_text:
        raise HTTPException(status_code=400, detail="jd_text is required")
    try:
        analysis = analyze_jd(jd_text)
        return analysis.model_dump()
    except Exception as e:
        logger.exception("analyze-jd failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to analyze JD: {e}")


@router.post("/optimize")
async def optimize(payload: OptimizeRequest) -> dict:
    try:
        result = run_full_optimization(
            payload.resume, payload.jd_text,
            extra_skills=payload.extra_skills,
            extra_keywords=payload.extra_keywords,
        )
        return result.model_dump()
    except Exception as e:
        logger.exception("optimize failed: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Optimization failed: {e}")


@router.post("/optimize-pdf")
async def optimize_pdf(payload: OptimizeRequest) -> Response:
    """End-to-end: parse + analyze + optimize + score + render PDF.

    Returns the optimized PDF as a binary download, and includes score info
    in response headers for the frontend to pick up.
    """
    try:
        result = run_full_optimization(payload.resume, payload.jd_text)
        pdf_bytes = render_resume_pdf(result.optimized_resume)
        filename = pdf_filename(payload.resume.contact.name or "resume")

        import json as _json
        meta_header = _json.dumps({
            "before_score": result.before_score.model_dump(),
            "after_score": result.after_score.model_dump(),
            "changes_summary": result.changes_summary,
        }, ensure_ascii=False)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Optimize-Meta": meta_header,
                "Access-Control-Expose-Headers": "X-Optimize-Meta",
            },
        )
    except Exception as e:
        logger.exception("optimize-pdf failed: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Optimization failed: {e}")


@router.post("/render-pdf")
async def render_pdf(payload: dict) -> Response:
    """Render an arbitrary Resume JSON to PDF."""
    try:
        from app.models.schemas import Resume
        resume = Resume.model_validate(payload.get("resume") or {})
        pdf_bytes = render_resume_pdf(resume)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{pdf_filename(resume.contact.name or "resume")}"',
            },
        )
    except Exception as e:
        logger.exception("render-pdf failed: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Render failed: {e}")


@router.post("/render-docx")
async def render_docx(payload: dict) -> Response:
    """Render an arbitrary Resume JSON to DOCX."""
    try:
        from app.models.schemas import Resume
        resume = Resume.model_validate(payload.get("resume") or {})
        docx_bytes = render_resume_docx(resume)
        name = docx_filename(resume.contact.name or "resume")
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{name}.docx"',
            },
        )
    except Exception as e:
        logger.exception("render-docx failed: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Render failed: {e}")
