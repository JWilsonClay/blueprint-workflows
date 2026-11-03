#!/usr/bin/env python3
"""Install the length and complexity pre-commit gates. One installer."""

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from engine_utils import atomic_write
from hooks import hook_text
from hooks.config import (
    AIM,
    COGNITIVE,
    MAX_ARGS,
    MAINTAIN,
    REJECT,
    ConfigError,
    load as load_config,
)


SUITE_ROOT = Path(__file__).resolve().parents[2]

# git 2.34.1 names from `git help hooks`. Any other file in .git/hooks is not a hook.
_HOOK_NAMES = frozenset({
    "applypatch-msg",
    "pre-applypatch",
    "post-applypatch",
    "pre-commit",
    "pre-merge-commit",
    "prepare-commit-msg",
    "commit-msg",
    "post-commit",
    "pre-rebase",
    "post-checkout",
    "post-merge",
    "pre-push",
    "pre-receive",
    "update",
    "proc-receive",
    "post-receive",
    "post-update",
    "reference-transaction",
    "push-to-checkout",
    "pre-auto-gc",
    "post-rewrite",
    "sendemail-validate",
    "fsmonitor-watchman",
    "p4-changelist",
    "p4-prepare-changelist",
    "p4-post-changelist",
    "p4-pre-submit",
    "post-index-change",
})

_REPORT_KEYS = (
    "loc_action",
    "complexity_action",
    "config_action",
    "hooks_path_action",
    "chain",
    "wrote",
    "length_runs",
    "loc_reject",
    "loc_maintain",
    "loc_aim",
    "cognitive",
    "max_args",
    "ceilings_source",
)

_CHAIN = {
    "create": "created",
    "create-and-set": "created",
    "wrap": "wrapped",
    "rewrap-and-set": "wrapped",
    "splice": "spliced",
    "splice-and-set": "spliced",
    "trampoline": "trampoline",
    "activate": "none",
    "noop": "none",
    "leave": "none",
    "refuse": "none",
}

_WRITES_SECTIONS = frozenset({
    "create",
    "create-and-set",
    "wrap",
    "rewrap-and-set",
    "splice",
    "splice-and-set",
    "trampoline",
})

_SETS_HOOKS = frozenset({
    "create-and-set",
    "rewrap-and-set",
    "splice-and-set",
    "activate",
})


class UsageError(Exception):
    pass


def _git(workspace, *args):
    return subprocess.run(
        ["git", "--no-pager", "-c", "color.ui=false", "-C", str(workspace), *args],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _read(path):
    return Path(path).read_bytes().decode("utf-8", "surrogateescape")


def _executable(path):
    return os.access(path, os.X_OK)


def _is_inside(child, parent):
    try:
        Path(child).resolve().relative_to(Path(parent).resolve())
    except ValueError:
        return False
    return True


def _resolve_repo_path(workspace, raw):
    path = Path(raw)
    if not path.is_absolute():
        path = workspace / path
    return path.resolve()


def _create_config_excl(path, body):
    """Create the config only if it is absent. O_EXCL, never a replace."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(str(path), flags, 0o644)
    try:
        data = memoryview(body.encode("utf-8"))
        while data:
            wrote = os.write(fd, data)
            data = data[wrote:]
    except Exception:
        os.close(fd)
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    os.close(fd)


def _validate(workspace):
    ws = Path(workspace).resolve()
    if not ws.is_dir():
        raise UsageError(f"not an existing directory: {ws}")
    if ws == Path(ws.anchor):
        raise UsageError(f"refusing filesystem root: {ws}")
    try:
        home = Path.home().resolve()
    except (RuntimeError, OSError):
        home = None
    if home is not None and ws == home:
        raise UsageError(f"refusing home root: {ws}")
    top = _git(ws, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        raise UsageError("not a git repository")
    if Path(top.stdout.strip()).resolve() != ws:
        raise UsageError("not the git toplevel")
    git_dir = _git(ws, "rev-parse", "--git-dir")
    if git_dir.returncode != 0:
        raise UsageError("not a git repository")
    raw = git_dir.stdout.strip()
    resolved = Path(raw)
    if not resolved.is_absolute():
        resolved = (ws / resolved).resolve()
    else:
        resolved = resolved.resolve()
    if resolved != (ws / ".git").resolve() or not (ws / ".git").is_dir():
        raise UsageError("not a normal repository")
    bare = _git(ws, "rev-parse", "--is-bare-repository")
    if bare.stdout.strip() == "true":
        raise UsageError("not a normal repository")
    return ws


def _hooks_path_value(workspace):
    proc = _git(workspace, "config", "--show-origin", "--get", "core.hooksPath")
    if proc.returncode != 0:
        return None
    lines = proc.stdout.splitlines()
    if not lines:
        return None
    line = lines[0]
    if "\t" in line:
        return line.split("\t", 1)[1].strip()
    return line.strip() or None


def _real_hooks(hooks_dir):
    if not hooks_dir.is_dir():
        return []
    found = []
    for entry in hooks_dir.iterdir():
        if entry.name.endswith(".sample") or entry.name not in _HOOK_NAMES:
            continue
        if not entry.is_file():
            continue
        try:
            size = entry.stat().st_size
        except OSError:
            continue
        if size == 0:
            continue
        found.append(entry)
    return found


def _length_signal(blob):
    return (
        "LOC-EXEMPT" in blob
        or "suite-hook:loc-gate" in blob
        or "suite-hook:loc-existing" in blob
    )


def _real_length(blob):
    return "LOC-EXEMPT" in blob or "suite-hook:loc-gate" in blob


def _complexity_signal(blob):
    return "suite-hook:complexity-gate" in blob


def _inspect(workspace):
    hooks_raw = _hooks_path_value(workspace)
    hooks_resolved = _resolve_repo_path(workspace, hooks_raw) if hooks_raw else None
    proc = _git(workspace, "rev-parse", "--git-path", "hooks")
    if proc.returncode != 0:
        raise UsageError(proc.stderr.strip() or "git rev-parse --git-path hooks failed")
    effective = _resolve_repo_path(workspace, proc.stdout.strip())
    git_hooks = (workspace / ".git" / "hooks").resolve()
    candidates = []
    effective_pre = effective / "pre-commit"
    if effective_pre.is_file() and not effective_pre.name.endswith(".sample"):
        candidates.append(effective_pre.resolve())
    githooks_pre = workspace / ".githooks" / "pre-commit"
    if githooks_pre.is_file():
        candidates.append(githooks_pre.resolve())
    dotgit_pre = git_hooks / "pre-commit"
    dotgit_real = None
    if dotgit_pre.is_file() and not dotgit_pre.name.endswith(".sample"):
        dotgit_real = dotgit_pre.resolve()
        candidates.append(dotgit_real)
    detected = []
    seen = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        detected.append(path)
        sibling = path.parent / "pre-commit.suite-preserved"
        if sibling.is_file() and sibling.resolve() not in seen:
            seen.add(sibling.resolve())
            detected.append(sibling.resolve())
    texts = {path: _read(path) for path in detected}
    active = effective_pre.resolve() if effective_pre.is_file() and not effective_pre.name.endswith(".sample") else None
    return {
        "hooks_resolved": hooks_resolved,
        "hooks_set": hooks_raw is not None,
        "effective": effective,
        "git_hooks": git_hooks,
        "real": _real_hooks(git_hooks),
        "githooks_pre": githooks_pre.resolve() if githooks_pre.is_file() else None,
        "dotgit_pre": dotgit_real,
        "active": active,
        "texts": texts,
    }


def _executed_blob(workspace, active, texts):
    if active is None or not Path(active).is_file():
        return ""
    active = Path(active).resolve()
    text = texts.get(active)
    if text is None:
        text = _read(active)
    parts = [text]
    if "suite-hook:chain" not in text:
        return text
    preserved = active.parent / "pre-commit.suite-preserved"
    if preserved.is_file() and "pre-commit.suite-preserved" in text:
        parts.append(texts.get(preserved.resolve(), _read(preserved)))
    dormant = (workspace / ".githooks" / "pre-commit").resolve()
    # shell_quote splits an embedded quote, so the raw path is not always contiguous.
    if dormant.is_file() and dormant != active and (
        str(dormant) in text or hook_text.shell_quote(str(dormant)) in text
    ):
        parts.append(texts.get(dormant, _read(dormant)))
    return "\n".join(parts)


def _running_hook(ctx):
    if ctx["hooks_set"]:
        return ctx["active"]
    return ctx["dotgit_pre"]


def _base_flags(ctx):
    blob = "\n".join(ctx["texts"].values())
    length_known = _length_signal(blob)
    complexity_known = _complexity_signal(blob)
    return {
        "length_known": length_known,
        "complexity_known": complexity_known,
        "install_length": not length_known,
        "install_complexity": not complexity_known,
        "hooks_refused": False,
        "reason": "",
        "path": None,
        "trampoline": None,
        "blocks": None,
    }


def _refuse(base, reason, *, hooks=False, path=None):
    plan = dict(base)
    plan.update({
        "op": "refuse",
        "reason": reason,
        "hooks_refused": hooks,
        "path": path,
        "install_length": False,
        "install_complexity": False,
    })
    return plan


def _noop_or_leave(workspace, ctx, base, path):
    executed = _executed_blob(workspace, path, ctx["texts"])
    plan = dict(base)
    plan["path"] = path
    plan["install_length"] = False
    plan["install_complexity"] = False
    if _real_length(executed) and _complexity_signal(executed):
        plan["op"] = "noop"
    else:
        plan["op"] = "leave"
    return plan


def _splice_plan(workspace, ctx, base, path, text):
    if not base["install_length"] and not base["install_complexity"]:
        return _noop_or_leave(workspace, ctx, base, path)
    blocks = []
    if base["install_length"]:
        blocks.append(hook_text.loc_block())
    if base["install_complexity"]:
        blocks.append(hook_text.complexity_block())
    if hook_text.splice(text, blocks) is None:
        return _refuse(base, "no exit line to splice before", path=path)
    plan = dict(base)
    plan.update({"op": "splice", "path": path, "blocks": blocks})
    return plan


def _usable_or_refuse(base, path, text):
    if not _executable(path):
        return _refuse(base, "pre-commit is not executable", path=path), text
    preserved = Path(path).parent / "pre-commit.suite-preserved"
    if preserved.exists() and "suite-hook:chain" not in text:
        return (
            _refuse(
                base,
                "preserved hook exists and the live hook is not a chain",
                path=path,
            ),
            text,
        )
    return None, text


def _existing_plan(workspace, ctx, base, path):
    text = ctx["texts"].get(path, _read(path))
    refusal, text = _usable_or_refuse(base, path, text)
    if refusal is not None:
        return refusal
    if "suite-hook:chain" in text:
        return _splice_plan(workspace, ctx, base, path, text)
    if not base["install_length"] and not base["install_complexity"]:
        return _noop_or_leave(workspace, ctx, base, path)
    plan = dict(base)
    plan.update({"op": "wrap", "path": path})
    return plan


def _dormant_plan(workspace, ctx, base):
    path = ctx["githooks_pre"]
    text = ctx["texts"].get(path, _read(path))
    refusal, text = _usable_or_refuse(base, path, text)
    if refusal is not None:
        return refusal
    if _length_signal(text) and _complexity_signal(text):
        plan = dict(base)
        plan.update({
            "op": "activate",
            "path": path,
            "install_length": False,
            "install_complexity": False,
        })
        return plan
    if "suite-hook:chain" in text:
        plan = _splice_plan(workspace, ctx, base, path, text)
        if plan["op"] == "noop":
            plan["op"] = "activate"
        elif plan["op"] == "splice":
            plan["op"] = "splice-and-set"
        return plan
    plan = dict(base)
    plan.update({"op": "rewrap-and-set", "path": path})
    return plan


def _decide(workspace, ctx):
    """Case table, first match. The default .git/hooks print is not case 4."""
    base = _base_flags(ctx)
    if not _is_inside(ctx["effective"], workspace):
        return _refuse(base, "hooks directory is outside the workspace", hooks=True)
    hooks_set = ctx["hooks_set"]
    # Unset hooksPath still prints .git/hooks. That is not a hook and not case 4.
    if not hooks_set and not ctx["real"]:
        if ctx["githooks_pre"] is None:
            plan = dict(base)
            plan.update({"op": "create-and-set", "path": workspace / ".githooks" / "pre-commit"})
            return plan
        return _dormant_plan(workspace, ctx, base)
    if not hooks_set and ctx["real"] and ctx["dotgit_pre"] is None:
        if ctx["githooks_pre"] is not None:
            if not _executable(ctx["githooks_pre"]):
                return _refuse(base, "pre-commit is not executable", path=ctx["githooks_pre"])
            plan = dict(base)
            plan.update({
                "op": "trampoline",
                "path": ctx["git_hooks"] / "pre-commit",
                "trampoline": ctx["githooks_pre"],
            })
            return plan
        plan = dict(base)
        plan.update({"op": "create", "path": ctx["git_hooks"] / "pre-commit"})
        return plan
    runs_dotgit = (not hooks_set and ctx["dotgit_pre"] is not None) or (
        hooks_set and ctx["hooks_resolved"] == ctx["git_hooks"]
    )
    if runs_dotgit:
        if ctx["dotgit_pre"] is None:
            plan = dict(base)
            plan.update({"op": "create", "path": ctx["git_hooks"] / "pre-commit"})
            return plan
        return _existing_plan(workspace, ctx, base, ctx["dotgit_pre"])
    if hooks_set and ctx["hooks_resolved"] is not None and _is_inside(ctx["hooks_resolved"], workspace):
        if ctx["active"] is not None:
            return _existing_plan(workspace, ctx, base, ctx["active"])
        plan = dict(base)
        plan.update({"op": "create", "path": ctx["effective"] / "pre-commit"})
        return plan
    return _refuse(base, "hooks directory is outside the workspace", hooks=True)


def _script_for(plan):
    return hook_text.render(
        str(SUITE_ROOT),
        preserved=plan["op"] in ("wrap", "rewrap-and-set"),
        length=plan["install_length"],
        complexity=plan["install_complexity"],
        trampoline=str(plan["trampoline"]) if plan.get("trampoline") else None,
    )


def _set_hooks_path(workspace):
    proc = _git(workspace, "config", "--local", "core.hooksPath", ".githooks")
    if proc.returncode != 0:
        detail = proc.stderr.strip() or "git config --local core.hooksPath failed"
        print(detail, file=sys.stderr)
        return False
    return True


def _guard_write(path, workspace):
    if not _is_inside(path, workspace):
        raise UsageError(f"refusing to write outside the workspace: {path}")


def _write_hook(path, text, workspace, mode=0o755):
    _guard_write(path, workspace)
    atomic_write(path, text, mode=mode)


def _perform(workspace, plan, *, write):
    op = plan["op"]
    path = Path(plan["path"]) if plan.get("path") else None
    hooks_ok = op not in _SETS_HOOKS
    wrote = False
    if op == "refuse":
        hooks_ok = False
    elif op in ("noop", "leave"):
        hooks_ok = True
    elif op == "activate":
        if write:
            hooks_ok = _set_hooks_path(workspace)
            if hooks_ok:
                text = _read(path)
                updated = hook_text.insert_marker(text)
                if updated != text:
                    mode = stat.S_IMODE(path.stat().st_mode)
                    _write_hook(path, updated, workspace, mode)
                wrote = True
        else:
            hooks_ok = True
    elif op == "create-and-set":
        script = _script_for(plan)
        if write:
            _write_hook(path, script, workspace)
            wrote = True
            hooks_ok = _set_hooks_path(workspace)
            if hooks_ok:
                _write_hook(path, hook_text.insert_marker(script), workspace)
        else:
            hooks_ok = True
    elif op == "rewrap-and-set":
        script = _script_for(plan)
        preserved = path.parent / "pre-commit.suite-preserved"
        if write:
            _guard_write(preserved, workspace)
            shutil.copy2(path, preserved)
            _write_hook(path, script, workspace)
            wrote = True
            hooks_ok = _set_hooks_path(workspace)
            if hooks_ok:
                _write_hook(path, hook_text.insert_marker(script), workspace)
        else:
            hooks_ok = True
    elif op == "splice-and-set":
        text = _read(path)
        updated = hook_text.splice(text, plan["blocks"])
        if updated is None:
            plan = dict(plan)
            plan["op"] = "refuse"
            plan["reason"] = "no exit line to splice before"
            op = "refuse"
        elif write:
            mode = stat.S_IMODE(path.stat().st_mode)
            _write_hook(path, updated, workspace, mode)
            wrote = True
            hooks_ok = _set_hooks_path(workspace)
            if hooks_ok:
                marked = hook_text.insert_marker(updated)
                _write_hook(path, marked, workspace, mode)
        else:
            hooks_ok = True
    elif op == "splice":
        text = _read(path)
        updated = hook_text.splice(text, plan["blocks"])
        if updated is None:
            op = "refuse"
            plan = dict(plan)
            plan["op"] = "refuse"
            plan["reason"] = "no exit line to splice before"
        elif write:
            mode = stat.S_IMODE(path.stat().st_mode)
            _write_hook(path, updated, workspace, mode)
            wrote = True
    elif op == "wrap":
        script = _script_for(plan)
        preserved = path.parent / "pre-commit.suite-preserved"
        if write:
            _guard_write(preserved, workspace)
            shutil.copy2(path, preserved)
            _write_hook(path, script, workspace)
            wrote = True
    elif op in ("create", "trampoline"):
        script = _script_for(plan)
        if write:
            _write_hook(path, script, workspace)
            wrote = True
    wrote_length = bool(plan["install_length"] and op in _WRITES_SECTIONS and op != "refuse")
    wrote_complexity = bool(plan["install_complexity"] and op in _WRITES_SECTIONS and op != "refuse")
    hook_will_run = True
    if op in _SETS_HOOKS:
        hook_will_run = hooks_ok
    if op == "refuse":
        hook_will_run = False
        wrote = False
        wrote_length = False
        wrote_complexity = False
    if not write:
        wrote = False
    return {
        "op": op,
        "reason": plan.get("reason", ""),
        "hooks_refused": plan.get("hooks_refused", False),
        "wrote_length": wrote_length,
        "wrote_complexity": wrote_complexity,
        "hooks_ok": hooks_ok,
        "hook_will_run": hook_will_run,
        "wrote": wrote,
        "activated": op == "activate" and hooks_ok,
    }


def _checker_action(wrote, known, *, pure_noop, activated, refused):
    if refused:
        return "refused"
    if activated:
        return "noop"
    if wrote:
        return "installed"
    if pure_noop:
        return "noop"
    if known:
        return "left-existing"
    return "noop"


def _ceilings(workspace, created):
    defaults = (REJECT, MAINTAIN, AIM, COGNITIVE, MAX_ARGS, "default")
    if created:
        return defaults
    path = workspace / ".githooks" / "suite-gates.cfg"
    if not path.exists():
        return defaults
    try:
        cfg = load_config(path)
    except ConfigError:
        # Present and rejected. The hook fail-closes, so neither missing-file
        # defaults nor a parsed ceiling is what the suite sections enforce.
        # null is falsy, so a reader of `value or 500` would adopt the built-in.
        rejected = "rejected"
        return (rejected, rejected, rejected, rejected, rejected, rejected)
    return (cfg.reject, cfg.maintain, cfg.aim, cfg.cognitive, cfg.max_args, "config")


def _length_runs(workspace):
    ctx = _inspect(workspace)
    active = _running_hook(ctx)
    # Git does not run a hook that lacks the executable bit.
    if active is None or not _executable(active):
        return False
    return _real_length(_executed_blob(workspace, active, ctx["texts"]))


def _config_action(workspace, outcome, *, write):
    want = outcome["hook_will_run"] and (
        outcome["wrote_length"] or outcome["wrote_complexity"] or outcome["activated"]
    )
    path = workspace / ".githooks" / "suite-gates.cfg"
    if not want:
        return "not-needed", False
    if path.exists():
        return "left-existing", False
    if not write:
        return "created", False
    try:
        _create_config_excl(path, hook_text.CONFIG_TEXT)
    except FileExistsError:
        return "left-existing", False
    return "created", True


def _report(workspace, plan, outcome, *, created_config):
    refused = outcome["op"] == "refuse"
    pure_noop = outcome["op"] == "noop"
    loc_action = _checker_action(
        outcome["wrote_length"],
        plan["length_known"],
        pure_noop=pure_noop,
        activated=outcome["activated"],
        refused=refused,
    )
    complexity_action = _checker_action(
        outcome["wrote_complexity"],
        plan["complexity_known"],
        pure_noop=pure_noop,
        activated=outcome["activated"],
        refused=refused,
    )
    if outcome["hooks_refused"] or plan.get("hooks_refused"):
        hooks_action = "refused"
    elif outcome["op"] in _SETS_HOOKS and outcome["hooks_ok"]:
        hooks_action = "set:.githooks"
    else:
        hooks_action = "unchanged"
    reject, maintain, aim, cognitive, max_args, source = _ceilings(workspace, created_config)
    return {
        "loc_action": loc_action,
        "complexity_action": complexity_action,
        "config_action": outcome["config_action"],
        "hooks_path_action": hooks_action,
        "chain": _CHAIN.get(outcome["op"], "none"),
        "wrote": bool(outcome["wrote"]),
        "length_runs": _length_runs(workspace),
        "loc_reject": reject,
        "loc_maintain": maintain,
        "loc_aim": aim,
        "cognitive": cognitive,
        "max_args": max_args,
        "ceilings_source": source,
    }


def _as_dry(report):
    dry = dict(report)
    for key in ("loc_action", "complexity_action"):
        if dry[key] == "installed":
            dry[key] = "would-install"
    if dry["config_action"] == "created":
        dry["config_action"] = "would-create"
    dry["wrote"] = False
    return dry


def install(workspace, *, confirmed):
    """Inspect ``workspace`` and, when ``confirmed``, install the missing gates.

    Returns the report dict. Unsafe paths raise UsageError and write nothing.
    """
    ws = _validate(workspace)
    ctx = _inspect(ws)
    plan = _decide(ws, ctx)
    if plan["op"] == "refuse":
        print(plan["reason"], file=sys.stderr)
    outcome = _perform(ws, plan, write=confirmed and plan["op"] != "refuse")
    if outcome["op"] == "refuse" and plan["op"] != "refuse":
        print(outcome["reason"], file=sys.stderr)
    config_action, created = _config_action(
        ws,
        outcome,
        write=confirmed and outcome["op"] != "refuse",
    )
    outcome["config_action"] = config_action
    report = _report(ws, plan, outcome, created_config=created)
    if not confirmed and outcome["op"] != "refuse":
        report = _as_dry(report)
    return {key: report[key] for key in _REPORT_KEYS}


def _format_human(report):
    parts = []
    for key in _REPORT_KEYS:
        value = report[key]
        if value is None:
            shown = "null"
        elif isinstance(value, bool):
            shown = "true" if value else "false"
        else:
            shown = value
        parts.append(f"{key}={shown}")
    return "suite-gates: " + " ".join(parts)


def _refused(report):
    return (
        report["loc_action"] == "refused"
        or report["complexity_action"] == "refused"
        or report["hooks_path_action"] == "refused"
    )


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(prog="install_gates.py")
    parser.add_argument("--workspace")
    parser.add_argument("--workspace-confirmed", action="store_true")
    parser.add_argument("--output-json", action="store_true")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else 2
    if not args.workspace:
        print(
            "usage: --workspace PATH [--workspace-confirmed] [--output-json]",
            file=sys.stderr,
        )
        return 2
    try:
        report = install(Path(args.workspace), confirmed=args.workspace_confirmed)
    except UsageError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.output_json:
        print(json.dumps(report, indent=2))
    else:
        print(_format_human(report))
    return 1 if _refused(report) else 0


if __name__ == "__main__":
    sys.exit(main())
