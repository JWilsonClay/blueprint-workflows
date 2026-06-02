"""
plan_parser.py — Implementation Plan Locator + Parser
======================================================
Two responsibilities:

  1. locate_plan(): find the implementation plan deterministically, fixing the
     historical /focus-plan bug where Phase 0 looked for `implementation_plan.md`
     (underscore) while the suite generator writes `implementation-plan.md`
     (hyphen). Canonical name wins; the legacy underscore name is tolerated.

  2. parse(): split the plan into items (one per `##`/`###`/`####` header) and
     extract verifiable *anchors* from each item — file paths and code symbols
     the substrate can be checked against. Extraction is deliberately
     conservative: symbols are only taken from inline-code spans and must look
     like code (not English prose), so the anchor list is precise rather than
     noisy.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from focus._utils import CODE_EXTENSIONS, safe_read

# Canonical plan filename (what /implementation-plan produces) and the legacy
# underscore spelling tolerated for backward compatibility.
CANONICAL_PLAN_NAME = "implementation-plan.md"
LEGACY_PLAN_NAME = "implementation_plan.md"

_HEADER_RE = re.compile(r"^(#{2,4})\s+(.*\S)\s*$")
_CHECKBOX_RE = re.compile(r"^\s*[-*]\s+\[([ xX/~])\]\s")
_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_FENCE_RE = re.compile(r"^\s*```")
# Bare (un-backticked) path-like tokens scanned out of prose/tables.
_BARE_FILE_RE = re.compile(r"(?<![\w/.])([\w][\w./-]*\.[A-Za-z0-9]{1,5})\b")
# A symbol anchor must be a single identifier (optionally dotted, optional ()).
_SYMBOL_RE = re.compile(r"^[A-Za-z_][\w]*(?:\.[A-Za-z_]\w*)*(?:\(\))?$")

_MAX_ANCHORS_PER_ITEM = 40


@dataclass
class Anchor:
    """A verifiable pointer extracted from a plan item."""
    kind: str   # "file" | "symbol"
    raw: str    # original token as written in the plan
    query: str  # normalized search term used against the substrate

    def as_dict(self) -> dict:
        return {"kind": self.kind, "raw": self.raw, "query": self.query}


@dataclass
class PlanItem:
    """One header-delimited section of the plan."""
    item_id: int
    title: str
    level: int
    source_line: int
    anchors: List[Anchor] = field(default_factory=list)


def locate_plan(workspace: Path) -> Tuple[Optional[Path], Optional[str]]:
    """
    Locate the implementation plan at the workspace root.

    Returns:
        (path, spelling) where spelling is "hyphen" or "underscore", or
        (None, None) if no plan file is present. The canonical hyphen name is
        preferred; the underscore name is only used if the hyphen is absent.
    """
    workspace = Path(workspace)
    canonical = workspace / CANONICAL_PLAN_NAME
    if canonical.is_file():
        return canonical, "hyphen"
    legacy = workspace / LEGACY_PLAN_NAME
    if legacy.is_file():
        return legacy, "underscore"
    return None, None


def _looks_like_code(token: str) -> bool:
    """Heuristic: True if *token* reads as a code identifier, not an English word."""
    core = token[:-2] if token.endswith("()") else token
    if len(core.replace(".", "")) < 3:
        return False
    if token.endswith("()") or "." in token or "_" in token:
        return True
    # CamelCase: an internal uppercase plus at least one lowercase.
    return any(c.isupper() for c in core[1:]) and any(c.islower() for c in core)


def _has_code_extension(token: str) -> bool:
    return token.lower().endswith(tuple(CODE_EXTENSIONS))


def extract_anchors(text: str) -> List[Anchor]:
    """
    Extract file and symbol anchors from a block of plan text.

    File anchors come from any token ending in a known code/doc extension
    (inside backticks or bare in prose). Symbol anchors come only from
    inline-code spans and must pass the _looks_like_code heuristic. Results
    are de-duplicated by (kind, query) and capped.
    """
    anchors: List[Anchor] = []
    seen = set()

    def add(kind: str, raw: str, query: str) -> None:
        key = (kind, query)
        if query and key not in seen:
            seen.add(key)
            anchors.append(Anchor(kind=kind, raw=raw, query=query))

    # 1. Inline-code spans → files and symbols.
    for span in _INLINE_CODE_RE.findall(text):
        tok = span.strip()
        if not tok or " " in tok:
            continue  # commands / phrases in backticks are not anchors.
        if _has_code_extension(tok):
            add("file", tok, tok.strip("/"))
        elif _SYMBOL_RE.match(tok) and _looks_like_code(tok):
            add("symbol", tok, tok.rstrip("()"))

    # 2. Bare path-like tokens in prose/tables → file anchors only.
    for m in _BARE_FILE_RE.findall(text):
        tok = m.strip()
        if _has_code_extension(tok):
            add("file", tok, tok)

    return anchors[:_MAX_ANCHORS_PER_ITEM]


def parse(plan_text: str) -> List[PlanItem]:
    """
    Parse plan markdown into a list of PlanItem objects.

    Each `##`/`###`/`####` header starts a new item; the item's body runs to
    the next header. Headers inside fenced code blocks are ignored, but fenced
    content still contributes anchors (verification snippets reference real
    files/symbols). Text before the first header is not treated as an item.
    """
    lines = plan_text.splitlines()
    # Identify header line indices (outside fences).
    headers: List[Tuple[int, int, str]] = []  # (line_idx, level, title)
    in_fence = False
    for idx, line in enumerate(lines):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _HEADER_RE.match(line)
        if m:
            headers.append((idx, len(m.group(1)), m.group(2).strip()))

    items: List[PlanItem] = []
    for i, (line_idx, level, title) in enumerate(headers):
        end = headers[i + 1][0] if i + 1 < len(headers) else len(lines)
        body = "\n".join(lines[line_idx:end])
        items.append(
            PlanItem(
                item_id=i + 1,
                title=title,
                level=level,
                source_line=line_idx + 1,  # 1-based for human/citation use.
                anchors=extract_anchors(body),
            )
        )
    return items


def count_checkboxes(plan_text: str) -> dict:
    """
    Count task-checkbox states across the plan.

    Returns {"open": n, "done": n, "in_progress": n}. Orphaned `open` /
    `in_progress` tasks are a /triage signal that a build is incomplete.
    """
    counts = {"open": 0, "done": 0, "in_progress": 0}
    for line in plan_text.splitlines():
        m = _CHECKBOX_RE.match(line)
        if not m:
            continue
        mark = m.group(1).lower()
        if mark == " ":
            counts["open"] += 1
        elif mark == "x":
            counts["done"] += 1
        else:  # "/" or "~"
            counts["in_progress"] += 1
    return counts


def load_and_parse(plan_path: Path) -> Tuple[List[PlanItem], dict]:
    """Read a plan file (bounded) and return (items, checkbox_counts)."""
    text = safe_read(plan_path, max_bytes=5 * 1024 * 1024)
    return parse(text), count_checkboxes(text)
