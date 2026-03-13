"""
Document upload and processing endpoints.
"""
import os
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
ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/plain",
    "text/markdown",
    "image/png",
    "image/jpeg",
    "image/jpg"
}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and process a document file.
    
    Returns:
        File metadata with extracted text
    """
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            400,
            "Unsupported file type. Allowed: PDF, DOCX, XLSX, TXT, FEATURE"
        )
    
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
        extracted = await parser.parse_file(str(file_path), file.content_type)
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "content_type": file.content_type,
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
