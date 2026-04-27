"""
Assessment export endpoints: CSV and LaTeX bundle.
"""
import io
import re
import zipfile
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from models import Assessment, Card
from services.latex_export import build_csv, build_latex_bundle
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/assessments/{assessment_id}/export", tags=["exports"])


def _safe_filename(name: str) -> str:
    """Make a string safe to use inside a Content-Disposition filename."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name or "assessment").strip("_")
    return cleaned or "assessment"


def _get_assessment_or_404(db: Session, assessment_id: int) -> Assessment:
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment with id {assessment_id} not found",
        )
    return assessment


@router.get("/csv")
async def export_csv(assessment_id: int, db: Session = Depends(get_db)):
    """Export all cards for the assessment as CSV."""
    assessment = _get_assessment_or_404(db, assessment_id)
    cards = (
        db.query(Card)
        .filter(Card.assessment_id == assessment_id)
        .order_by(Card.section_number, Card.created_at)
        .all()
    )
    body = build_csv(cards)
    filename = f"{_safe_filename(assessment.name)}_findings.csv"

    logger.info("Exported CSV", assessment_id=assessment_id, count=len(cards))

    return StreamingResponse(
        io.BytesIO(body.encode("utf-8")),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/latex")
async def export_latex(assessment_id: int, db: Session = Depends(get_db)):
    """Export all findings for the assessment as a LaTeX bundle (ZIP).

    The ZIP contains:
      findings/<id>-<slug>/final.tex   (one file per finding)
      findings-collected-fa.tex        (\\input lines in severity order)
    """
    assessment = _get_assessment_or_404(db, assessment_id)
    cards = (
        db.query(Card)
        .filter(Card.assessment_id == assessment_id)
        .order_by(Card.created_at)
        .all()
    )

    files = build_latex_bundle(cards)

    # Build zip in-memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in files:
            zf.writestr(path, content)
    buf.seek(0)

    filename = f"{_safe_filename(assessment.name)}_findings_latex.zip"
    logger.info(
        "Exported LaTeX bundle",
        assessment_id=assessment_id,
        files=len(files),
    )

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
