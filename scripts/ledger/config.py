"""
config.py — Ledger config loading
===================================
Loads the editable `ledger_config.toml`. A hardcoded DEFAULT_CONFIG mirrors it
so the monitor still functions if the config file is missing or `tomllib` is
unavailable (Python < 3.11) — degrade to suite defaults, never fail.
"""

from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    tomllib = None

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "ledger_config.toml"

# Safety net: mirrors ledger_config.toml. Used only if the toml file/parser is unavailable.
DEFAULT_CONFIG = {
    "ledgers": [
        {
            "name": "workflow_manifest_narrative",
            "mode": "shard",
            "active_dir": "manifest/history",
            "shard_name_pattern": "WORKFLOW_MANIFEST_{quarter}.md",
            "entry_pattern": r"^## \*\*\[",
            "warn_threshold_entries": 15,
            "warn_threshold_bytes": 30000,
        },
        {
            "name": "suite_phylogeny",
            "mode": "warn",
            "path": "manifest/SUITE_PHYLOGENY.md",
            "entry_pattern": r"^## Lineage Entry",
            "warn_threshold_entries": 15,
            "warn_threshold_bytes": 30000,
        },
    ]
}


def load_config(path: Path = None) -> dict:
    """
    Load the ledger config from *path* (default: the bundled ledger_config.toml).
    Falls back to DEFAULT_CONFIG if the file is absent or tomllib is unavailable.
    """
    path = Path(path) if path else _DEFAULT_CONFIG_PATH
    if tomllib is None or not path.exists():
        return DEFAULT_CONFIG
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    return data if data.get("ledgers") else DEFAULT_CONFIG


def iter_ledgers(config: dict):
    """Yield each ledger's config dict, in declared order."""
    for ledger in config.get("ledgers") or []:
        if ledger.get("name") and ledger.get("mode"):
            yield ledger
