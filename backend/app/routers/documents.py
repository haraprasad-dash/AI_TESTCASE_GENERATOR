"""
Document upload and processing endpoints.
"""
import uuid
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from app.services.document_parser import (
    DocumentParser, get_document_parser,
    UnsupportedFileError, ExtractionError
)

router = APIRouter(prefix="/api/documents", tags=["documents"])

UPLOAD_DIR = Path("./uploads")
ALLOWED_UPLOADS = {
    ".pdf": {"application/pdf", "application/octet-stream"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
    },
    ".xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/octet-stream",
    },
    ".xls": {"application/vnd.ms-excel", "application/octet-stream"},
    ".txt": {"text/plain", "application/octet-stream"},
    ".md": {"text/markdown", "text/plain", "application/octet-stream"},
    ".feature": {"text/plain", "text/x-gherkin", "application/octet-stream"},
    ".png": {"image/png", "application/octet-stream"},
    ".jpg": {"image/jpeg", "image/jpg", "application/octet-stream"},
    ".jpeg": {"image/jpeg", "image/jpg", "application/octet-stream"},
}
CANONICAL_CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".feature": "text/x-gherkin",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


def _resolve_content_type(file: UploadFile) -> str:
    suffix = Path(file.filename or "").suffix.lower()
    allowed_types = ALLOWED_UPLOADS.get(suffix)
    if not allowed_types:
        raise HTTPException(
            400,
            "Unsupported file type. Allowed: PDF, DOCX, XLSX, XLS, TXT, MD, FEATURE, PNG, JPG"
        )

    content_type = (file.content_type or "application/octet-stream").lower()
    if content_type not in allowed_types:
        raise HTTPException(
            400,
            "Unsupported file type. Allowed: PDF, DOCX, XLSX, XLS, TXT, MD, FEATURE, PNG, JPG"
        )

    return CANONICAL_CONTENT_TYPES[suffix]


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and process a document file.
    
    Returns:
        File metadata with extracted text
    """
    resolved_content_type = _resolve_content_type(file)
    
    # Generate unique file ID
    file_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix
    safe_filename = f"{file_id}{file_ext}"
    file_path = UPLOAD_DIR / safe_filename
    
    try:
        # Ensure upload directory exists
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Check file size after save
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            file_path.unlink()
            raise HTTPException(400, f"File too large: {file_size / (1024*1024):.1f}MB (max 20MB)")
        
        # Extract text
        parser = get_document_parser()
        extracted = await parser.parse_file(str(file_path), resolved_content_type)
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "content_type": resolved_content_type,
            "size_bytes": file_size,
            "extracted_text": extracted.text,
            "page_count": extracted.page_count
        }
        
    except UnsupportedFileError as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(400, str(e))
        
    except ExtractionError as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(422, str(e))
        
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(500, f"Upload failed: {str(e)}")


@router.post("/upload-multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """Upload and process multiple files."""
    results = []
    errors = []
    
    for file in files:
        try:
            result = await upload_file(file)
            results.append(result)
        except HTTPException as e:
            errors.append({"filename": file.filename, "error": e.detail})
    
    return {
        "successful": results,
        "failed": errors,
        "total": len(files),
        "success_count": len(results),
        "fail_count": len(errors)
    }


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """Delete an uploaded file."""
    # Find file with matching ID prefix
    for file_path in UPLOAD_DIR.iterdir():
        if file_path.name.startswith(file_id):
            file_path.unlink()
            return {"message": "File deleted"}
    
    raise HTTPException(404, "File not found")
