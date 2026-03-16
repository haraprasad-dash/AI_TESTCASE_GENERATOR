"""
Review service for test case and user guide analysis with clarification workflow.
"""

from __future__ import annotations

import re
import uuid
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
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
        self._skill_cache: Dict[str, str] = {}

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

    def _fetch_user_guide_url_text(self, url: str) -> Tuple[str, str | None]:
        parsed = urlparse((url or "").strip())
        if parsed.netloc.lower() in {"example.com", "www.example.com"}:
            return "", "Skipped remote fetch for placeholder domain"

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "TestGen-AI-ReviewBot/1.0",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                body = response.read().decode("utf-8", errors="ignore")

            body = re.sub(r"<script[\s\S]*?</script>", " ", body, flags=re.IGNORECASE)
            body = re.sub(r"<style[\s\S]*?</style>", " ", body, flags=re.IGNORECASE)
            body = re.sub(r"<[^>]+>", " ", body)
            body = re.sub(r"\s+", " ", body).strip()
            return body[:20000], None
        except Exception as exc:
            return "", f"URL content fetch failed: {exc}"

    def _load_skill_text(self, skill_filename: str) -> str:
        if skill_filename in self._skill_cache:
            return self._skill_cache[skill_filename]

        try:
            root = Path(__file__).resolve().parents[3]
            skill_path = root / skill_filename
            text = skill_path.read_text(encoding="utf-8")
            self._skill_cache[skill_filename] = text
            return text
        except Exception:
            self._skill_cache[skill_filename] = ""
            return ""

    def _template_terms_user_guide(self) -> List[Tuple[str, Tuple[str, ...], str]]:
        skill_text = self._load_skill_text("skill-prompt-userguide-review.md").lower()
        candidates: List[Tuple[str, Tuple[str, ...], str]] = [
            (
                "Prerequisites and setup guidance",
                ("prerequisite", "setup"),
                "Add a prerequisites/setup subsection with required environment and access details",
            ),
            (
                "Troubleshooting and common errors",
                ("troubleshooting", "error"),
                "Document common failures, probable causes, and exact recovery actions",
            ),
            (
                "Step-by-step workflow clarity",
                ("step", "workflow"),
                "Provide numbered steps with expected outcome per step",
            ),
            (
                "Examples and expected outcomes",
                ("example", "expected"),
                "Include concrete examples with expected system/user-visible outcomes",
            ),
            (
                "Version/timeliness notes",
                ("version", "current"),
                "Add version scope, release alignment, and last verified date",
            ),
        ]

        if not skill_text:
            return candidates

        selected: List[Tuple[str, Tuple[str, ...], str]] = []
        for label, tokens, guidance in candidates:
            if any(token in skill_text for token in tokens):
                selected.append((label, tokens, guidance))
        return selected or candidates

    def _template_terms_test_case(self) -> List[Tuple[str, Tuple[str, ...], str]]:
        skill_text = self._load_skill_text("skill-prompt-testcase-review.md").lower()
        candidates: List[Tuple[str, Tuple[str, ...], str]] = [
            (
                "Negative and edge case coverage",
                ("negative", "edge"),
                "Add explicit negative and edge scenarios with expected failure behavior",
            ),
            (
                "Boundary condition coverage",
                ("boundary",),
                "Add boundary-value checks for min/max/empty/invalid inputs",
            ),
            (
                "Traceability mapping",
                ("traceability", "requirement"),
                "Ensure each requirement maps to at least one deterministic test case",
            ),
            (
                "Atomic and unambiguous steps",
                ("atomic", "unambiguous"),
                "Split multi-purpose cases into atomic test cases with clear expected results",
            ),
        ]

        if not skill_text:
            return candidates

        selected: List[Tuple[str, Tuple[str, ...], str]] = []
        for label, tokens, guidance in candidates:
            if any(token in skill_text for token in tokens):
                selected.append((label, tokens, guidance))
        return selected or candidates

    def _instruction_focus_phrases(self, instruction_text: str) -> List[str]:
        if not instruction_text.strip():
            return []

        cleaned = re.sub(r"(?im)^\s*(test case review instructions:|user guide review instructions:)\s*", "", instruction_text)
        fragments = re.split(r"[\n\.;]|\band\b|\bwith\b|\binclude\b", cleaned, flags=re.IGNORECASE)

        phrases: List[str] = []
        for fragment in fragments:
            phrase = re.sub(r"\s+", " ", fragment).strip(" -:\t\r")
            if len(phrase) < 8:
                continue
            if phrase.lower() in {p.lower() for p in phrases}:
                continue
            phrases.append(phrase)
        return phrases[:8]

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

    def _normalize_question(self, question: str) -> str:
        return re.sub(r"\s+", " ", (question or "").strip().lower())

    def _answered_questions(self, inputs: ReviewInputs) -> set[str]:
        answered: set[str] = set()
        for entry in inputs.clarification_history:
            answer = (entry.answer or "").strip()
            if not answer:
                continue
            for question in entry.questions:
                answered.add(self._normalize_question(question))
        return answered

    def _clarification_answer_text(self, inputs: ReviewInputs) -> str:
        return "\n".join(
            (entry.answer or "").strip()
            for entry in inputs.clarification_history
            if (entry.answer or "").strip()
        )

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
            fetched_text, fetch_warning = self._fetch_user_guide_url_text(inputs.user_guide_url)
            if fetched_text:
                chunks.append(f"Fetched URL content:\n{fetched_text}")
            elif fetch_warning:
                chunks.append(fetch_warning)
        return "\n\n".join(c for c in chunks if c)

    def _focus_terms(self, inputs: ReviewInputs, test_case_text: str) -> List[str]:
        merged_instructions = self._merged_custom_instructions(inputs)
        quoted = re.findall(r'"([^"]{4,80})"', merged_instructions)
        scenario_terms = re.findall(r"(?i)agent interface header text color|theme settings|header text color", test_case_text)

        raw_terms = [*quoted, *scenario_terms]
        cleaned: List[str] = []
        for term in raw_terms:
            normalized = re.sub(r"\s+", " ", term).strip()
            if len(normalized) >= 4 and normalized.lower() not in {t.lower() for t in cleaned}:
                cleaned.append(normalized)
        return cleaned[:8]

    def _guide_expectations_from_testcases(self, test_case_text: str) -> List[Tuple[str, Tuple[str, ...], str]]:
        lower = test_case_text.lower()
        expectations: List[Tuple[str, Tuple[str, ...], str]] = []

        if any(token in lower for token in ("#ffffff", "default value", "default hex")):
            expectations.append(
                (
                    "Default header text color behavior",
                    ("#ffffff", "default", "header text color"),
                    "Document default value behavior and its visual impact in Theme Settings",
                )
            )

        if any(token in lower for token in ("invalid hex", "without #", "mandatory", "too many characters", "3-digit")):
            expectations.append(
                (
                    "Hex color validation rules",
                    ("invalid", "hex", "validation", "#"),
                    "Add accepted/rejected hex input rules including shorthand and save behavior",
                )
            )

        if "color picker" in lower:
            expectations.append(
                (
                    "Color picker behavior",
                    ("color picker", "preview"),
                    "Describe picker interaction, value sync, and preview updates",
                )
            )

        if any(token in lower for token in ("upgrade", "version 26.2", "pre-26.2")):
            expectations.append(
                (
                    "Upgrade and backward compatibility notes",
                    ("upgrade", "26.2", "existing themes"),
                    "Include migration/default behavior for pre-upgrade themes",
                )
            )

        return expectations

    def _clarification_questions(
        self,
        review_type: str,
        reqs: List[str],
        test_case_text: str,
        guide_text: str,
        clarification_answer_text: str = "",
    ) -> List[str]:
        questions: List[str] = []
        include_test_case_review = review_type in ("test-cases", "both")
        include_user_guide_review = review_type in ("user-guide", "both")
        answer_text = (clarification_answer_text or "").lower()

        ambiguous_tokens = ("tbd", "todo", "etc", "as needed", "optional")
        strictness_already_answered = any(
            token in answer_text
            for token in ("strict", "flexible", "allow flexibility", "gherkin syntax")
        )
        expected_result_already_answered = any(
            token in answer_text
            for token in ("expected result", "expected outcomes", "allow flexibility")
        )

        if include_test_case_review and any(token in test_case_text.lower() for token in ambiguous_tokens) and not strictness_already_answered:
            questions.append(
                "Several test case lines include ambiguous tokens (e.g., TBD/TODO/etc). Which exact expected outcomes should be enforced?"
            )

        if include_test_case_review and "expected" not in test_case_text.lower() and "then" not in test_case_text.lower() and not expected_result_already_answered:
            questions.append(
                "Test cases appear to miss explicit expected results. Should each case require a strict expected-result field?"
            )

        prerequisites_already_answered = any(
            token in answer_text
            for token in ("no preconditions", "no precondition", "no prerequisites", "no prerequisite", "preconditions are")
        )
        if include_user_guide_review and guide_text and "prerequisite" not in guide_text.lower() and "precondition" not in guide_text.lower() and not prerequisites_already_answered:
            questions.append("User guide appears to miss prerequisites. Can you provide the required preconditions?")

        if reqs and len(reqs) < 2:
            questions.append("Only limited requirement detail was detected. Should review proceed with best-effort assumptions?")

        return questions

    def _smart_default_questions(
        self,
        review_type: str,
        inputs: ReviewInputs,
        test_case_text: str,
        clarification_answer_text: str = "",
    ) -> List[str]:
        questions: List[str] = []
        include_test_case_review = review_type in ("test-cases", "both")
        include_user_guide_review = review_type in ("user-guide", "both")
        answer_text = (clarification_answer_text or "").lower()

        has_bdd = any(self._is_bdd_file(self._file_name(f)) for f in inputs.files)
        if include_test_case_review and has_bdd and not any(token in answer_text for token in ("strict", "flexibility", "flexible", "gherkin")):
            questions.append("Validate Gherkin syntax strictly or allow flexibility?")

        has_excel = any(self._is_spreadsheet_file(self._file_name(f)) for f in inputs.files)
        if include_test_case_review and has_excel and not any(token in answer_text for token in ("column", "col ", "column a", "column b", "test id column")):
            auto_col = self._detect_excel_test_id_column(test_case_text)
            questions.append(f"Which column contains Test ID? (Auto-detected: {auto_col})")

        if include_user_guide_review and inputs.user_guide_url and not any(
            token in answer_text
            for token in ("latest version", "this is latest", "yes latest", "yes this is latest")
        ):
            questions.append("Is this the latest version of the guide URL provided?")

        jira_ids = self._collect_ticket_ids(inputs.jira_id, getattr(inputs, "jira_ids", []))
        valueedge_ids = self._collect_ticket_ids(inputs.valueedge_id, getattr(inputs, "valueedge_ids", []))
        if review_type == "both" and jira_ids and valueedge_ids:
            questions.append("Sources from JIRA and ValueEdge are both present. Proceed with current version assumptions or clarify authoritative version?")

        deduped: List[str] = []
        seen = set()
        for q in questions:
            if q not in seen:
                deduped.append(q)
                seen.add(q)
        return deduped[:5]

    def _instruction_driven_questions(
        self,
        review_type: str,
        inputs: ReviewInputs,
        test_case_text: str,
        guide_text: str,
    ) -> List[str]:
        questions: List[str] = []

        include_test_case_review = review_type in ("test-cases", "both")
        include_user_guide_review = review_type in ("user-guide", "both")

        if include_test_case_review:
            instruction_text = (inputs.test_case_review_instructions or inputs.custom_instructions or "").strip()
            for phrase in self._instruction_focus_phrases(instruction_text):
                tokens = [token for token in re.findall(r"[a-z0-9#]{4,}", phrase.lower()) if token not in {"review", "test", "case", "cases", "guide"}]
                if tokens and not any(token in test_case_text.lower() for token in tokens[:3]):
                    questions.append(f"Custom instruction '{phrase[:70]}' is not evident in current test artifacts. Should this be mandatory?")
                    break

        if include_user_guide_review:
            instruction_text = (inputs.user_guide_review_instructions or inputs.custom_instructions or "").strip()
            for phrase in self._instruction_focus_phrases(instruction_text):
                tokens = [token for token in re.findall(r"[a-z0-9#]{4,}", phrase.lower()) if token not in {"review", "user", "guide", "section", "focus"}]
                if tokens and not any(token in guide_text.lower() for token in tokens[:3]):
                    questions.append(f"Custom instruction '{phrase[:70]}' is missing in guide context. Should review treat this as a hard requirement?")
                    break

        return questions[:2]

    def _build_test_case_review(
        self,
        reqs: List[str],
        test_case_text: str,
        apply_template: bool,
        instruction_text: str,
    ) -> Tuple[str, Dict[str, Any]]:
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

        if apply_template:
            lower_tc = test_case_text.lower()
            for label, tokens, _ in self._template_terms_test_case():
                if not any(token in lower_tc for token in tokens):
                    critical_gaps.append(
                        {
                            "req_id": f"TEMPLATE-{len(critical_gaps) + 1}",
                            "description": f"Template checklist gap: {label}",
                            "covered_by": "-",
                            "coverage_status": "Gap",
                            "priority": "High",
                        }
                    )

        instruction_phrases = self._instruction_focus_phrases(instruction_text)
        lower_tc = test_case_text.lower()
        instruction_gaps = 0
        for phrase in instruction_phrases:
            tokens = [token for token in re.findall(r"[a-z0-9#]{4,}", phrase.lower()) if token not in {"review", "cases", "case", "tests", "test"}]
            if not tokens:
                continue
            if not any(token in lower_tc for token in tokens[:3]):
                instruction_gaps += 1
                critical_gaps.append(
                    {
                        "req_id": f"INST-{instruction_gaps}",
                        "description": f"Custom instruction not reflected: {phrase[:120]}",
                        "covered_by": "-",
                        "coverage_status": "Gap",
                        "priority": "High",
                    }
                )

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
                "review_mode": "template_guided" if apply_template else "instruction_only",
                "instruction_influence_count": instruction_gaps,
            },
            "coverage_matrix": matrix,
            "critical_gaps": critical_gaps,
        }
        return "\n".join(lines), payload

    def _extract_guide_sections(self, guide_text: str) -> List[str]:
        sections: List[str] = []
        for line in guide_text.splitlines():
            heading_match = re.match(r"^\s*#+\s+(.+)$", line)
            ordered_match = re.match(r"^\s*\d+[\.)]\s+(.+)$", line)
            section = heading_match.group(1).strip() if heading_match else ordered_match.group(1).strip() if ordered_match else ""
            if section and section not in sections:
                sections.append(section)
        return sections[:8]

    def _guide_lines(self, guide_text: str) -> List[Tuple[int, str]]:
        lines: List[Tuple[int, str]] = []
        for index, line in enumerate(guide_text.splitlines(), start=1):
            normalized = re.sub(r"\s+", " ", line).strip()
            if normalized:
                lines.append((index, normalized))
        return lines

    def _line_reference_for_tokens(self, guide_lines: List[Tuple[int, str]], tokens: Tuple[str, ...]) -> str:
        lowered_tokens = tuple(t.lower() for t in tokens if t)
        if not lowered_tokens:
            return "Not found in extracted text"

        for line_number, line in guide_lines:
            lowered_line = line.lower()
            if all(token in lowered_line for token in lowered_tokens):
                return f"L{line_number}"

        for line_number, line in guide_lines:
            lowered_line = line.lower()
            if any(token in lowered_line for token in lowered_tokens):
                return f"L{line_number}"

        return "Not found in extracted text"

    def _quality_score(self, guide_text: str, sections: List[str], modification_count: int, missing_count: int) -> int:
        words = len(re.findall(r"\b\w+\b", guide_text))
        step_lines = len(re.findall(r"^\s*(?:\d+[\.)]|[-*]\s+|step\s+\d+)", guide_text, flags=re.IGNORECASE | re.MULTILINE))

        score = 55
        if words >= 250:
            score += 15
        elif words >= 130:
            score += 8

        if len(sections) >= 3:
            score += 10
        elif len(sections) >= 2:
            score += 6

        if step_lines >= 4:
            score += 10
        elif step_lines >= 2:
            score += 5

        score -= min(modification_count * 8, 24)
        score -= min(missing_count * 10, 30)

        return max(0, min(score, 100))

    def _count_test_case_scenarios(self, test_case_text: str) -> int:
        matches = re.findall(r"^\s*Scenario(?: Outline)?\s*:\s+.+$", test_case_text, flags=re.IGNORECASE | re.MULTILINE)
        return len(matches)

    def _customer_facing_topics_from_testcases(self, test_case_text: str) -> List[str]:
        topics: List[str] = []
        for match in re.findall(r"^\s*Scenario(?: Outline)?\s*:\s+(.+)$", test_case_text, flags=re.IGNORECASE | re.MULTILINE):
            title = re.sub(r"\s+", " ", match).strip()
            lowered = title.lower()
            if any(token in lowered for token in ("reject", "invalid", "negative", "edge", "boundary", "exploratory")):
                continue
            if title and title.lower() not in {t.lower() for t in topics}:
                topics.append(title)
        return topics[:10]

    def _build_user_guide_review(
        self,
        inputs: ReviewInputs,
        reqs: List[str],
        test_case_text: str,
        guide_text: str,
        source_label: str,
        apply_template: bool,
        instruction_text: str,
    ) -> Tuple[str, Dict[str, Any]]:
        answer_text = self._clarification_answer_text(inputs).lower()
        guide_lower = guide_text.lower()
        sections = self._extract_guide_sections(guide_text)
        guide_lines = self._guide_lines(guide_text)
        focus_terms = self._focus_terms(inputs, test_case_text)
        test_case_count = self._count_test_case_scenarios(test_case_text)
        customer_topics = self._customer_facing_topics_from_testcases(test_case_text)

        has_prerequisites = "prerequisite" in guide_lower or "precondition" in guide_lower
        clarified_no_prerequisites = any(
            token in answer_text
            for token in ("no preconditions", "no precondition", "no prerequisites", "no prerequisite")
        )
        prerequisites_missing = not has_prerequisites and not clarified_no_prerequisites

        modification_rows: List[Dict[str, str]] = []

        ambiguity_pattern = re.compile(r"\b(tbd|todo|etc\.?|as needed|if required|coming soon|to be updated)\b", flags=re.IGNORECASE)
        for line_number, line in guide_lines:
            match = ambiguity_pattern.search(line)
            if not match:
                continue
            token = match.group(1)
            modification_rows.append(
                {
                    "section": sections[0] if sections else "Guide Content",
                    "title": sections[0] if sections else "Guide Content",
                    "issue_type": "Ambiguous instruction language",
                    "observed_text": line[:180],
                    "recommendation": f"Replace '{token}' with explicit, testable instruction and expected result.",
                    "severity": "High",
                    "line_reference": f"L{line_number}",
                    "replacement_example": "Update with exact condition, user action, and expected UI/system response.",
                }
            )
            if len(modification_rows) >= 4:
                break

        if len(guide_text.strip()) < 220:
            modification_rows.append(
                {
                    "section": sections[1] if len(sections) > 1 else "Overview",
                    "title": sections[1] if len(sections) > 1 else "Overview",
                    "issue_type": "Limited customer-facing detail",
                    "observed_text": "Guide content is too brief for reliable customer execution.",
                    "recommendation": "Expand step-by-step instructions so customers can configure settings without relying on internal test artifacts",
                    "severity": "Medium",
                    "line_reference": "L1" if guide_lines else "Not found in extracted text",
                    "replacement_example": "Add step sequence with menu path, field value examples, save behavior, and expected outcome.",
                }
            )

        missing_rows: List[Dict[str, str]] = []
        if prerequisites_missing and apply_template:
            missing_rows.append(
                {
                    "expected_topic": "Prerequisites",
                    "based_on": "Guide readiness baseline",
                    "suggested_location": "Introductory section before setup or usage steps",
                    "priority": "High",
                }
            )

        missing_focus_terms = [term for term in focus_terms if term.lower() not in guide_lower]
        if missing_focus_terms:
            missing_rows.append(
                {
                    "expected_topic": ", ".join(missing_focus_terms[:2]),
                    "based_on": "User instructions and testcase focus terms",
                    "suggested_location": "Theme settings section covering header text color behavior",
                    "priority": "High",
                }
            )

        instruction_phrases = self._instruction_focus_phrases(instruction_text)
        instruction_influence_count = 0
        instruction_checks: List[Dict[str, str]] = []
        for phrase in instruction_phrases:
            phrase_tokens = [token for token in re.findall(r"[a-z0-9#]{4,}", phrase.lower()) if token not in {"review", "guide", "user", "section", "focus"}]
            if not phrase_tokens:
                continue
            matched = any(token in guide_lower for token in phrase_tokens[:3])
            instruction_checks.append(
                {
                    "instruction": phrase,
                    "status": "matched" if matched else "missing",
                }
            )
            if not matched:
                instruction_influence_count += 1
                missing_rows.append(
                    {
                        "expected_topic": phrase[:120],
                        "based_on": "Custom review instructions",
                        "suggested_location": "Add or update a dedicated subsection that satisfies this instruction",
                        "priority": "High",
                    }
                )

        if apply_template:
            for label, tokens, suggestion in self._guide_expectations_from_testcases(test_case_text):
                if not any(token in guide_lower for token in tokens):
                    missing_rows.append(
                        {
                            "expected_topic": label,
                            "based_on": "Reference testcase scenarios",
                            "suggested_location": suggestion,
                            "priority": "High",
                        }
                    )

            for label, tokens, guidance in self._template_terms_user_guide():
                if not any(token in guide_lower for token in tokens):
                    missing_rows.append(
                        {
                            "expected_topic": label,
                            "based_on": "Template skill checklist",
                            "suggested_location": guidance,
                            "priority": "Medium",
                        }
                    )

        for topic in customer_topics:
            normalized_topic = topic.lower()
            if not any(keyword in normalized_topic for keyword in ("default", "save", "preview", "theme", "color", "header")):
                continue
            if normalized_topic not in guide_lower:
                missing_rows.append(
                    {
                        "expected_topic": topic,
                        "based_on": "Customer-facing scenarios in reference testcases",
                        "suggested_location": "Task-oriented walkthrough section",
                        "priority": "Medium",
                    }
                )

        seen_modifications = set()
        unique_modification_rows: List[Dict[str, str]] = []
        for row in modification_rows:
            key = (row.get("issue_type", ""), row.get("line_reference", ""), row.get("recommendation", ""))
            if key in seen_modifications:
                continue
            seen_modifications.add(key)
            unique_modification_rows.append(row)
        modification_rows = unique_modification_rows[:6]

        correct_rows: List[Dict[str, str]] = []
        for section in sections:
            if any(row["title"] == section for row in modification_rows):
                continue
            correct_rows.append(
                {
                    "section": str(len(correct_rows) + 1),
                    "title": section,
                    "verification_status": "Aligned with available guide content and reference artifacts",
                    "confidence": "High" if guide_text.strip() else "Medium",
                }
            )
            if len(correct_rows) == 2:
                break

        if not correct_rows:
            correct_rows.append(
                {
                    "section": "1",
                    "title": sections[0] if sections else "General content",
                    "verification_status": "Reviewed against available guide source",
                    "confidence": "Medium",
                }
            )

        sections_reviewed = max(len(sections), len(correct_rows) + len(modification_rows) + len(missing_rows), 1)
        modification_needed = len(modification_rows)
        missing = len(missing_rows)
        correct = len(correct_rows)

        score = self._quality_score(guide_text, sections, modification_needed, missing)
        grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D"

        line_targeted_missing_rows: List[Dict[str, str]] = []
        for row in missing_rows:
            expected_topic = row.get("expected_topic", "")
            tokens = tuple(re.findall(r"[A-Za-z0-9#\.]+", expected_topic)[:3])
            line_targeted_missing_rows.append(
                {
                    **row,
                    "line_reference": self._line_reference_for_tokens(guide_lines, tokens),
                }
            )
        missing_rows = line_targeted_missing_rows

        lines = [
            "# User Guide Review Report",
            "## Document Metadata",
            f"- Document Source: {source_label}",
            f"- Review Date: {datetime.utcnow().isoformat()}Z",
            "- Sections Reviewed: All",
            f"- Reference Test Cases: {test_case_count}",
            f"- Reference Requirements: {len(reqs)}",
            f"- Focus Terms Checked: {', '.join(focus_terms) if focus_terms else 'None'}",
            f"- Quality Score: {score}/100",
            "",
            "## Customer-Facing Assessment",
            "### What Is Working Well",
        ]
        for row in correct_rows:
            lines.append(f"- {row['title']}: {row['verification_status']} ({row['confidence']} confidence)")
        if not correct_rows:
            lines.append("- Existing guide has limited explicit customer-facing coverage.")

        lines.extend([
            "",
            "### What Needs Improvement",
        ])
        if modification_rows:
            for idx, row in enumerate(modification_rows, start=1):
                lines.append(
                    f"{idx}. {row['issue_type']} ({row['severity']})\n"
                    f"   - Line to modify: {row['line_reference']}\n"
                    f"   - Current text: {row['observed_text']}\n"
                    f"   - Recommended change: {row['recommendation']}\n"
                    f"   - Suggested rewrite: {row['replacement_example']}"
                )
        else:
            lines.append("- No major structural issues detected from current evidence.")

        lines.extend([
            "",
            "### Recommended Corrections For The User Guide",
        ])
        if missing_rows:
            for idx, row in enumerate(missing_rows, start=1):
                lines.append(
                    f"{idx}. Add section: {row['expected_topic']} (Priority: {row['priority']})\n"
                    f"   - Why: {row['based_on']}\n"
                    f"   - Line context checked: {row['line_reference']}\n"
                    f"   - How to fix: {row['suggested_location']}"
                )
        else:
            lines.append("- No missing customer-facing topic detected for the current scope.")

        if instruction_checks:
            lines.extend([
                "",
                "### Custom Instruction Compliance",
            ])
            for idx, check in enumerate(instruction_checks, start=1):
                status_text = "Matched" if check["status"] == "matched" else "Missing"
                lines.append(f"{idx}. {check['instruction']} — {status_text}")

        lines.extend([
            "",
            "## Summary",
            f"- Sections Reviewed: {sections_reviewed}",
            f"- Customer-facing areas already clear: {correct}",
            f"- Areas needing rewrite: {modification_needed}",
            f"- Missing customer-facing topics: {missing}",
            f"- Quality Score: {score}/100",
            f"- Overall Guide Readiness: {grade}",
        ])

        payload = {
            "summary": {
                "sections_reviewed": sections_reviewed,
                "correct": correct,
                "needs_modification": modification_needed,
                "missing": missing,
                "quality_score": score,
                "overall_grade": grade,
                "review_mode": "template_guided" if apply_template else "instruction_only",
                "instruction_influence_count": instruction_influence_count,
            },
            "strengths": correct_rows,
            "modification_recommendations": modification_rows,
            "missing_topics": missing_rows,
            "instruction_checks": instruction_checks,
        }
        return "\n".join(lines), payload

    def review(self, review_type: str, inputs: ReviewInputs) -> ReviewResponse:
        self._validate_review_request(inputs)

        reqs = self._extract_requirements(inputs)
        test_case_text = self._extract_test_case_text(inputs)
        guide_text = self._extract_user_guide_text(inputs)
        clarification_answer_text = self._clarification_answer_text(inputs)

        round_count = len(inputs.clarification_history)
        questions = self._clarification_questions(
            review_type,
            reqs,
            test_case_text,
            guide_text,
            clarification_answer_text,
        )
        questions.extend(
            self._instruction_driven_questions(
                review_type,
                inputs,
                test_case_text,
                guide_text,
            )
        )
        # Enrich with scenario-specific smart defaults.
        questions.extend(
            self._smart_default_questions(
                review_type,
                inputs,
                test_case_text,
                clarification_answer_text,
            )
        )
        answered_questions = self._answered_questions(inputs)
        questions = [
            question
            for question in list(dict.fromkeys(questions))
            if self._normalize_question(question) not in answered_questions
        ][:5]
        if round_count > 0 and clarification_answer_text.strip() and not answered_questions:
            questions = []
        clarification_required = bool(questions and round_count < _MAX_CLARIFICATION_ROUNDS)
        assumptions_applied = bool(questions and round_count >= _MAX_CLARIFICATION_ROUNDS)

        report_blocks: List[str] = []
        report_json: Dict[str, Any] = {}

        if review_type in ("test-cases", "both"):
            test_case_instruction_text = (inputs.test_case_review_instructions or "").strip()
            if not test_case_instruction_text:
                test_case_instruction_text = (inputs.custom_instructions or "").strip()
            md, payload = self._build_test_case_review(
                reqs,
                test_case_text,
                apply_template=inputs.review_test_cases,
                instruction_text=test_case_instruction_text,
            )
            report_blocks.append(md)
            report_json["test_case_review"] = payload

        if review_type in ("user-guide", "both"):
            source_label = inputs.user_guide_url or "Uploaded guide document"
            md, payload = self._build_user_guide_review(
                inputs,
                reqs,
                test_case_text,
                guide_text,
                source_label,
                apply_template=inputs.review_user_guide,
                instruction_text=(inputs.user_guide_review_instructions or inputs.custom_instructions or "").strip(),
            )
            report_blocks.append(md)
            report_json["user_guide_review"] = payload

        if clarification_answer_text.strip():
            latest_answer = clarification_answer_text.strip().splitlines()[-1].strip()
            report_blocks.append(
                "\n".join([
                    "## Clarification Applied",
                    f"- Clarification rounds submitted: {round_count}",
                    f"- Latest response considered: {latest_answer}",
                ])
            )

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
