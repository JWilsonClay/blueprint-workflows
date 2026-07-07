"""
config.py — Seed config loading + managed-block rendering
=========================================================
Loads the editable `seed.toml` (the tunable surface) and renders the deterministic
managed block. The block is intentionally TIMESTAMP-FREE: identical config must
produce byte-identical output so re-runs are idempotent.

A hardcoded DEFAULT_SEED mirrors `seed.toml` so the seeder still functions if the
config file is missing or `tomllib` is unavailable (Python < 3.11) — it degrades
to the suite defaults rather than failing.
"""

from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    tomllib = None

# Markers. The seeder ONLY ever rewrites content between these two lines.
BLOCK_START = "# >>> Sovereign Suite — managed block (auto-generated; edit above/below, not inside) >>>"
BLOCK_END = "# <<< Sovereign Suite — managed block <<<"
_BLOCK_NOTE = "# (managed by scripts/gitignore — re-run /sentinel to refresh; never edit between the markers)"

_DEFAULT_SEED_PATH = Path(__file__).resolve().parent / "seed.toml"

# Safety net: mirrors seed.toml. Used only if the toml file/parser is unavailable.
DEFAULT_SEED = {
    "categories": {
        "suite": {
            "title": "Suite-generated / ingestion-banned (never tracked)",
            # [CORRECTED 2026-07-07, mirrors seed.toml] .history/ narrowed to
            # .history/quarantine/ -- see seed.toml's comment for the rationale.
            "patterns": [".history/quarantine/", "quarantine/", ".workflow_state/",
                         "deprecated/", ".doorway/"],
        },
        "security": {
            "title": "Security — secrets & credentials (NEVER commit)",
            "scan_secrets": True,
            "patterns": [".env", ".env.*", "secrets/", "*.key", "*.pem",
                         "id_rsa*", "*.p12", "*.pfx", "credentials*.json",
                         "service-account*.json", ".aws/"],
        },
        "noise": {
            "title": "Common noise (build artifacts, caches, editor cruft)",
            "patterns": ["__pycache__/", "*.pyc", ".venv/", "node_modules/",
                         "dist/", "build/", ".DS_Store", "*.log", ".idea/",
                         ".vscode/"],
        },
    }
}


def load_seed(path: Path = None) -> dict:
    """
    Load the seed config from *path* (default: the bundled seed.toml). Falls back to
    DEFAULT_SEED if the file is absent or tomllib is unavailable. Never raises on a
    missing config — only on a genuinely malformed toml the user must fix.
    """
    path = Path(path) if path else _DEFAULT_SEED_PATH
    if tomllib is None or not path.exists():
        return DEFAULT_SEED
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    return data if data.get("categories") else DEFAULT_SEED


def iter_categories(config: dict):
    """Yield (key, title, scan_secrets, patterns) in config (insertion) order."""
    for key, cat in (config.get("categories") or {}).items():
        patterns = [p for p in (cat.get("patterns") or []) if p and str(p).strip()]
        yield key, cat.get("title", key), bool(cat.get("scan_secrets")), patterns


def security_patterns(config: dict) -> list:
    """All patterns from categories flagged `scan_secrets = true` (the warn set)."""
    out = []
    for _key, _title, scan, patterns in iter_categories(config):
        if scan:
            out.extend(patterns)
    return out


def render_block(config: dict) -> str:
    """
    Render the managed block as a deterministic string starting with BLOCK_START
    and ending with BLOCK_END, with NO surrounding newlines (the splicer in
    seeder.py supplies those). Timestamp-free → byte-identical across runs.
    """
    lines = [BLOCK_START, _BLOCK_NOTE]
    for _key, title, _scan, patterns in iter_categories(config):
        if not patterns:
            continue
        lines.append(f"# --- {title} ---")
        lines.extend(patterns)
    lines.append(BLOCK_END)
    return "\n".join(lines)


def count_patterns(config: dict) -> int:
    """Total number of ignore patterns across all categories."""
    return sum(len(patterns) for *_x, patterns in iter_categories(config))
