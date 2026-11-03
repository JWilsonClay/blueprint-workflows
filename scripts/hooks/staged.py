"""Index access for the staged Python gates. Reads git. Does not install hooks."""

import re
import subprocess
import sys
from pathlib import Path

from hooks import config as gate_config


class GitError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class UsageError(Exception):
    pass


class Hunk:
    def __init__(self, old_start, old_count, new_start, new_count, old_lines, new_lines):
        self.old_start = old_start
        self.old_count = old_count
        self.new_start = new_start
        self.new_count = new_count
        self.old_lines = old_lines
        self.new_lines = new_lines


class StagedPy:
    def __init__(self, path, added, blob, pre_image, hunks):
        self.path = path
        self.added = added
        self.blob = blob
        self.pre_image = pre_image
        self.hunks = hunks


class Prepared:
    def __init__(self, exit_code=None, files=None, cfg=None):
        self.exit_code = exit_code
        self.files = files if files is not None else []
        self.cfg = cfg


_HUNK_RE = re.compile(br"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def _run(args, cwd, text):
    return subprocess.run(
        args,
        cwd=None if cwd is None else str(cwd),
        capture_output=True,
        text=text,
        timeout=30,
        check=False,
    )


def _stderr(proc):
    data = proc.stderr
    if isinstance(data, str):
        return data.strip()
    return (data or b"").decode("utf-8", "replace").strip()


def _git(cwd, args, text):
    proc = _run(["git", "--no-pager", "-c", "color.ui=false", *args], cwd, text)
    if proc.returncode != 0:
        raise GitError(_stderr(proc) or "git command failed")
    return proc.stdout


def resolve_toplevel(workspace):
    proc = _run(["git", "--no-pager", "rev-parse", "--show-toplevel"], workspace, text=False)
    if proc.returncode != 0:
        raise GitError(_stderr(proc) or "not a git repository")
    return Path(proc.stdout.decode("utf-8", "replace").strip())


def _parse_args(argv):
    workspace = None
    staged = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--staged":
            staged = True
        elif arg == "--workspace":
            index += 1
            if index >= len(argv):
                raise UsageError()
            workspace = Path(argv[index])
        elif arg.startswith("--workspace="):
            workspace = Path(arg.split("=", 1)[1])
        else:
            raise UsageError()
        index += 1
    if not staged:
        raise UsageError()
    return workspace


def _parse_name_status(text):
    parts = text.split("\0")
    if parts and parts[-1] == "":
        parts.pop()
    records = []
    index = 0
    while index < len(parts):
        token = parts[index]
        if not token:
            index += 1
            continue
        if token[0] in {"R", "C"}:
            if index + 2 >= len(parts):
                raise GitError("truncated rename record")
            records.append((token, parts[index + 1], parts[index + 2]))
            index += 3
            continue
        if index + 1 >= len(parts):
            raise GitError("truncated name-status record")
        records.append((token, parts[index + 1], parts[index + 1]))
        index += 2
    return records


def _parse_patch(patch):
    hunks = []
    current = None
    old_line = 0
    new_line = 0
    for line in patch.splitlines():
        match = _HUNK_RE.match(line)
        if match is not None:
            old_start = int(match.group(1))
            old_count = int(match.group(2)) if match.group(2) is not None else 1
            new_start = int(match.group(3))
            new_count = int(match.group(4)) if match.group(4) is not None else 1
            current = Hunk(old_start, old_count, new_start, new_count, [], [])
            hunks.append(current)
            old_line = old_start
            new_line = new_start
            continue
        if current is None or line.startswith(b"\\"):
            continue
        if line.startswith(b"+"):
            current.new_lines.append(new_line)
            new_line += 1
        elif line.startswith(b"-"):
            current.old_lines.append(old_line)
            old_line += 1
        else:
            old_line += 1
            new_line += 1
    return hunks


def _has_hunk(patch):
    return any(line.startswith(b"@@") for line in patch.splitlines())


def _show(cwd, spec):
    return _git(cwd, ["show", spec], text=False)


def _cached_diff(cwd, paths):
    return _git(cwd, ["diff", "--cached", "-M", "-U0", "--", *paths], text=False)


def staged_python(toplevel):
    """Judged staged Python files. Pure renames are omitted."""
    text = _git(
        toplevel,
        ["diff", "--cached", "-M", "--name-status", "-z", "--diff-filter=ACMR"],
        text=True,
    )
    judged = []
    for token, old, new in _parse_name_status(text):
        if not new.endswith(".py"):
            continue
        letter = token[0]
        if letter == "R":
            patch = _cached_diff(toplevel, [old, new])
        else:
            patch = _cached_diff(toplevel, [new])
        has_hunk = _has_hunk(patch)
        # A copy is judged as an add. A pure rename (no @@ hunk) is not judged.
        if letter == "R" and not has_hunk:
            continue
        if letter not in {"A", "C", "R"} and not has_hunk:
            continue
        added = letter in {"A", "C"}
        blob = _show(toplevel, f":{new}")
        pre_image = None
        if not added:
            pre_spec = old if letter == "R" else new
            pre_image = _show(toplevel, f"HEAD:{pre_spec}")
        judged.append(StagedPy(new, added, blob, pre_image, _parse_patch(patch)))
    return judged


def prepare(argv=None):
    """Resolve the repo and config. Return a Prepared with exit_code set to stop."""
    if argv is None:
        argv = sys.argv[1:]
    try:
        workspace = _parse_args(argv)
    except UsageError:
        print("usage: --staged [--workspace PATH]", file=sys.stderr)
        return Prepared(exit_code=2)
    try:
        toplevel = resolve_toplevel(workspace)
        files = staged_python(toplevel)
    except GitError as exc:
        print(f"git failed: {exc.message}")
        return Prepared(exit_code=1)
    if not files:
        return Prepared(exit_code=0)
    try:
        cfg = gate_config.load(toplevel / ".githooks" / "suite-gates.cfg")
    except gate_config.ConfigError as exc:
        reason = " ".join(exc.message.split())
        print(f"suite-gates.cfg rejected: {reason}")
        return Prepared(exit_code=1)
    if cfg.missing_file:
        print(gate_config.missing_file_line())
    else:
        for key, value in cfg.missing_keys:
            print(gate_config.missing_key_line(key, value))
    return Prepared(files=files, cfg=cfg)
