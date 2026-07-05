#!/usr/bin/env python3
"""
seeder.py — Sovereign Suite Gitignore Seeder CLI
================================================
Writes a non-destructive, idempotent **managed block** into a target workspace's
`.gitignore`, preloaded from an editable `seed.toml`, and warns when secret/
credential files are ALREADY tracked (recommending /gitclean for those).

Design contracts:
  * Non-destructive (/nodelete applied to .gitignore): the user's existing entries
    are never touched. Only content BETWEEN the managed-block markers is rewritten.
  * Idempotent: identical config → byte-identical file across runs (no duplicate
    block, no timestamp drift inside the block).
  * Detect-and-warn, never auto-scrub: gitignore prevents *future* leaks only. An
    already-committed secret needs history rewrite — that is /gitclean's job, not
    this seeder's. The seeder must not imply "you're protected now."
  * Path-contained: refuses dangerous targets (filesystem root, $HOME root,
    non-existent paths) and writes only inside the resolved workspace.

Usage:
    python seeder.py --workspace /abs/path [--config /abs/seed.toml]
                     [--report-only] [--output-json] [--quiet]

Hook: invoked by the /sentinel flow alongside doorway.py against the flagged
--workspace, so every workspace the suite operates on receives correct,
security-aware ignore coverage automatically.

Origin: helpdesk ticket 20260612_gitignore-seeder_module.md.
"""

import argparse
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from gitignore import __version__
from gitignore._utils import assert_within, atomic_write
from engine_utils import safe_read
from gitignore.config import (
    BLOCK_END,
    BLOCK_START,
    count_patterns,
    load_seed,
    render_block,
    security_patterns,
)
from gitignore.matcher import find_tracked_secrets
from gitignore.reporter import SeederReporter

SCHEMA_VERSION = "1.0"
GITIGNORE_NAME = ".gitignore"
_ADVISORY = (
    "A .gitignore prevents FUTURE commits of matching files. It does NOT remove "
    "anything already in git history. For secrets that are already tracked, run "
    "/gitclean (Mode A) to scrub them from history — this seeder never rewrites history."
)


def assert_safe_target(workspace: Path) -> None:
    """
    Refuse dangerous write targets (CWE-22 / blast-radius containment). Raises
    ValueError for: a path that is not an existing directory, the filesystem root,
    or the user's home-directory root. The seeder must only ever seed a real,
    bounded project workspace.
    """
    ws = Path(workspace).resolve()
    if not ws.is_dir():
        raise ValueError(f"[REFUSED] Not an existing directory: {ws}")
    if ws == Path(ws.anchor):
        raise ValueError(f"[REFUSED] Refusing to seed the filesystem root: {ws}")
    try:
        home = Path.home().resolve()
        if ws == home:
            raise ValueError(f"[REFUSED] Refusing to seed the home-directory root: {ws}")
    except (RuntimeError, OSError):
        pass  # Home not resolvable — the root/dir guards above still apply.


def tracked_files(workspace: Path):
    """
    Return the list of git-tracked paths in *workspace* via `git ls-files -z`, or
    None if the workspace is not a git repo / git is unavailable. None is distinct
    from [] (a git repo with zero tracked files). NUL-separation (-z) is robust to
    spaces/newlines in filenames. subprocess uses a list (no shell) — no CWE-78.
    """
    try:
        proc = subprocess.run(
            ["git", "-C", str(workspace), "ls-files", "-z"],
            capture_output=True, text=True, timeout=30, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return [p for p in proc.stdout.split("\0") if p]


class GitignoreSeeder:
    """
    Seeds/refreshes the managed block in {workspace}/.gitignore and runs the
    already-tracked-secret detect-and-warn pass.

    Args:
        workspace:   Resolved absolute Path to the target workspace root.
        config_path: Optional path to an alternative seed.toml (defaults to bundled).
        apply:       When False (--report-only), compute everything but write nothing.
    """

    def __init__(self, workspace, config_path=None, apply=True):
        self.workspace = Path(workspace).resolve()
        assert_safe_target(self.workspace)
        self.gitignore_path = self.workspace / GITIGNORE_NAME
        assert_within(self.gitignore_path, self.workspace)
        self.config = load_seed(config_path)
        self.apply = apply

    def run(self) -> dict:
        existing = safe_read(self.gitignore_path) if self.gitignore_path.exists() else ""
        block = render_block(self.config)
        new_content = self._splice_block(existing, block)

        had_block = BLOCK_START in existing and BLOCK_END in existing
        file_existed = self.gitignore_path.exists()
        changed = new_content != existing

        if not file_existed:
            block_action = "created"
        elif not had_block:
            block_action = "block-appended"
        elif changed:
            block_action = "block-updated"
        else:
            block_action = "unchanged"

        # Detect-and-warn: intersect security patterns with already-tracked files.
        tracked = tracked_files(self.workspace)
        secrets = find_tracked_secrets(tracked, security_patterns(self.config)) \
            if tracked is not None else []

        wrote = False
        if self.apply and changed:
            self._write(new_content)
            wrote = True

        return {
            "schema_version": SCHEMA_VERSION,
            "tool": "gitignore-seeder",
            "tool_version": __version__,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "workspace": str(self.workspace),
            "gitignore_path": str(self.gitignore_path),
            "file_existed": file_existed,
            "block_action": block_action,
            "changed": changed,
            "wrote": wrote,
            "managed_patterns": count_patterns(self.config),
            "git_repo": tracked is not None,
            "tracked_secrets": secrets,
            "summary": {"advisory": _ADVISORY},
        }

    # --- managed-block splicing ----------------------------------------

    @staticmethod
    def _splice_block(existing: str, block: str) -> str:
        """
        Replace the existing managed block in *existing* with *block* in place; if no
        block is present, append it (preserving every existing user entry). Idempotent:
        feeding back an already-correct file returns it byte-for-byte unchanged.
        """
        start = existing.find(BLOCK_START)
        end = existing.find(BLOCK_END)
        if start != -1 and end != -1 and end >= start:
            end_full = end + len(BLOCK_END)
            return existing[:start] + block + existing[end_full:]
        if existing and not existing.endswith("\n"):
            existing += "\n"
        sep = "\n" if existing else ""
        return existing + sep + block + "\n"

    def _write(self, content: str) -> None:
        # Preserve an existing file's permission bits; default 0o644 for a new file.
        mode = 0o644
        if self.gitignore_path.exists():
            mode = stat.S_IMODE(self.gitignore_path.stat().st_mode)
        atomic_write(self.gitignore_path, content, mode=mode)


def _parse_args():
    p = argparse.ArgumentParser(
        prog="seeder.py",
        description="Sovereign Suite Gitignore Seeder — writes a non-destructive, "
                    "idempotent managed block into a workspace's .gitignore and "
                    "warns on already-tracked secrets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  python seeder.py --workspace /home/user/project\n"
               "  python seeder.py --workspace /home/user/project --report-only --output-json\n",
    )
    p.add_argument("--workspace", required=True, type=str,
                   help="Absolute path to the target workspace root.")
    p.add_argument("--config", type=str, default=None,
                   help="Alternative seed.toml path (defaults to the bundled config).")
    p.add_argument("--report-only", action="store_true",
                   help="Compute the block + secret scan but write nothing.")
    p.add_argument("--output-json", action="store_true", help="Emit JSON to stdout.")
    p.add_argument("--quiet", action="store_true", help="Suppress human-readable output.")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        seeder = GitignoreSeeder(args.workspace, config_path=args.config,
                                 apply=not args.report_only)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2  # Refused / unsafe target.
    report = seeder.run()
    SeederReporter().render(report, quiet=args.quiet, output_json=args.output_json)
    # Exit 0 even when tracked secrets are found: the warning is advisory and the
    # seeding itself succeeded. /sentinel surfaces the warning to the operator.
    return 0


if __name__ == "__main__":
    sys.exit(main())
