"""
Export endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional

from app.services.export_service import ExportService, ExportError

router = APIRouter(prefix="/api/export", tags=["export"])


def get_export_service():
    """Get export service instance."""
    return ExportService()


@router.post("/{request_id}")
async def export_generation(
    request_id: str,
    export_request: dict,
    service: ExportService = Depends(get_export_service)
):
    """Export generation results to specified format."""
    try:
        format_type = export_request.get("format", "markdown")
        test_plan = export_request.get("test_plan")
        test_cases = export_request.get("test_cases")
        
        result = await service.export(
            test_plan=test_plan,
            test_cases=test_cases,
            format=format_type,
            filename_prefix=f"testgen_{request_id[:8]}"
        )
        
        return {
            "file_path": result.file_path,
            "format": result.format,
            "size_bytes": result.size_bytes,
            "download_url": f"/api/export/download/{Path(result.file_path).name}"
        }
        
    except ExportError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(500, f"Export failed: {str(e)}")


@router.get("/download/{filename}")
async def download_file(filename: str):
    """Download exported file."""
    # Sanitize: strip any path components to prevent directory traversal
    safe_filename = Path(filename).name
    file_path = Path("./outputs") / safe_filename
    
    if not file_path.exists():
        raise HTTPException(404, "File not found")
    
    media_types = {
        ".md": "text/markdown",
        ".pdf": "application/pdf",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".json": "application/json",
        ".feature": "text/plain"
    }
    
    media_type = media_types.get(file_path.suffix, "application/octet-stream")
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )
