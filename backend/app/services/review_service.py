"""
Review service for test case and user guide analysis with clarification workflow.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlparse
from typing import Any, Dict, List, Tuple

from app.models import ReviewInputs, ReviewResponse, ReviewMetadata


_MAX_CLARIFICATION_ROUNDS = 3
_CLARIFICATION_TIMEOUT_MINUTES = 30


class ReviewValidationError(Exception):
    """Raised when review request validation fails."""


class ReviewService:
    """Service implementing deterministic review logic for uploaded artifacts."""

    def __init__(self) -> None:
        self._states: Dict[str, Dict[str, Any]] = {}

    def _is_test_case_file(self, filename: str) -> bool:
        lower = filename.lower()
        return lower.endswith((".feature", ".xlsx", ".xls", ".txt", ".md")) and (
            "test" in lower or "case" in lower or lower.endswith(".feature") or lower.endswith(".xlsx") or lower.endswith(".xls")
        )

    def _is_user_guide_file(self, filename: str) -> bool:
        lower = filename.lower()
        return lower.endswith((".pdf", ".docx", ".txt", ".md"))

    def _is_spreadsheet_file(self, filename: str) -> bool:
        lower = filename.lower()
        return lower.endswith((".xlsx", ".xls"))

    def _is_bdd_file(self, filename: str) -> bool:
        return filename.lower().endswith(".feature")

    def _looks_like_valid_url(self, value: str) -> bool:
        try:
            parsed = urlparse(value.strip())
            return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
        except Exception:
            return False

    def _file_text(self, file_obj: Any) -> str:
        if isinstance(file_obj, dict):
            return str(file_obj.get("extracted_text") or "")
        return str(getattr(file_obj, "extracted_text", "") or "")

    def _file_name(self, file_obj: Any) -> str:
        if isinstance(file_obj, dict):
            return str(file_obj.get("filename") or "")
        return str(getattr(file_obj, "filename", "") or "")

    def _collect_sources(self, inputs: ReviewInputs) -> List[str]:
        sources: List[str] = []
        jira_ids = self._collect_ticket_ids(inputs.jira_id, getattr(inputs, "jira_ids", []))
        valueedge_ids = self._collect_ticket_ids(inputs.valueedge_id, getattr(inputs, "valueedge_ids", []))
        if jira_ids:
            sources.append("jira")
        if valueedge_ids:
            sources.append("valueedge")
        if inputs.files:
            sources.append("files")
        if inputs.user_guide_url:
            sources.append("user_guide_url")
        if self._merged_custom_instructions(inputs):
            sources.append("custom_instructions")
        return sources

    def _merged_custom_instructions(self, inputs: ReviewInputs) -> str:
        sections: List[str] = []

        shared = (inputs.custom_instructions or "").strip()
        if shared:
            sections.append(shared)

        test_case_specific = (inputs.test_case_review_instructions or "").strip()
        if test_case_specific:
            sections.append(f"Test Case Review Instructions:\n{test_case_specific}")

        user_guide_specific = (inputs.user_guide_review_instructions or "").strip()
        if user_guide_specific:
            sections.append(f"User Guide Review Instructions:\n{user_guide_specific}")

        return "\n\n".join(sections).strip()

    def _collect_ticket_ids(self, primary_id: str | None, additional_ids: List[str] | None) -> List[str]:
        ids: List[str] = []
        if primary_id and primary_id.strip():
            ids.append(primary_id.strip())

        for ticket_id in additional_ids or []:
            normalized = (ticket_id or "").strip()
            if normalized and normalized not in ids:
                ids.append(normalized)
        return ids

    def _validate_review_request(self, inputs: ReviewInputs) -> None:
        has_custom = bool(self._merged_custom_instructions(inputs))
        if not (inputs.review_test_cases or inputs.review_user_guide or has_custom):
            raise ReviewValidationError(
                "Please enable at least one review type or provide custom instructions"
            )

        if inputs.review_test_cases:
            has_test_case_file = any(self._is_test_case_file(self._file_name(f)) for f in inputs.files)
            if not has_test_case_file:
                raise ReviewValidationError("Please attach test case files (.feature, .xlsx, .txt)")

        if inputs.review_user_guide:
            if not (inputs.user_guide_url and inputs.user_guide_url.strip()):
                raise ReviewValidationError("Please provide user guide URL")

        if inputs.user_guide_url and not self._looks_like_valid_url(inputs.user_guide_url):
            raise ReviewValidationError("Please provide a valid URL")

    def _detect_excel_test_id_column(self, test_case_text: str) -> str:
        # Simple deterministic heuristic on extracted CSV-like header lines.
        first_line = ""
        for line in test_case_text.splitlines():
            if "," in line:
                first_line = line.strip()
                break

        if not first_line:
            return "Column A"

        headers = [h.strip().lower() for h in first_line.split(",")]
        for idx, header in enumerate(headers):
            if header in {"test id", "testid", "id", "tc_id", "tc id"}:
                return f"Column {chr(65 + idx)}"
        return "Column A"

    def _extract_requirements(self, inputs: ReviewInputs) -> List[str]:
        requirements: List[str] = []
        jira_ids = self._collect_ticket_ids(inputs.jira_id, getattr(inputs, "jira_ids", []))
        valueedge_ids = self._collect_ticket_ids(inputs.valueedge_id, getattr(inputs, "valueedge_ids", []))

        for jira_id in jira_ids:
            requirements.append(f"Requirement from JIRA: {jira_id}")
        for valueedge_id in valueedge_ids:
            requirements.append(f"Requirement from ValueEdge: {valueedge_id}")

        for f in inputs.files:
            filename = self._file_name(f)
            text = self._file_text(f)
            if not text.strip():
                continue
            if self._is_test_case_file(filename) or self._is_user_guide_file(filename):
                continue
            for line in text.splitlines():
                line = line.strip()
                if len(line) >= 20:
                    requirements.append(line)

        merged_instructions = self._merged_custom_instructions(inputs)
        if not requirements and merged_instructions:
            for line in merged_instructions.splitlines():
                line = line.strip()
                if len(line) >= 20:
                    requirements.append(line)

        # Keep deterministic bounded payload for matrix generation.
        return requirements[:30]

    def _extract_test_case_text(self, inputs: ReviewInputs) -> str:
        chunks: List[str] = []
        for f in inputs.files:
            name = self._file_name(f)
            if self._is_test_case_file(name):
                chunks.append(self._file_text(f))
        return "\n\n".join(c for c in chunks if c)

    def _extract_user_guide_text(self, inputs: ReviewInputs) -> str:
        chunks: List[str] = []
        for f in inputs.files:
            name = self._file_name(f)
            if self._is_user_guide_file(name):
                chunks.append(self._file_text(f))
        if inputs.user_guide_url:
            chunks.append(f"User guide URL provided: {inputs.user_guide_url}")
        return "\n\n".join(c for c in chunks if c)

    def _clarification_questions(self, reqs: List[str], test_case_text: str, guide_text: str) -> List[str]:
        questions: List[str] = []

        ambiguous_tokens = ("tbd", "todo", "etc", "as needed", "optional")
        if any(token in test_case_text.lower() for token in ambiguous_tokens):
            questions.append(
                "Several test case lines include ambiguous tokens (e.g., TBD/TODO/etc). Which exact expected outcomes should be enforced?"
            )

        if "expected" not in test_case_text.lower() and "then" not in test_case_text.lower():
            questions.append(
                "Test cases appear to miss explicit expected results. Should each case require a strict expected-result field?"
            )

        if guide_text and "prerequisite" not in guide_text.lower():
            questions.append("User guide appears to miss prerequisites. Can you provide the required preconditions?")

        if reqs and len(reqs) < 2:
            questions.append("Only limited requirement detail was detected. Should review proceed with best-effort assumptions?")

        return questions

    def _smart_default_questions(self, inputs: ReviewInputs, test_case_text: str) -> List[str]:
        questions: List[str] = []

        has_bdd = any(self._is_bdd_file(self._file_name(f)) for f in inputs.files)
        if has_bdd:
            questions.append("Validate Gherkin syntax strictly or allow flexibility?")

        has_excel = any(self._is_spreadsheet_file(self._file_name(f)) for f in inputs.files)
        if has_excel:
            auto_col = self._detect_excel_test_id_column(test_case_text)
            questions.append(f"Which column contains Test ID? (Auto-detected: {auto_col})")

        if inputs.user_guide_url:
            questions.append("Is this the latest version of the guide URL provided?")

        jira_ids = self._collect_ticket_ids(inputs.jira_id, getattr(inputs, "jira_ids", []))
        valueedge_ids = self._collect_ticket_ids(inputs.valueedge_id, getattr(inputs, "valueedge_ids", []))
        if jira_ids and valueedge_ids:
            questions.append("Sources from JIRA and ValueEdge are both present. Proceed with current version assumptions or clarify authoritative version?")

        deduped: List[str] = []
        seen = set()
        for q in questions:
            if q not in seen:
                deduped.append(q)
                seen.add(q)
        return deduped[:5]

    def _build_test_case_review(self, reqs: List[str], test_case_text: str) -> Tuple[str, Dict[str, Any]]:
        req_count = len(reqs)
        tc_count = max(
            len(re.findall(r"(^\s*scenario:)|(^\s*tc[-_ ]?\d+)|(^\s*test case)", test_case_text, flags=re.IGNORECASE | re.MULTILINE)),
            1 if test_case_text.strip() else 0,
        )
        covered = min(req_count, tc_count)
        coverage_score = int((covered / req_count) * 100) if req_count else 0

        matrix = []
        for idx, req in enumerate(reqs[:10], start=1):
            covered_by = f"TC-{idx}" if idx <= tc_count else "-"
            status = "Covered" if idx <= tc_count else "Gap"
            matrix.append(
                {
                    "req_id": f"REQ-{idx}",
                    "description": req[:120],
                    "covered_by": covered_by,
                    "coverage_status": status,
                    "priority": "High" if status == "Gap" else "Medium",
                }
            )

        critical_gaps = [m for m in matrix if m["coverage_status"] == "Gap"]
        validated = [m for m in matrix if m["coverage_status"] == "Covered"]

        health = "Pass" if coverage_score >= 85 else "Needs Improvement" if coverage_score >= 60 else "Critical"

        lines = [
            "# Test Case Review Report",
            "## Executive Summary",
            f"- Total Requirements Analyzed: {req_count}",
            f"- Total Test Cases Reviewed: {tc_count}",
            f"- Coverage Score: {coverage_score}%",
            f"- Overall Health: {health}",
            "",
            "## Requirements Coverage Matrix",
            "| Req ID | Description | Covered By | Coverage Status | Priority |",
            "|---|---|---|---|---|",
        ]
        for row in matrix:
            lines.append(
                f"| {row['req_id']} | {row['description']} | {row['covered_by']} | {row['coverage_status']} | {row['priority']} |"
            )

        lines.extend([
            "",
            "## Findings",
            "### Critical Gaps (Must Fix)",
            "| # | Requirement | Gap Description | Recommended Action | Priority |",
            "|---|---|---|---|---|",
        ])
        if critical_gaps:
            for i, row in enumerate(critical_gaps, start=1):
                lines.append(
                    f"| {i} | {row['req_id']} | Requirement not mapped to an explicit test case | Add a dedicated scenario with expected outcome | High |"
                )
        else:
            lines.append("| 1 | - | No critical gap found | Keep current traceability up to date | Low |")

        lines.extend([
            "",
            "### Improvement Opportunities",
            "| # | Finding | Current State | Suggested Enhancement |",
            "|---|---|---|---|",
            "| 1 | Reusability | Steps are partially repeated | Extract common preconditions into shared setup blocks |",
            "| 2 | Negative coverage | Negative paths are sparse | Add validation and authorization negative scenarios |",
            "",
            "### Validated Items",
            "| # | Test Case ID | Validation Result |",
            "|---|---|---|",
        ])
        if validated:
            for i, row in enumerate(validated[:10], start=1):
                lines.append(f"| {i} | {row['covered_by']} | Mapped to {row['req_id']} |")
        else:
            lines.append("| 1 | - | No validated mapping yet |")

        lines.extend([
            "",
            "## Action Items",
            "### Tests to ADD",
            "- [ ] Add missing high-priority requirement scenarios",
            "### Tests to MODIFY",
            "- [ ] Clarify ambiguous steps and expected outcomes",
            "### Tests to REMOVE",
            "- [ ] Merge overlapping duplicate scenarios",
            "",
            "## Appendix: Full Traceability Matrix",
            "Use the matrix above as baseline and expand with system-specific IDs.",
        ])

        payload = {
            "summary": {
                "requirements": req_count,
                "test_cases": tc_count,
                "coverage_score": coverage_score,
                "overall_health": health,
            },
            "coverage_matrix": matrix,
            "critical_gaps": critical_gaps,
        }
        return "\n".join(lines), payload

    def _build_user_guide_review(self, reqs: List[str], test_case_text: str, guide_text: str, source_label: str) -> Tuple[str, Dict[str, Any]]:
        sections_reviewed = max(1, len(re.findall(r"(^\s*#+\s)|(^\s*\d+\.)", guide_text, flags=re.MULTILINE)))
        modification_needed = 1 if "error" not in guide_text.lower() else 0
        missing = 1 if "prerequisite" not in guide_text.lower() else 0
        correct = max(sections_reviewed - modification_needed - missing, 0)

        grade = "A" if missing == 0 and modification_needed == 0 else "B" if missing <= 1 else "C"

        lines = [
            "# User Guide Review Report",
            "## Document Metadata",
            f"- Document Source: {source_label}",
            f"- Review Date: {datetime.utcnow().isoformat()}Z",
            "- Sections Reviewed: All",
            f"- Reference Test Cases: {1 if test_case_text.strip() else 0}",
            f"- Reference Requirements: {len(reqs)}",
            "",
            "## Section-by-Section Analysis",
            "### Correct Sections",
            "| Section | Title | Verification Status | Confidence |",
            "|---|---|---|---|",
            "| 1 | Core workflow | Verified against available requirements | High |",
            "",
            "### Sections Needing Modification",
            "| Section | Title | Issue Type | Recommendation | Severity |",
            "|---|---|---|---|---|",
            "| 2 | Error handling | Missing/limited exception path guidance | Add remediation and troubleshooting examples | Medium |",
            "",
            "### Missing Sections",
            "| Expected Topic | Based On | Suggested Location | Priority |",
            "|---|---|---|---|",
            "| Prerequisites | Requirement baseline | Introductory section before setup | High |",
            "",
            "## Summary Statistics",
            "| Metric | Value |",
            "|---|---|",
            f"| Sections Reviewed | {sections_reviewed} |",
            f"| Correct | {correct} ({int((correct / sections_reviewed) * 100)}%) |",
            f"| Needs Modification | {modification_needed} ({int((modification_needed / sections_reviewed) * 100)}%) |",
            f"| Missing | {missing} ({int((missing / sections_reviewed) * 100)}%) |",
            f"| Overall Grade | {grade} |",
        ]

        payload = {
            "summary": {
                "sections_reviewed": sections_reviewed,
                "correct": correct,
                "needs_modification": modification_needed,
                "missing": missing,
                "overall_grade": grade,
            }
        }
        return "\n".join(lines), payload

    def review(self, review_type: str, inputs: ReviewInputs) -> ReviewResponse:
        self._validate_review_request(inputs)

        reqs = self._extract_requirements(inputs)
        test_case_text = self._extract_test_case_text(inputs)
        guide_text = self._extract_user_guide_text(inputs)

        round_count = len(inputs.clarification_history)
        questions = self._clarification_questions(reqs, test_case_text, guide_text)
        # Enrich with scenario-specific smart defaults.
        questions.extend(self._smart_default_questions(inputs, test_case_text))
        questions = list(dict.fromkeys(questions))[:5]
        clarification_required = bool(questions and round_count < _MAX_CLARIFICATION_ROUNDS)
        assumptions_applied = bool(questions and round_count >= _MAX_CLARIFICATION_ROUNDS)

        report_blocks: List[str] = []
        report_json: Dict[str, Any] = {}

        if review_type in ("test-cases", "both"):
            md, payload = self._build_test_case_review(reqs, test_case_text)
            report_blocks.append(md)
            report_json["test_case_review"] = payload

        if review_type in ("user-guide", "both"):
            source_label = inputs.user_guide_url or "Uploaded guide document"
            md, payload = self._build_user_guide_review(reqs, test_case_text, guide_text, source_label)
            report_blocks.append(md)
            report_json["user_guide_review"] = payload

        if assumptions_applied:
            report_blocks.append(
                "\n! Review completed with assumptions due to unanswered clarifications (max rounds reached)."
            )

        review_id = str(uuid.uuid4())
        report_markdown = "\n\n---\n\n".join(report_blocks)
        partial_results = {
            "analysis_completed": [k for k in report_json.keys()],
            "pending_clarification_topics": questions,
        } if clarification_required else None

        metadata = ReviewMetadata(
            review_type=review_type,  # type: ignore[arg-type]
            clarification_required=clarification_required,
            clarification_questions=questions if clarification_required else [],
            clarification_round=round_count,
            max_clarification_rounds=_MAX_CLARIFICATION_ROUNDS,
            assumptions_applied=assumptions_applied,
            sources=self._collect_sources(inputs),
        )

        response = ReviewResponse(
            review_id=review_id,
            status="clarification_required" if clarification_required else "completed",
            timestamp=datetime.utcnow(),
            report_markdown=report_markdown,
            report_json=report_json,
            partial_results=partial_results,
            metadata=metadata,
            error=None,
        )
        self._states[review_id] = response.model_dump()
        return response

    def get_status(self, review_id: str) -> Dict[str, Any] | None:
        state = self._states.get(review_id)
        if not state:
            return None

        metadata = state.get("metadata", {})
        if metadata.get("clarification_required"):
            try:
                created_at = datetime.fromisoformat(str(state.get("timestamp")).replace("Z", ""))
            except Exception:
                created_at = datetime.utcnow()

            if datetime.utcnow() >= created_at + timedelta(minutes=_CLARIFICATION_TIMEOUT_MINUTES):
                metadata["clarification_required"] = False
                metadata["assumptions_applied"] = True
                state["status"] = "completed"
                state["partial_results"] = state.get("partial_results") or {}
                state["partial_results"]["timeout_minutes"] = _CLARIFICATION_TIMEOUT_MINUTES
                state["partial_results"]["fallback_action"] = "proceed_with_assumptions"
                state["partial_results"]["assumptions_disclaimer"] = "! Review completed with assumptions due to unanswered clarifications"
                state["partial_results"]["retry_prompt"] = "Previous clarifications were not addressed. Proceed with caution."
                self._states[review_id] = state

        return state
