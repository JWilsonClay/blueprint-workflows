"""
cwe_scanner.py — Deterministic CWE Signature Scanner (read-only)
=================================================================
Detects the security findings in the /harden Phase-2c checklist that have exact,
machine-checkable signatures — the deterministic half of the audit. It opens
files for reading and writes nothing.

What it detects (and explicitly what it does NOT):

  DETECTS (deterministic, regex-exact): dynamic code-evaluation builtins; the
  shell-True subprocess keyword; command-shell execution calls; hardcoded
  credential CANDIDATES; unsafe deserialization; disabled TLS verification; weak
  hashing; world-writable permission bits; insecure temp-file creation; weak RNG.

  DOES NOT detect (irreducible judgment, owned by the /harden agent): whether a
  finding is exploitable in context; whether a control is actually REACHED on the
  execution path (Sound Effect Execution); whether input validation is
  *sufficient*; the worst-case impact. The scanner reports mechanical presence;
  the agent reasons about meaning.

Every finding carries a CWE id and a severity tier (CRITICAL / HIGH / MEDIUM /
LOW). Severities feed grade_computer, which turns them into a grade CEILING. A
finding flagged ``requires_confirmation`` (e.g., a credential candidate) is a
one-directional signal: the agent must confirm it before it counts — its absence
proves nothing.

Self-scan note: every pattern targets *real call syntax*; the escaped regex
source here does not match itself, and this module legitimately scans its own
package during a workspace run. Curate, never special-case.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional

from harden._utils import safe_read

CRITICAL = "CRITICAL"
HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"

_MAX_FINDINGS_PER_FILE = 200

_PY = (".py",)
_BASH = (".sh", ".bash")
_JSTS = (".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx")


class _Sig:
    """One deterministic signature: a compiled pattern plus its metadata."""

    __slots__ = ("id", "category", "cwe", "severity", "exts", "note",
                 "advisory", "requires_confirmation", "pattern")

    def __init__(self, id, category, cwe, severity, pattern, exts=None,
                 note="", advisory=False, requires_confirmation=False):
        self.id = id
        self.category = category
        self.cwe = cwe
        self.severity = severity
        self.exts = exts            # None = applies to any script extension
        self.note = note
        self.advisory = advisory
        self.requires_confirmation = requires_confirmation
        self.pattern = re.compile(pattern)


# ---------------------------------------------------------------------------
# Signature table. Patterns target real call syntax; the lookbehind on the
# Python ones avoids matching a same-named method/attribute on another object.
# ---------------------------------------------------------------------------
_SIGNATURES: List[_Sig] = [
    # --- High-confidence CRITICAL (unambiguous; hard-blocks the grade) -------
    _Sig("dynamic-exec", "Injection & Command Execution", "CWE-95", CRITICAL,
         r"(?<![\w.])(?:eval|exec)\s*\(", exts=_PY,
         note="Dynamic code evaluation of a runtime value enables arbitrary code execution."),
    _Sig("subprocess-shell-true", "Injection & Command Execution", "CWE-78", CRITICAL,
         r"shell\s*=\s*True\b", exts=None,
         note="A subprocess invoked through the system shell is a command-injection surface. "
              "STRICT RULE 8 mandates flagging this CRITICAL regardless of context."),
    _Sig("tls-verify-disabled", "Network & External Calls", "CWE-295", CRITICAL,
         r"verify\s*=\s*False\b", exts=None,
         note="TLS certificate verification disabled. STRICT RULE 7 is an absolute prohibition."),
    _Sig("tls-unverified-context", "Network & External Calls", "CWE-295", CRITICAL,
         r"_create_unverified_context\s*\(", exts=_PY,
         note="Explicitly unverified TLS context. STRICT RULE 7 is an absolute prohibition."),
    _Sig("tls-check-hostname-off", "Network & External Calls", "CWE-295", CRITICAL,
         r"check_hostname\s*=\s*False\b", exts=_PY,
         note="Hostname verification disabled on a TLS context."),
    _Sig("tls-cert-none", "Network & External Calls", "CWE-295", CRITICAL,
         r"(?<![\w.])ssl\.CERT_NONE\b", exts=_PY,
         note="TLS peer-certificate requirement set to none."),

    # --- Medium-confidence HIGH (caps at Silver; some need confirmation) -----
    _Sig("os-system", "Injection & Command Execution", "CWE-78", HIGH,
         r"(?<![\w.])os\.system\s*\(", exts=_PY,
         note="Command-shell execution; prefer subprocess with an argument list and no shell."),
    _Sig("subprocess-exec-shell", "Injection & Command Execution", "CWE-78", HIGH,
         r"(?<![\w.])os\.(?:popen|exec[lv]p?e?)\s*\(", exts=_PY,
         note="Process/command execution via os.* — validate every interpolated argument."),
    _Sig("pickle-load", "Serialization / Deserialization", "CWE-502", HIGH,
         r"(?<![\w.])(?:cPickle|pickle)\.(?:load|loads)\s*\(", exts=_PY,
         note="Deserializing untrusted data with pickle permits arbitrary code execution."),
    _Sig("yaml-unsafe-load", "Serialization / Deserialization", "CWE-502", HIGH,
         r"(?<![\w.])yaml\.load\s*\(", exts=_PY,
         note="yaml.load without a safe loader can construct arbitrary objects; "
              "use safe_load / SafeLoader. (Skipped when the call names a safe Loader.)"),
    _Sig("world-writable-chmod", "Umask & File Creation Permissions", "CWE-732", HIGH,
         r"chmod\s*\([^)]*0o?777", exts=_PY,
         note="World-writable file permissions (0777)."),
    _Sig("world-writable-chmod-sh", "Umask & File Creation Permissions", "CWE-732", HIGH,
         r"chmod\s+(?:-R\s+)?0?777\b", exts=_BASH,
         note="World-writable file permissions (chmod 777)."),
    _Sig("curl-pipe-shell", "Injection & Command Execution", "CWE-78", HIGH,
         r"(?:curl|wget)\b[^|\n]*\|\s*(?:sudo\s+)?(?:ba)?sh\b", exts=_BASH,
         note="Piping a network download straight into a shell executes unverified remote code."),
    _Sig("js-dynamic-exec", "Injection & Command Execution", "CWE-95", HIGH,
         r"(?<![\w.])eval\s*\(", exts=_JSTS,
         note="Dynamic code evaluation of a runtime value."),
    _Sig("js-child-exec", "Injection & Command Execution", "CWE-78", HIGH,
         r"child_process\.exec\s*\(", exts=_JSTS,
         note="child_process.exec runs through a shell; prefer execFile with an argument list."),

    # --- Advisory MEDIUM / LOW (caps at Gold / does not affect ceiling) ------
    _Sig("weak-hash", "Cryptography Usage", "CWE-327", MEDIUM,
         r"(?<![\w.])hashlib\.(?:md5|sha1)\s*\(", exts=_PY, advisory=True,
         note="Weak hash for security use. Acceptable for non-security checksums — adjudicate."),
    _Sig("insecure-tempfile", "Path Traversal & File System Safety", "CWE-377", MEDIUM,
         r"(?<![\w.])tempfile\.mktemp\s*\(", exts=_PY, advisory=True,
         note="mktemp is race-prone (TOCTOU); prefer mkstemp / NamedTemporaryFile."),
    _Sig("weak-random", "Cryptography Usage", "CWE-330", LOW, exts=_PY, advisory=True,
         pattern=r"(?<![\w.])random\.(?:random|randint|choice|randrange)\s*\(",
         note="Standard PRNG is not cryptographically secure. Fine for non-security use; "
              "use secrets/SystemRandom for tokens, keys, nonces."),
]

# Credential key names (case-insensitive) for the hardcoded-secret heuristic —
# the same vocabulary as the workflow's Phase-0 credential scan.
_SECRET_KEY_RE = re.compile(
    r"(?i)\b(password|passwd|secret|api[_-]?key|apikey|token|"
    r"private[_-]?key|access[_-]?key|client[_-]?secret|auth[_-]?token)\b"
    r"\s*[:=]\s*(?P<q>[\"'])(?P<val>[^\"'\n]{4,})(?P=q)"
)

# Right-hand sides that are NOT real secrets (placeholders / safe sources).
_PLACEHOLDER_MARKERS = (
    "os.environ", "os.getenv", "getenv", "environ[", "process.env", "config[",
    "none", "null", "nil", "true", "false", "example", "changeme", "change_me",
    "your", "xxx", "todo", "fixme", "placeholder", "dummy", "sample", "test",
    "redacted", "removed", "<", "${", "{{", "%s", "{}", "...", "f'", 'f"',
)


def _looks_like_real_secret(value: str) -> bool:
    """
    Heuristic gate for the hardcoded-credential check. ONE-DIRECTIONAL: a True is
    a *candidate* the agent must confirm; a False is a safe skip (placeholder,
    env lookup, format string, or too short).
    """
    v = value.strip()
    if len(v) < 6:
        return False
    low = v.lower()
    if any(marker in low for marker in _PLACEHOLDER_MARKERS):
        return False
    has_alpha = any(c.isalpha() for c in v)
    has_nonalpha = any(not c.isalpha() for c in v)
    return (has_alpha and has_nonalpha) or len(v) >= 16


def _line_of(text: str, idx: int) -> int:
    return text.count("\n", 0, max(idx, 0)) + 1


def _excerpt(text: str, idx: int) -> str:
    start = text.rfind("\n", 0, idx) + 1
    end = text.find("\n", idx)
    if end == -1:
        end = len(text)
    return text[start:end].strip()[:160]


class CWEScanner:
    """Read-only deterministic CWE signature scanner."""

    def scan_text(self, relpath: str, text: str, ext: str) -> List[Dict]:
        """Return the findings for one already-read script file."""
        findings: List[Dict] = []
        ext = ext.lower()

        for sig in _SIGNATURES:
            if sig.exts is not None and ext not in sig.exts:
                continue
            for m in sig.pattern.finditer(text):
                line = _excerpt(text, m.start())
                # yaml safe-loader calls are not findings.
                if sig.id == "yaml-unsafe-load" and (
                    "SafeLoader" in line or "Loader=" in line or "safe_load" in line
                ):
                    continue
                findings.append({
                    "signature": sig.id,
                    "category": sig.category,
                    "cwe": sig.cwe,
                    "severity": sig.severity,
                    "line": _line_of(text, m.start()),
                    "excerpt": line,
                    "note": sig.note,
                    "advisory": sig.advisory,
                    "requires_confirmation": sig.requires_confirmation,
                })
                if len(findings) >= _MAX_FINDINGS_PER_FILE:
                    return findings

        findings.extend(self._scan_secrets(text))
        return findings[:_MAX_FINDINGS_PER_FILE]

    def _scan_secrets(self, text: str) -> List[Dict]:
        out: List[Dict] = []
        for m in _SECRET_KEY_RE.finditer(text):
            if not _looks_like_real_secret(m.group("val")):
                continue
            out.append({
                "signature": "hardcoded-secret",
                "category": "Secrets & Sensitive Data",
                "cwe": "CWE-798",
                "severity": HIGH,  # HIGH (caps at Silver), not CRITICAL: FP-prone
                                   # by nature. The agent confirms and may escalate.
                "line": _line_of(text, m.start()),
                "excerpt": _excerpt(text, m.start())[:80] + "  …(value redacted)",
                "note": "Hardcoded credential CANDIDATE. Confirm it is a real secret "
                        "(not a placeholder/example); if real, escalate to CRITICAL and "
                        "move to env/secret manager.",
                "advisory": False,
                "requires_confirmation": True,
            })
        return out

    def scan_file(self, path: Path, relpath: str) -> List[Dict]:
        """Read *path* (bounded) and scan it. Returns [] for unreadable files."""
        text = safe_read(Path(path))
        if not text:
            return []
        return self.scan_text(relpath, text, Path(path).suffix)


def first_line_of(text: str) -> str:
    """Return the first line of *text* (for shebang-based script detection)."""
    nl = text.find("\n")
    return text if nl == -1 else text[:nl]
