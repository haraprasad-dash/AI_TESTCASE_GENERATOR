# SOP 09: Export Service

## Goal
Export generated test plans and test cases to multiple formats.

## Layer
Layer 3: Tools (`backend/app/services/export_service.py`)

## Supported Formats

| Format | Extension | Library | Use Case |
|--------|-----------|---------|----------|
| Markdown | .md | Native | Version control, editing |
| PDF | .pdf | markdown-pdf / weasyprint | Sharing, documentation |
| Excel | .xlsx | pandas/openpyxl | Test management tools |
| JSON | .json | Native | Integration with other tools |
| Gherkin | .feature | Native | BDD framework import |

## Implementation

### Export Service (`services/export_service.py`)

```python
"""
Export Service - Convert generated content to various formats.
"""
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import tempfile

import pandas as pd
from markdown import markdown


@dataclass
class ExportResult:
    """Result of export operation."""
    file_path: str
    format: str
    size_bytes: int


class ExportService:
    """Service for exporting test artifacts."""
    
    def __init__(self, output_dir: str = "./outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def export(
        self,
        test_plan: Optional[str],
        test_cases: Optional[str],
        format: str,
        filename_prefix: str = "testgen"
    ) -> ExportResult:
        """
        Export test artifacts to specified format.
        
        Args:
            test_plan: Test plan markdown content
            test_cases: Test cases markdown content
            format: Export format (markdown, pdf, excel, json, gherkin)
            filename_prefix: Prefix for output filename
            
        Returns:
            ExportResult with file path and metadata
        """
        if format == "markdown":
            return await self._export_markdown(test_plan, test_cases, filename_prefix)
        elif format == "pdf":
            return await self._export_pdf(test_plan, test_cases, filename_prefix)
        elif format == "excel":
            return await self._export_excel(test_cases, filename_prefix)
        elif format == "json":
            return await self._export_json(test_plan, test_cases, filename_prefix)
        elif format == "gherkin":
            return await self._export_gherkin(test_cases, filename_prefix)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def _export_markdown(
        self,
        test_plan: Optional[str],
        test_cases: Optional[str],
        filename_prefix: str
    ) -> ExportResult:
        """Export as combined Markdown file."""
        parts = []
        
        if test_plan:
            parts.append(test_plan)
            parts.append("\n\n---\n\n")
        
        if test_cases:
            parts.append(test_cases)
        
        content = "\n".join(parts)
        
        file_path = self.output_dir / f"{filename_prefix}.md"
        file_path.write_text(content, encoding='utf-8')
        
        return ExportResult(
            file_path=str(file_path),
            format="markdown",
            size_bytes=file_path.stat().st_size
        )
    
    async def _export_pdf(
        self,
        test_plan: Optional[str],
        test_cases: Optional[str],
        filename_prefix: str
    ) -> ExportResult:
        """Export as PDF file."""
        try:
            import markdown_pdf
        except ImportError:
            raise ExportError("markdown-pdf not installed. Run: pip install markdown-pdf")
        
        parts = []
        if test_plan:
            parts.append(test_plan)
        if test_cases:
            parts.append(test_cases)
        
        content = "\n\n---\n\n".join(parts)
        
        file_path = self.output_dir / f"{filename_prefix}.pdf"
        
        # Convert markdown to PDF
        pdf = markdown_pdf.MarkdownPdf()
        pdf.add_section(markdown_pdf.Section(content))
        pdf.save(str(file_path))
        
        return ExportResult(
            file_path=str(file_path),
            format="pdf",
            size_bytes=file_path.stat().st_size
        )
    
    async def _export_excel(
        self,
        test_cases: Optional[str],
        filename_prefix: str
    ) -> ExportResult:
        """Export test cases as Excel file."""
        if not test_cases:
            raise ExportError("No test cases to export")
        
        # Parse test cases from markdown tables
        parsed_cases = self._parse_test_cases(test_cases)
        
        if not parsed_cases:
            raise ExportError("Could not parse test cases")
        
        file_path = self.output_dir / f"{filename_prefix}.xlsx"
        
        # Create DataFrame
        df = pd.DataFrame(parsed_cases)
        
        # Export to Excel with formatting
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Test Cases', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Test Cases']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        return ExportResult(
            file_path=str(file_path),
            format="excel",
            size_bytes=file_path.stat().st_size
        )
    
    async def _export_json(
        self,
        test_plan: Optional[str],
        test_cases: Optional[str],
        filename_prefix: str
    ) -> ExportResult:
        """Export as structured JSON."""
        data = {
            "test_plan": test_plan,
            "test_cases": self._parse_test_cases(test_cases) if test_cases else [],
            "metadata": {
                "format_version": "1.0",
                "export_date": str(pd.Timestamp.now())
            }
        }
        
        file_path = self.output_dir / f"{filename_prefix}.json"
        file_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        
        return ExportResult(
            file_path=str(file_path),
            format="json",
            size_bytes=file_path.stat().st_size
        )
    
    async def _export_gherkin(
        self,
        test_cases: Optional[str],
        filename_prefix: str
    ) -> ExportResult:
        """Export test cases as Gherkin .feature file."""
        if not test_cases:
            raise ExportError("No test cases to export")
        
        gherkin_content = self._convert_to_gherkin(test_cases)
        
        file_path = self.output_dir / f"{filename_prefix}.feature"
        file_path.write_text(gherkin_content, encoding='utf-8')
        
        return ExportResult(
            file_path=str(file_path),
            format="gherkin",
            size_bytes=file_path.stat().st_size
        )
    
    def _parse_test_cases(self, markdown_content: str) -> List[Dict[str, str]]:
        """Parse test cases from markdown table."""
        cases = []
        
        # Find markdown tables
        table_pattern = r'\|([^\n]+)\|\n\|[-:\|\s]+\|\n((?:\|[^\n]+\|\n?)+)'
        matches = re.findall(table_pattern, markdown_content)
        
        for header_line, rows in matches:
            headers = [h.strip() for h in header_line.split('|') if h.strip()]
            
            for row in rows.strip().split('\n'):
                cells = [c.strip() for c in row.split('|') if c.strip()]
                if len(cells) >= len(headers):
                    case = dict(zip(headers, cells))
                    cases.append(case)
        
        return cases
    
    def _convert_to_gherkin(self, test_cases: str) -> str:
        """Convert test cases to Gherkin format."""
        lines = [
            "Feature: Generated Test Cases",
            "",
            "  Generated from TestGen AI Agent",
            ""
        ]
        
        # Parse and convert each test case
        parsed = self._parse_test_cases(test_cases)
        
        for i, case in enumerate(parsed, 1):
            description = case.get('Description', f'Test Case {i}')
            steps = case.get('Steps', '')
            expected = case.get('Expected Result', '')
            
            lines.append(f"  Scenario: {description}")
            
            # Add Given-When-Then from steps
            if steps:
                step_lines = steps.split('\n')
                for j, step in enumerate(step_lines):
                    step = step.strip()
                    if step:
                        # Convert numbered steps to Given/When/Then
                        if j == 0:
                            prefix = "Given"
                        elif "when" in step.lower():
                            prefix = "When"
                        elif "then" in step.lower():
                            prefix = "Then"
                        else:
                            prefix = "And"
                        
                        # Remove numbering
                        step_text = re.sub(r'^\d+[\.\)]\s*', '', step)
                        lines.append(f"    {prefix} {step_text}")
            
            # Add expected result as Then
            if expected:
                lines.append(f"    Then {expected}")
            
            lines.append("")
        
        return "\n".join(lines)


class ExportError(Exception):
    """Export operation failed."""
    pass
```

### API Router (`routers/export.py`)

```python
"""
Export endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import Optional

from app.services.export_service import ExportService, ExportError
from app.models import ExportRequest

router = APIRouter(prefix="/api/export", tags=["export"])


def get_export_service():
    """Get export service instance."""
    return ExportService()


@router.post("/{request_id}")
async def export_generation(
    request_id: str,
    export_request: ExportRequest,
    service: ExportService = Depends(get_export_service)
):
    """Export generation results to specified format."""
    try:
        result = await service.export(
            test_plan=export_request.test_plan,
            test_cases=export_request.test_cases,
            format=export_request.format,
            filename_prefix=f"testgen_{request_id[:8]}"
        )
        
        return {
            "file_path": result.file_path,
            "format": result.format,
            "size_bytes": result.size_bytes,
            "download_url": f"/api/export/download/{result.file_path.split('/')[-1]}"
        }
        
    except ExportError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(500, f"Export failed: {str(e)}")


@router.get("/download/{filename}")
async def download_file(filename: str):
    """Download exported file."""
    file_path = Path("./outputs") / filename
    
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
```

## Excel Export Columns

| Column | Description |
|--------|-------------|
| TC_ID | Test Case ID |
| Title | Test case title |
| Description | Detailed description |
| Preconditions | Required setup |
| Test Steps | Step-by-step instructions |
| Expected Result | Expected outcome |
| Priority | High/Medium/Low |
| Test Type | Functional/Regression/etc |
| Related Requirement | Traceability link |

## Edge Cases
1. **No test cases**: Return error for Excel/Gherkin export
2. **Parse failures**: Return empty results with warning
3. **Large files**: Stream large exports to avoid memory issues
4. **File name collisions**: Add timestamp to filename
5. **Missing dependencies**: Graceful error if pandas/openpyxl not installed
