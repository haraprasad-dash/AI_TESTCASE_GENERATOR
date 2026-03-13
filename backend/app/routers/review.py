"""
Review endpoints for test case and user guide analysis.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.models import ReviewConfiguration, ReviewInputs, ReviewRequest
from app.services.export_service import ExportService
from app.services.review_service import ReviewService, ReviewValidationError

router = APIRouter(prefix="/api/review", tags=["review"])

_review_service = ReviewService()


def _build_request(payload: Dict[str, Any]) -> ReviewRequest:
    return ReviewRequest(
        request_id=payload.get("request_id"),
        timestamp=datetime.utcnow(),
        inputs=ReviewInputs(**payload.get("inputs", {})),
        configuration=ReviewConfiguration(**payload.get("configuration", {})),
    )


@router.post("/test-cases")
async def review_test_cases(payload: Dict[str, Any]):
    """Review uploaded test cases against requirement context."""
    try:
        request = _build_request(payload)
        return _review_service.review("test-cases", request.inputs)
    except ReviewValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review failed: {e}")


@router.post("/user-guide")
async def review_user_guide(payload: Dict[str, Any]):
    """Review user guide accuracy and completeness."""
    try:
        request = _build_request(payload)
        return _review_service.review("user-guide", request.inputs)
    except ReviewValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review failed: {e}")


@router.post("/both")
async def review_both(payload: Dict[str, Any]):
    """Run test case and user guide reviews in one request."""
    try:
        request = _build_request(payload)
        return _review_service.review("both", request.inputs)
    except ReviewValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review failed: {e}")


@router.get("/{review_id}/status")
async def review_status(review_id: str):
    """Return latest stored review status and partial results."""
    state = _review_service.get_status(review_id)
    if not state:
        raise HTTPException(status_code=404, detail="Review ID not found")
    return state


@router.post("/clarification/{review_id}/attach")
async def review_clarification_attach(review_id: str, file: UploadFile = File(...)):
    """Accept clarification attachments and acknowledge linkage to review session."""
    state = _review_service.get_status(review_id)
    if not state:
        raise HTTPException(status_code=404, detail="Review ID not found")

    uploads = Path("./uploads")
    uploads.mkdir(parents=True, exist_ok=True)
    target = uploads / f"{review_id}_{Path(file.filename).name}"

    content = await file.read()
    target.write_bytes(content)

    return {
        "review_id": review_id,
        "filename": file.filename,
        "stored_path": str(target),
        "message": "Attachment stored and will be considered in follow-up clarifications",
    }


@router.post("/{review_id}/export")
async def export_review(review_id: str, payload: Dict[str, Any]):
    """Export review report using existing export service formats."""
    state = _review_service.get_status(review_id)
    if not state:
        raise HTTPException(status_code=404, detail="Review ID not found")

    format_type = payload.get("format", "markdown")
    report_markdown = state.get("report_markdown")

    service = ExportService()
    result = await service.export(
        test_plan=report_markdown,
        test_cases=report_markdown,
        format=format_type,
        filename_prefix=f"review_{review_id[:8]}",
    )

    return {
        "file_path": result.file_path,
        "format": result.format,
        "size_bytes": result.size_bytes,
        "download_url": f"/api/export/download/{Path(result.file_path).name}",
    }
