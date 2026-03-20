"""
Review service for test case and user guide analysis with clarification workflow.
"""

from __future__ import annotations

import concurrent.futures
import re
import time
import uuid
import urllib.request
from datetime import datetime, timedelta
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlparse
from typing import Any, Dict, List, Tuple

from app.config import get_settings
from app.models import ReviewInputs, ReviewResponse, ReviewMetadata


_MAX_CLARIFICATION_ROUNDS = 3
_CLARIFICATION_TIMEOUT_MINUTES = 30

_EXCLUDED_TEST_TAGS = {
    "negative",
    "exploratory",
    "edgecase",
    "edge",
    "performance",
}

_EXCLUDED_TITLE_KEYWORDS = (
    "attempt to",
    "verify error",
    "validation error",
    "invalid input",
    " fail",
    "boundary",
    "rapid",
    "concurrent",
    "stress",
    "load",
    "responsiveness",
    "keyboard navigation",
)


class _GuideHTMLExtractor(HTMLParser):
    """Converts documentation HTML into readable text with lightweight structure retention."""

    def __init__(self) -> None:
        super().__init__()
        self._chunks: List[str] = []
        self._skip_depth = 0
        self._skip_tags = {
            "script",
            "style",
            "noscript",
            "nav",
            "header",
            "footer",
            "svg",
        }
        self._block_tags = {
            "p",
            "div",
            "section",
            "article",
            "main",
            "br",
            "li",
            "ul",
            "ol",
            "table",
            "tr",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
        }

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str | None]]) -> None:
        attr_text = " ".join((value or "") for _, value in attrs).lower()
        if tag in self._skip_tags or any(token in attr_text for token in ("nav", "menu", "footer", "sidebar", "breadcrumb", "toc")):
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag in self._block_tags:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self._skip_depth and tag in self._skip_tags:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag in self._block_tags:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = unescape(data or "")
        if text.strip():
            self._chunks.append(text)

    def text(self) -> str:
        merged = "".join(self._chunks)
        merged = re.sub(r"\r", "", merged)
        merged = re.sub(r"\n\s*\n\s*\n+", "\n\n", merged)
        lines = [re.sub(r"\s+", " ", line).strip() for line in merged.splitlines()]
        return "\n".join(line for line in lines if line)


class ReviewValidationError(Exception):
    """Raised when review request validation fails."""


class ReviewService:
    """Service implementing deterministic review logic for uploaded artifacts."""

    def __init__(self) -> None:
        self._states: Dict[str, Dict[str, Any]] = {}
        self._skill_cache: Dict[str, str] = {}
        try:
            self._settings = get_settings()
        except Exception:
            self._settings = None

    def _is_test_case_file(self, filename: str) -> bool:
        lower = filename.lower()
        return lower.endswith((".feature", ".xlsx", ".xls", ".txt", ".md")) and (
            "test" in lower or "case" in lower or lower.endswith(".feature") or lower.endswith(".xlsx") or lower.endswith(".xls")
        )

    def _is_user_guide_file(self, filename: str) -> bool:
        lower = filename.lower()
        return lower.endswith((".pdf", ".docx", ".txt", ".md"))

    def _has_uploaded_user_guide_content(self, inputs: ReviewInputs) -> bool:
        for file_obj in inputs.files:
            name = self._file_name(file_obj)
            text = self._file_text(file_obj)
            if self._is_user_guide_file(name) and len((text or "").strip()) >= 20:
                return True
        return False

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

    def _extract_requested_sections(self, instruction_text: str) -> List[str]:
        text = instruction_text or ""
        sections: List[str] = []

        for quoted in re.findall(r'"([^"]{3,120})"', text):
            value = re.sub(r"\s+", " ", quoted).strip()
            if value and value.lower() not in {s.lower() for s in sections}:
                sections.append(value)

        for matched in re.findall(r"(?i)(?:section|sections)\s*[:\-]\s*([A-Za-z0-9 ,/_-]{3,160})", text):
            for part in re.split(r",| and ", matched):
                value = re.sub(r"\s+", " ", part).strip(" .")
                if value and value.lower() not in {s.lower() for s in sections}:
                    sections.append(value)

        return sections[:6]

    def _is_section_only_request(self, instruction_text: str) -> bool:
        return bool(
            re.search(r"(?i)\b(read|focus|review)\b.*\b(only|specific|particular)\b.*\b(section|sections)\b", instruction_text or "")
            or re.search(r"(?i)\bonly\b.*\b(section|sections)\b", instruction_text or "")
        )

    def _filter_text_by_section_hints(self, text: str, section_hints: List[str], strict: bool) -> str:
        if not text.strip() or not section_hints:
            return text

        lines = text.splitlines()
        normalized_hints = [hint.lower() for hint in section_hints if hint.strip()]
        match_indexes: List[int] = []
        for index, line in enumerate(lines):
            lowered = line.lower()
            if any(hint in lowered for hint in normalized_hints):
                match_indexes.append(index)

        if not match_indexes:
            return "" if strict else text

        if strict:
            selected_lines: List[str] = []
            for index in match_indexes:
                pointer = index
                while pointer < len(lines):
                    current = lines[pointer]
                    if pointer > index and re.match(r"^\s*#", current):
                        break
                    selected_lines.append(current)
                    pointer += 1
            deduped = []
            seen = set()
            for line in selected_lines:
                key = line.strip().lower()
                if key and key not in seen:
                    deduped.append(line)
                    seen.add(key)
            return "\n".join(deduped)

        keep = set()
        window = 6
        for index in match_indexes:
            start = max(0, index - window)
            end = min(len(lines), index + window + 1)
            for pointer in range(start, end):
                keep.add(pointer)

        filtered = [lines[i] for i in sorted(keep) if lines[i].strip()]
        return "\n".join(filtered)

    def _run_playwright_auth_in_thread(self, url: str) -> Tuple[str, str | None]:
        """Runs inside a worker thread — opens a headed browser, waits for interactive sign-in,
        then captures and returns the page content."""
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
        except ImportError:
            return "", (
                "Playwright is not installed. "
                "Run: pip install playwright && playwright install chromium"
            )

        _LOGIN_MARKERS = (
            "login", "signin", "sign-in", "sso", "authenticate",
            "auth/", "/auth?", "opentext", "microfocus.com/login",
        )

        def _is_login_url(u: str) -> bool:
            ul = (u or "").lower()
            return any(m in ul for m in _LOGIN_MARKERS)

        target_host = urlparse(url).netloc.lower()

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=False,
                    args=["--start-maximized"],
                )
                context = browser.new_context(viewport=None)
                page = context.new_page()

                page.goto(url, wait_until="domcontentloaded", timeout=30_000)

                # Poll until the user completes sign-in and lands back on the target domain
                deadline = time.time() + 180  # 3-minute limit
                signed_in = False
                while time.time() < deadline:
                    current_url = page.url
                    current_host = urlparse(current_url).netloc.lower()
                    try:
                        page_snapshot = page.content()
                    except Exception:
                        time.sleep(1)
                        continue
                    if (
                        current_host == target_host
                        and not _is_login_url(current_url)
                        and not self._contains_auth_wall(page_snapshot)
                    ):
                        signed_in = True
                        break
                    time.sleep(2)

                if not signed_in:
                    browser.close()
                    return "", "Browser sign-in timed out (3-minute limit). Please try again."

                # Navigate to the exact target URL if we ended up on a different page (e.g. home)
                if page.url.rstrip("/") != url.rstrip("/"):
                    try:
                        page.goto(url, wait_until="networkidle", timeout=30_000)
                        time.sleep(1)
                    except Exception:
                        pass  # best-effort; use whatever page we're on

                try:
                    page.wait_for_load_state("networkidle", timeout=20_000)
                except Exception:
                    pass
                time.sleep(2)

                rendered_text = ""
                try:
                    rendered_text = page.evaluate("() => document.body ? document.body.innerText : ''") or ""
                except Exception:
                    rendered_text = ""

                html = ""
                for _ in range(5):
                    try:
                        html = page.content()
                        if html:
                            break
                    except Exception:
                        time.sleep(1)
                browser.close()
        except Exception as exc:
            return "", f"Browser auth error: {exc}"

        # Extract readable text from the captured HTML
        try:
            extracted = re.sub(r"\s+", " ", (rendered_text or "")).strip()
            if len(extracted) < 300:
                parser = _GuideHTMLExtractor()
                parser.feed(html)
                extracted = parser.text().strip()
            if len(extracted) < 300:
                extracted = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
                extracted = re.sub(r"<style[\s\S]*?</style>", " ", extracted, flags=re.IGNORECASE)
                extracted = re.sub(r"<[^>]+>", " ", extracted)
                extracted = re.sub(r"\s+", " ", extracted).strip()
            if len(extracted) < 100:
                return "", "Browser sign-in succeeded but page content appears empty"
            return extracted[:60_000], None
        except Exception as exc:
            return "", f"Content extraction after browser auth failed: {exc}"

    def _fetch_with_playwright_auth(self, url: str) -> Tuple[str, str | None]:
        """Thread-safe wrapper: runs Playwright in a dedicated worker thread to avoid
        event-loop conflicts with FastAPI's asyncio executor."""
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(self._run_playwright_auth_in_thread, url)
                return future.result(timeout=220)  # 3 min + buffer
        except concurrent.futures.TimeoutError:
            return "", "Browser sign-in timed out"
        except Exception as exc:
            return "", f"Browser auth launch failed: {exc}"

    def _contains_auth_wall(self, text: str) -> bool:
        lower = (text or "").lower()
        auth_markers = (
            "please sign in",
            "sign in",
            "sign-in",
            "login",
            "opentext sign-in",
            "single sign-on",
            "sso",
            "access denied",
            "forbidden",
            "authentication required",
        )
        return any(marker in lower for marker in auth_markers)

    def _looks_like_portal_shell(self, body: str, extracted_text: str) -> bool:
        body_lower = (body or "").lower()
        shell_markers = (
            "enable javascript",
            "loading...",
            "app-root",
            "id=\"root\"",
            "id='root'",
            "__next",
            "data-reactroot",
            "cloudflare",
        )
        marker_hit = any(marker in body_lower for marker in shell_markers)
        very_short = len((extracted_text or "").strip()) < 350

        # Any explicit auth-wall marker should trigger fallback regardless of text length.
        return self._contains_auth_wall(body) or self._contains_auth_wall(extracted_text) or (marker_hit and very_short)

    def _build_guide_fetch_headers(self, session_cookie: str | None = None) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        settings = getattr(self, "_settings", None)

        # Per-request cookie from UI takes priority, then fall back to .env settings
        per_request_cookie = (session_cookie or "").strip()
        if per_request_cookie:
            headers["Cookie"] = per_request_cookie
        elif settings is not None:
            env_cookie = (getattr(settings, "guide_fetch_cookie", None) or "").strip()
            if env_cookie:
                headers["Cookie"] = env_cookie

        if settings is not None:
            auth = (getattr(settings, "guide_fetch_authorization", None) or "").strip()
            if auth:
                headers["Authorization"] = auth
        return headers

    def _fetch_reader_proxy_text(self, target_url: str) -> Tuple[str, str | None]:
        encoded_target = quote((target_url or "").strip(), safe=":/?&=#%")
        proxy_url = f"https://r.jina.ai/http://{encoded_target}" if not encoded_target.startswith("http") else f"https://r.jina.ai/{encoded_target}"

        try:
            req = urllib.request.Request(
                proxy_url,
                headers={
                    "User-Agent": "TestGen-AI-ReviewBot/1.0",
                    "Accept": "text/plain,text/markdown;q=0.9,*/*;q=0.8",
                },
            )
            with urllib.request.urlopen(req, timeout=25) as response:
                body = response.read().decode("utf-8", errors="ignore")

            cleaned = re.sub(r"^\s*URL Source:.*$", "", body, flags=re.IGNORECASE | re.MULTILINE)
            cleaned = re.sub(r"^\s*Markdown Content:\s*$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
            cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)
            cleaned = cleaned.strip()
            if self._contains_auth_wall(cleaned):
                return "", "Reader proxy returned authentication wall"
            if len(cleaned) < 300:
                return "", "Reader proxy returned insufficient content"
            return cleaned[:60000], None
        except Exception as exc:
            return "", f"Reader proxy fetch failed: {exc}"

    def _fetch_user_guide_url_text(
        self,
        url: str,
        section_hints: List[str],
        strict_section_only: bool,
        session_cookie: str | None = None,
    ) -> Tuple[str, str | None]:
        parsed = urlparse((url or "").strip())
        if parsed.netloc.lower() in {"example.com", "www.example.com"}:
            return "", "Skipped remote fetch for placeholder domain"

        try:
            req = urllib.request.Request(url, headers=self._build_guide_fetch_headers(session_cookie))
            with urllib.request.urlopen(req, timeout=20) as response:
                body = response.read().decode("utf-8", errors="ignore")

            parser = _GuideHTMLExtractor()
            parser.feed(body)
            extracted = parser.text()
            if not extracted.strip():
                extracted = re.sub(r"<script[\s\S]*?</script>", " ", body, flags=re.IGNORECASE)
                extracted = re.sub(r"<style[\s\S]*?</style>", " ", extracted, flags=re.IGNORECASE)
                extracted = re.sub(r"<[^>]+>", " ", extracted)
                extracted = re.sub(r"\s+", " ", extracted).strip()

            if self._looks_like_portal_shell(body, extracted):
                proxy_text, proxy_warning = self._fetch_reader_proxy_text(url)
                if proxy_text:
                    extracted = proxy_text
                else:
                    # Final fallback: open a headed browser for interactive sign-in
                    pw_text, pw_warn = self._fetch_with_playwright_auth(url)
                    if pw_text:
                        extracted = pw_text
                    else:
                        return "", pw_warn or proxy_warning

            filtered = self._filter_text_by_section_hints(extracted, section_hints, strict_section_only)
            if strict_section_only and section_hints and not filtered.strip():
                return "", "Requested sections were not found in extracted guide content"

            return filtered[:60000], None
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
            has_user_guide_file = any(self._is_user_guide_file(self._file_name(f)) for f in inputs.files)
            if not has_user_guide_file:
                raise ReviewValidationError("Please attach user guide files (.pdf, .docx, .txt, .md)")

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
        if review_type == "both" and guide_text and "prerequisite" not in guide_text.lower() and "precondition" not in guide_text.lower() and not prerequisites_already_answered:
            questions.append("User guide appears to miss prerequisites. Can you provide the required preconditions?")

        if include_test_case_review and reqs and len(reqs) < 2:
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

    def _parse_feature_scenarios(self, test_case_text: str) -> List[Dict[str, Any]]:
        scenarios: List[Dict[str, Any]] = []
        pending_tags: List[str] = []
        current: Dict[str, Any] | None = None

        for raw_line in test_case_text.splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                continue

            if stripped.startswith("@"):
                tag_tokens = [token.strip().lstrip("@").lower() for token in stripped.split() if token.strip().startswith("@")]
                pending_tags.extend(tag_tokens)
                continue

            scenario_match = re.match(r"(?i)^\s*Scenario(?: Outline)?\s*:\s*(.+)$", stripped)
            if scenario_match:
                if current:
                    scenarios.append(current)
                current = {
                    "title": re.sub(r"\s+", " ", scenario_match.group(1)).strip(),
                    "tags": list(dict.fromkeys(pending_tags)),
                    "steps": [],
                }
                pending_tags = []
                continue

            if current and re.match(r"(?i)^\s*(Given|When|Then|And|But)\b", stripped):
                current["steps"].append(stripped)

        if current:
            scenarios.append(current)

        return scenarios

    def _is_customer_facing_scenario(self, scenario: Dict[str, Any]) -> bool:
        tags = {str(tag).lower() for tag in scenario.get("tags", [])}
        title = str(scenario.get("title", "")).lower()
        joined_steps = " ".join(str(step).lower() for step in scenario.get("steps", []))
        combined = f"{title} {joined_steps}"

        if any(tag in _EXCLUDED_TEST_TAGS for tag in tags):
            return False
        if any(keyword in combined for keyword in _EXCLUDED_TITLE_KEYWORDS):
            return False
        if "ui" in tags and ("responsive" in combined or "resolution" in combined):
            return False
        if "accessibility" in tags:
            return False
        return True

    def _count_test_case_scenarios(self, test_case_text: str) -> int:
        return len(self._parse_feature_scenarios(test_case_text))

    def _customer_facing_topics_from_testcases(self, test_case_text: str) -> List[str]:
        topics: List[str] = []
        for scenario in self._parse_feature_scenarios(test_case_text):
            if not self._is_customer_facing_scenario(scenario):
                continue
            title = str(scenario.get("title", "")).strip()
            if title and title.lower() not in {t.lower() for t in topics}:
                topics.append(title)
        return topics[:24]

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
        guide_lower = guide_text.lower()
        guide_lines = self._guide_lines(guide_text)
        line_lookup = {line_number: line for line_number, line in guide_lines}
        sections = self._extract_guide_sections(guide_text)
        uploaded_guide_available = self._has_uploaded_user_guide_content(inputs)
        low_confidence_guide = (not uploaded_guide_available) and (
            len(guide_text.strip()) < 400
            or "url content fetch failed" in guide_lower
            or "requested sections were not found" in guide_lower
        )

        if low_confidence_guide and not uploaded_guide_available:
            lines = [
                "# User Guide Review Report",
                "## Review Context",
                f"- Document Source: {source_label}",
                f"- Review Date: {datetime.utcnow().isoformat()}Z",
                "- Analysis Status: Uploaded guide content unavailable or not extractable",
                "",
                "## Blocker",
                "Attached user guide documents did not provide extractable documentation content.",
                "",
                "## Action Required",
                "1. Attach one or more user guide files (.pdf/.docx/.md/.txt) with selectable text content.",
                "2. Rerun review after confirming files are parsed successfully in upload preview.",
                "3. Ensure section-specific instructions are provided when partial review is needed.",
                "",
                "## Defect Log",
                "1. [HIGH] Source Access Gap - User guide body could not be extracted from attached files.",
                "",
                "## Priority Actions",
                "1. HIGH: Upload readable guide artifact(s) to unlock accurate coverage/clarity analysis.",
            ]

            payload = {
                "summary": {
                    "sections_reviewed": 0,
                    "correct": 0,
                    "needs_modification": 0,
                    "missing": 1,
                    "quality_score": 0,
                    "overall_grade": "D",
                    "review_mode": "template_guided" if apply_template else "instruction_only",
                    "instruction_influence_count": 0,
                },
                "strengths": [],
                "modification_recommendations": [],
                "missing_topics": [
                    {
                        "expected_topic": "Guide source acquisition",
                        "feature": "Guide source acquisition",
                        "test_case": "All related scenarios",
                        "what": "Attached guide content extraction failed.",
                        "impact": "Coverage and traceability analysis cannot be trusted without actual guide content.",
                        "suggested_location": "Not available",
                        "suggested_text": "Attach readable guide document(s) and rerun review.",
                        "add_text": "Attach readable guide document(s) and rerun review.",
                        "traceability": "Not available",
                        "severity": "HIGH",
                    }
                ],
                "instruction_checks": [],
                "defects": [
                    {
                        "severity": "HIGH",
                        "type": "Source Access Gap",
                        "feature": "Guide file content extraction",
                        "details": "Attached guide files did not yield extractable review content.",
                    }
                ],
            }
            return "\n".join(lines), payload
        scenarios = [
            scenario
            for scenario in self._parse_feature_scenarios(test_case_text)
            if self._is_customer_facing_scenario(scenario)
        ]

        if not sections:
            sections = [
                "Purge Configuration",
                "Rule Creation",
                "Rule Management",
                "Scheduling",
                "Audit",
            ]

        documented_rows: List[Dict[str, str]] = []
        missing_rows: List[Dict[str, str]] = []
        clarity_rows: List[Dict[str, str]] = []

        ambiguity_pattern = re.compile(r"\b(tbd|todo|etc\.?|as needed|if required|coming soon|to be updated)\b", flags=re.IGNORECASE)
        for line_number, line in guide_lines:
            if len(clarity_rows) >= 8:
                break
            if not ambiguity_pattern.search(line):
                continue
            clarity_rows.append(
                {
                    "feature": "Instruction clarity",
                    "current": line[:220],
                    "issue": "Ambiguous wording does not provide customer-executable guidance.",
                    "corrected": "Replace with explicit action, required values, and expected result after save.",
                    "line_reference": f"L{line_number}",
                    "severity": "MEDIUM",
                }
            )

        for scenario_index, scenario in enumerate(scenarios, start=1):
            title = str(scenario.get("title", "")).strip()
            testcase_id = f"TC-{scenario_index:03d}"
            generic_tokens = {
                "verify", "create", "rule", "rules", "with", "for", "using", "from", "that", "this", "when", "then",
                "purge", "feature", "configuration", "config", "settings", "section", "scenario", "existing", "new",
            }
            tokens = [
                token
                for token in re.findall(r"[a-z0-9#]{4,}", title.lower())
                if token not in generic_tokens
            ][:5]

            line_reference = "Not found in extracted text"
            best_partial_reference = "Not found in extracted text"
            best_partial_hits = 0
            covered = False
            if not low_confidence_guide and len(tokens) >= 2:
                required_hits = 3 if len(tokens) >= 4 else 2
                for line_number, line in guide_lines:
                    if line_number <= 5:
                        continue
                    lowered = line.lower()
                    hits = sum(1 for token in tokens if token in lowered)
                    if hits > best_partial_hits:
                        best_partial_hits = hits
                        best_partial_reference = f"L{line_number}"
                    if hits >= required_hits:
                        line_reference = f"L{line_number}"
                        covered = True
                        break

            where_to_find = sections[0]
            if covered and line_reference.startswith("L"):
                where_to_find = f"{sections[0]} ({line_reference})"

            if covered:
                documented_rows.append(
                    {
                        "test_case_id": testcase_id,
                        "test_case": title,
                        "feature": title,
                        "where": where_to_find,
                        "description": "User guide includes customer-visible behavior for this workflow.",
                        "benefit": "Helps administrators configure purge behavior reliably.",
                        "traceability": line_reference,
                    }
                )
            elif best_partial_hits >= 1 and best_partial_reference.startswith("L"):
                line_number_match = re.match(r"^L(\d+)$", best_partial_reference)
                observed_text = ""
                if line_number_match:
                    observed_text = line_lookup.get(int(line_number_match.group(1)), "")
                clarity_rows.append(
                    {
                        "feature": title,
                        "test_case_id": testcase_id,
                        "test_case": title,
                        "current": observed_text[:220],
                        "issue": "Guide text is partially aligned but not detailed enough for full testcase execution.",
                        "corrected": (
                            f"For {testcase_id} ({title}), provide explicit prerequisites, steps, field values, "
                            "validation behavior, and expected result."
                        ),
                        "line_reference": best_partial_reference,
                        "issue_type": "Partial coverage needs modification",
                        "recommendation": "Expand this line/section with complete procedural and validation detail.",
                        "replacement_example": (
                            f"{title}: 1) Open Purge Configuration. 2) Configure required fields exactly. "
                            "3) Save. 4) Verify expected output and audit/log result."
                        ),
                        "severity": "MEDIUM",
                    }
                )
            else:
                missing_rows.append(
                    {
                        "test_case_id": testcase_id,
                        "test_case": title,
                        "feature": title,
                        "what": "Customer-facing workflow exists in testcase coverage but is not clearly documented in guide text.",
                        "impact": "Customers may misconfigure purge behavior, causing compliance and retention risk.",
                        "add_text": (
                            f"Add a section for '{title}' with navigation path, required fields, save behavior, "
                            "and expected outcome."
                        ),
                        "suggested_location": f"Add under {sections[0]} as subsection for {testcase_id}.",
                        "suggested_text": (
                            f"{title}: 1) Open Purge Configuration. 2) Enter required values. "
                            "3) Save. 4) Confirm expected behavior and trace evidence."
                        ),
                        "traceability": "Not found in extracted text",
                        "severity": "HIGH",
                    }
                )

        if apply_template:
            instruction_phrases = self._instruction_focus_phrases(instruction_text)
            instruction_checks: List[Dict[str, str]] = []
            instruction_influence_count = 0
            for phrase in instruction_phrases:
                phrase_tokens = tuple(
                    token
                    for token in re.findall(r"[a-z0-9#]{4,}", phrase.lower())
                    if token not in {"review", "user", "guide", "section", "focus"}
                )[:4]
                matched = bool(phrase_tokens) and any(token in guide_lower for token in phrase_tokens)
                instruction_checks.append({"instruction": phrase, "status": "matched" if matched else "missing"})
                if not matched:
                    instruction_influence_count += 1
        else:
            instruction_checks = []
            instruction_influence_count = 0

        seen_missing = set()
        deduped_missing_rows: List[Dict[str, str]] = []
        for row in missing_rows:
            key = (row.get("feature", ""), row.get("traceability", ""))
            if key in seen_missing:
                continue
            seen_missing.add(key)
            deduped_missing_rows.append(row)
        missing_rows = deduped_missing_rows[:24]
        documented_rows = documented_rows[:24]

        detailed_strengths: List[Dict[str, str]] = []
        for row in documented_rows:
            line_ref = row.get("traceability", "Not found in extracted text")
            line_number_match = re.match(r"^L(\d+)$", line_ref)
            evidence_text = ""
            if line_number_match:
                evidence_text = line_lookup.get(int(line_number_match.group(1)), "")
            test_case_label = row.get("test_case", row.get("feature", "N/A"))
            test_case_id = row.get("test_case_id", "")
            full_test_case = f"{test_case_id} - {test_case_label}" if test_case_id else test_case_label
            detailed_strengths.append(
                {
                    "title": row.get("feature", "Matched topic"),
                    "section": row.get("where", "Guide section"),
                    "verification_status": "Mapped to explicit user-guide evidence.",
                    "test_case": full_test_case,
                    "line_reference": line_ref,
                    "evidence": evidence_text,
                    "customer_benefit": row.get("benefit", ""),
                    "traceability": line_ref,
                }
            )

        detailed_missing_topics: List[Dict[str, str]] = []
        for row in missing_rows:
            feature = row.get("feature", "Missing topic")
            test_case_label = row.get("test_case", feature)
            test_case_id = row.get("test_case_id", "")
            full_test_case = f"{test_case_id} - {test_case_label}" if test_case_id else test_case_label
            suggested_text = (
                f"Add subsection '{feature}' with prerequisites, exact inputs, validation rules, expected save result, "
                "and one complete customer-facing example."
            )
            detailed_missing_topics.append(
                {
                    "expected_topic": feature,
                    "feature": feature,
                    "test_case": full_test_case,
                    "why_missing": row.get("what", ""),
                    "customer_impact": row.get("impact", ""),
                    "suggested_location": row.get("suggested_location", row.get("traceability", "Not found in extracted text")),
                    "traceability": row.get("traceability", "Not found in extracted text"),
                    "add_text": row.get("add_text", suggested_text),
                    "suggested_text": row.get("suggested_text", suggested_text),
                    "severity": row.get("severity", "HIGH"),
                }
            )

        detailed_modifications: List[Dict[str, str]] = []
        for row in clarity_rows:
            test_case_label = row.get("test_case", "All related customer-facing scenarios")
            test_case_id = row.get("test_case_id", "")
            full_test_case = f"{test_case_id} - {test_case_label}" if test_case_id else test_case_label
            detailed_modifications.append(
                {
                    "issue_type": row.get("issue_type", row.get("issue", "Modification required")),
                    "feature": row.get("feature", "Instruction clarity"),
                    "line_reference": row.get("line_reference", "Not found in extracted text"),
                    "observed_text": row.get("current", ""),
                    "recommendation": row.get("recommendation", row.get("issue", "")),
                    "replacement_example": row.get("replacement_example", row.get("corrected", "")),
                    "test_case": full_test_case,
                    "severity": row.get("severity", "MEDIUM"),
                }
            )

        defects: List[Dict[str, str]] = []
        for row in missing_rows:
            defects.append(
                {
                    "severity": row["severity"],
                    "type": "Coverage Gap",
                    "feature": row["feature"],
                    "details": row["impact"],
                }
            )
        for row in clarity_rows:
            defects.append(
                {
                    "severity": row["severity"],
                    "type": "Clarity",
                    "feature": row["feature"],
                    "details": row["issue"],
                }
            )

        severity_rank = {"HIGH": 1, "MEDIUM": 2, "LOW": 3}
        defects.sort(key=lambda item: severity_rank.get(item["severity"], 9))

        high_actions = [d for d in defects if d["severity"] == "HIGH"]
        medium_actions = [d for d in defects if d["severity"] == "MEDIUM"]
        low_actions = [d for d in defects if d["severity"] == "LOW"]

        score = self._quality_score(guide_text, sections, len(clarity_rows), len(missing_rows))
        grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D"

        lines = [
            "# Purge Configuration Feature",
            "## User Guide Gap Analysis",
            "Customer-Focused Analysis: What Users Need to Know to Configure and Use the Feature",
            "",
            "Status | Meaning | Customer Impact",
            "--- | --- | ---",
            "DOCUMENTED | Feature explained in user guide | Customers can use this capability",
            "MISSING | Feature NOT documented | Customers unaware this exists",
            "NEEDS CLARITY | Documentation unclear | Customers may be confused",
            "",
            "# User Guide Review Report",
            "## Review Context",
            f"- Document Source: {source_label}",
            f"- Review Date: {datetime.utcnow().isoformat()}Z",
            f"- Guide Sections Detected: {', '.join(sections)}",
            f"- Included Customer-Facing Test Cases: {len(scenarios)}",
            f"- Ignored Scenarios (negative/edge/exploratory/performance): {max(self._count_test_case_scenarios(test_case_text) - len(scenarios), 0)}",
            f"- Quality Score: {score}/100 ({grade})",
            "",
            "## 1) FEATURES PROPERLY DOCUMENTED (MATCHING TEST CASES)",
        ]

        if detailed_strengths:
            for row in detailed_strengths:
                lines.extend(
                    [
                        f"Matched Test Case: {row['test_case']}",
                        f"Guide Section: {row['section']}",
                        f"Guide Evidence Line: {row['line_reference']}",
                        f"Guide Evidence Text: {row['evidence'] or 'Line content available in source guide.'}",
                        f"Why this is matching: {row['verification_status']}",
                        f"Customer Benefit: {row['customer_benefit']}",
                        "",
                    ]
                )
        else:
            lines.append("No fully documented customer-facing feature could be confidently mapped from extracted content.")

        lines.extend([
            "",
            "## 2) FEATURES NOT DOCUMENTED (MISSING TEST CASE COVERAGE)",
        ])
        if detailed_missing_topics:
            for row in detailed_missing_topics:
                lines.extend(
                    [
                        f"Missing Test Case: {row['test_case']}",
                        f"What is missing: {row['why_missing']}",
                        f"Customer impact: {row['customer_impact']}",
                        f"Where to add in guide: {row['suggested_location']}",
                        f"Exact text to add (example): {row['suggested_text']}",
                        f"Traceability: {row['traceability']}",
                        "",
                    ]
                )
        else:
            lines.append("No major coverage gaps detected for filtered customer-facing scenarios.")

        lines.extend([
            "",
            "## 3) NEEDS MODIFICATION (EXACT LINE + CORRECTION)",
        ])
        if detailed_modifications:
            for row in detailed_modifications:
                lines.extend(
                    [
                        f"Affected Test Cases: {row['test_case']}",
                        f"Line: {row['line_reference']}",
                        f"Line to modify: {row['line_reference']}",
                        f"Current text: \"{row['observed_text']}\"",
                        f"What modification is required: {row['recommendation']}",
                        f"How it should look after correction: {row['replacement_example']}",
                        "",
                    ]
                )
        else:
            lines.append("No high-confidence clarity defects were found in extracted lines.")

        lines.extend([
            "",
            "## DEFECT LOG",
        ])
        if defects:
            for index, defect in enumerate(defects, start=1):
                lines.append(f"{index}. [{defect['severity']}] {defect['type']} - {defect['feature']}: {defect['details']}")
        else:
            lines.append("No defects recorded.")

        lines.extend([
            "",
            "## PRIORITY ACTIONS",
            "1. HIGH severity items first",
        ])
        for defect in high_actions[:5]:
            lines.append(f"   - Fix: {defect['feature']} ({defect['type']})")
        lines.append("2. MEDIUM severity items next")
        for defect in medium_actions[:5]:
            lines.append(f"   - Improve: {defect['feature']} ({defect['type']})")
        lines.append("3. LOW severity items last")
        for defect in low_actions[:5]:
            lines.append(f"   - Polish: {defect['feature']} ({defect['type']})")

        if instruction_checks:
            lines.extend([
                "",
                "## Custom Instruction Compliance",
                "Custom review instructions were evaluated against extracted guide content.",
            ])
            for check in instruction_checks:
                lines.append(f"- {check['instruction']} => {check['status']}")

        lines.extend([
            "",
            "## 4) RECOMMENDED DOCUMENTATION STRUCTURE",
            "Section | Content | Priority",
            "--- | --- | ---",
            "Overview | What purge does, soft vs hard delete concepts | High",
            "Prerequisites | Administrator role required, enable in Application Settings | High",
            "Creating a Purge Rule | Step-by-step guide with screenshots | High",
            "Duration Configuration | Validation rules with examples | High",
            "Schedule Configuration | Recurrence, max execution time, best practices | High",
            "Entity Selection | OOTB vs custom entities, phase selection | Medium",
            "Hard Deletion Warning | Sensitive entities, acknowledgement process | High",
            "Managing Rules | Edit, activate/deactivate, delete, discard changes | Medium",
            "What Happens to Records | Soft delete visibility, recovery, permanent deletion | High",
            "Audit Trail | Viewing logs, compliance information | High",
            "Upgrading from 26.1 | Default rule explanation for existing customers | High",
            "Troubleshooting | Common issues and solutions | Medium",
            "FAQ | Quick answers to common questions | Low",
            "",
            "Key Customer Questions the Guide Should Answer:",
            "- What is the difference between soft and hard delete?",
            "- How do I recover a record that was purged?",
            "- Who can configure purge rules?",
            "- Why can't I select certain end phases?",
            "- What happens when I upgrade from 26.1?",
            "- How long should I set the durations?",
            "- Will purge affect system performance?",
            "- Where can I see what was purged?",
        ])

        payload = {
            "summary": {
                "sections_reviewed": max(len(sections), 1),
                "correct": len(documented_rows),
                "needs_modification": len(clarity_rows),
                "missing": len(missing_rows),
                "quality_score": score,
                "overall_grade": grade,
                "review_mode": "template_guided" if apply_template else "instruction_only",
                "instruction_influence_count": instruction_influence_count,
            },
            "strengths": detailed_strengths,
            "modification_recommendations": detailed_modifications,
            "missing_topics": detailed_missing_topics,
            "instruction_checks": instruction_checks,
            "defects": defects,
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
        non_blocking_user_guide_mode = review_type == "user-guide"
        clarification_required = bool(questions and round_count < _MAX_CLARIFICATION_ROUNDS)
        assumptions_applied = bool(questions and round_count >= _MAX_CLARIFICATION_ROUNDS)
        if non_blocking_user_guide_mode:
            clarification_required = False
            assumptions_applied = bool(questions)

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
            source_label = "Uploaded guide document(s)"
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

        clarification_hints = questions if (clarification_required or non_blocking_user_guide_mode) else []

        metadata = ReviewMetadata(
            review_type=review_type,  # type: ignore[arg-type]
            clarification_required=clarification_required,
            clarification_questions=clarification_hints,
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
