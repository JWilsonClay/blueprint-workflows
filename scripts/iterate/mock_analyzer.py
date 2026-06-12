"""
mock_analyzer.py — Deterministic Mock-Trap AST Analyzer (read-only, Python-first)
==================================================================================
Parses a Python test file's Abstract Syntax Tree — WITHOUT executing it — and
extracts the mechanical facts that determine whether the test exercises the
production code it claims to validate or merely patches a mock in its place.

It detects (deterministic, from the AST):

  * Imports — split into TEST-INFRASTRUCTURE (unittest, mock, pytest, …) and
    PRODUCTION CANDIDATES (everything else). Each records its local binding name
    and fully-qualified source.
  * Patch targets — every patch()/@patch/patch.object/patch.dict/mocker.patch/
    monkeypatch.setattr call, with the LITERAL target string it replaces.
  * Mock constructions — MagicMock/Mock/AsyncMock/… instantiations.
  * Per-symbol usage — for each imported production candidate: is it patched
    (its behavior replaced), and how many times is it called?
  * The hardcoded-assertion tautology — a return_value/side_effect literal that
    is later echoed in an `assert == <literal>` / assertEqual(x, <literal>). This
    is the /iterate-test Step-4g / STRICT-RULE-10 deficiency ("an assertion
    against a hardcoded expected output value is always a test deficiency"), made
    mechanical.

It does NOT execute the test, import the module, or reason about Python's
patch-where-it-is-used semantics. It reports presence and counts; the
bridge_classifier turns them into a one-directional advisory signal, and the
/iterate-test agent owns the PRIMARY-vs-INFRASTRUCTURE judgment. Read-only:
parses text, writes nothing.
"""

import ast
from typing import Dict, List, Optional, Set

# Module roots and bound names that are test scaffolding, never the subject under
# test. A test importing ONLY these has no production substrate to exercise.
_TEST_INFRA_ROOTS = frozenset({
    "unittest", "mock", "pytest", "_pytest", "nose", "nose2", "hypothesis",
    "doctest", "pytest_mock", "freezegun", "responses", "httpretty",
    "testfixtures", "factory", "faker",
})
# Names commonly imported FROM unittest.mock / pytest — test infra even though
# their dotted root (e.g. a bare `from unittest.mock import patch`) is resolved.
_TEST_INFRA_NAMES = frozenset({
    "patch", "MagicMock", "Mock", "AsyncMock", "NonCallableMock",
    "NonCallableMagicMock", "PropertyMock", "mock_open", "sentinel", "call",
    "ANY", "create_autospec", "seal", "DEFAULT", "fixture", "raises",
    "mocker", "monkeypatch",
})

# Callables whose first string argument names a target to be replaced by a mock.
_PATCH_TAILS = frozenset({"patch", "patch.object", "patch.dict", "patch.multiple"})
# monkeypatch.setattr(target, ...) (pytest) — handled specially below.
_SETATTR_TAILS = frozenset({"setattr"})

# Mock object constructors.
_MOCK_CLASSES = frozenset({
    "MagicMock", "Mock", "AsyncMock", "NonCallableMock",
    "NonCallableMagicMock", "PropertyMock", "create_autospec", "mock_open",
})

_MAX_ITEMS = 300  # Bound every reported list (CWE-400).


def _dotted(node: ast.AST) -> Optional[str]:
    """Return the dotted name of a Name/Attribute expression, or None."""
    parts: List[str] = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        return ".".join(reversed(parts))
    return None


def _const_value(node: ast.AST):
    """Return the literal value of an ast.Constant, else a sentinel object."""
    if isinstance(node, ast.Constant):
        return node.value
    return _NO_CONST


_NO_CONST = object()


def _is_interesting_literal(value) -> bool:
    """
    One-directional gate for the hardcoded-assertion smell. Only flag literals
    distinctive enough that echoing a mock's canned value in an assert is a real
    tautology signal — never trivial values (None/bool/short) that legitimately
    recur. A True is an advisory candidate; a False is a safe skip.
    """
    if value is None or isinstance(value, bool):
        return False
    if isinstance(value, (str, bytes)):
        return len(value) >= 6
    return False  # numbers recur too often to be a reliable signal


def _target_keys(target: str) -> Set[str]:
    """Identity keys for a patch target string ('a.b.c' -> {'a.b.c','b.c','c'})."""
    if not target:
        return set()
    parts = target.split(".")
    keys = {target, parts[-1]}
    if len(parts) >= 2:
        keys.add(".".join(parts[-2:]))
    return keys


def _symbol_keys(local_name: str, qualified: str) -> Set[str]:
    """Identity keys for an imported symbol, for patch-target matching."""
    keys = {local_name, qualified}
    keys.add(qualified.split(".")[-1])
    return keys


class MockTrapAnalyzer:
    """Read-only AST analyzer of a single Python test file."""

    def analyze(self, relpath: str, source: str, subject: Optional[str] = None) -> Dict:
        """
        Return the mechanical Mock-Trap evidence for one test file.

        On a syntax error the file is reported with ``parse_error: True`` and no
        findings — a malformed test degrades the scan, never crashes it.
        """
        result = {
            "path": relpath,
            "parse_error": False,
            "imports": {"production_candidates": [], "test_infra": []},
            "patches": [],
            "mock_constructions": [],
            "symbols": [],
            "hardcoded_assertions": [],
        }
        try:
            tree = ast.parse(source)
        except (SyntaxError, ValueError) as exc:
            result["parse_error"] = True
            result["parse_error_detail"] = f"{type(exc).__name__}: {exc}"
            return result

        imports = self._collect_imports(tree)
        result["imports"]["production_candidates"] = [
            {k: v for k, v in i.items() if k != "is_test_infra"}
            for i in imports if not i["is_test_infra"]
        ][:_MAX_ITEMS]
        result["imports"]["test_infra"] = [
            {k: v for k, v in i.items() if k != "is_test_infra"}
            for i in imports if i["is_test_infra"]
        ][:_MAX_ITEMS]

        decorator_ids, with_ids = self._structural_call_ids(tree)
        patches = self._collect_patches(tree, decorator_ids, with_ids)
        result["patches"] = patches[:_MAX_ITEMS]
        result["mock_constructions"] = self._collect_mocks(tree)[:_MAX_ITEMS]

        call_counts = self._call_counts(tree)
        result["symbols"] = self._build_symbols(
            [i for i in imports if not i["is_test_infra"]],
            patches, call_counts, subject,
        )[:_MAX_ITEMS]

        result["hardcoded_assertions"] = self._tautology_smells(tree)[:_MAX_ITEMS]
        return result

    # ------------------------------------------------------------------
    # Imports
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_imports(tree: ast.AST) -> List[Dict]:
        out: List[Dict] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    qualified = alias.name
                    local = alias.asname or alias.name.split(".")[0]
                    root = qualified.split(".")[0]
                    out.append({
                        "local_name": local,
                        "qualified_name": qualified,
                        "lineno": node.lineno,
                        "is_test_infra": root in _TEST_INFRA_ROOTS,
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                root = module.split(".")[0] if module else ""
                module_is_infra = root in _TEST_INFRA_ROOTS
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    local = alias.asname or alias.name
                    qualified = f"{module}.{alias.name}" if module else alias.name
                    is_infra = module_is_infra or alias.name in _TEST_INFRA_NAMES
                    out.append({
                        "local_name": local,
                        "qualified_name": qualified,
                        "lineno": node.lineno,
                        "is_test_infra": is_infra,
                    })
        return out

    # ------------------------------------------------------------------
    # Patches
    # ------------------------------------------------------------------

    @staticmethod
    def _structural_call_ids(tree: ast.AST):
        """ids() of Call nodes appearing as decorators or `with` context exprs."""
        decorator_ids: Set[int] = set()
        with_ids: Set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call):
                        decorator_ids.add(id(dec))
            elif isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    if isinstance(item.context_expr, ast.Call):
                        with_ids.add(id(item.context_expr))
        return decorator_ids, with_ids

    def _collect_patches(self, tree, decorator_ids, with_ids) -> List[Dict]:
        out: List[Dict] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = _dotted(node.func)
            if not func:
                continue
            target = self._patch_target(func, node)
            if target is _NOT_PATCH:
                continue
            kind = ("decorator" if id(node) in decorator_ids
                    else "with" if id(node) in with_ids else "call")
            out.append({
                "func": func,
                "target": target,        # may be None if not a string literal
                "kind": kind,
                "lineno": node.lineno,
            })
        return out

    @staticmethod
    def _patch_target(func: str, node: ast.Call):
        """
        Return the patch target string (or None for a non-literal target) if
        *node* is a patch-like call, else the _NOT_PATCH sentinel.
        """
        tail2 = ".".join(func.split(".")[-2:])
        tail1 = func.split(".")[-1]

        # patch("a.b.c") / mocker.patch("a.b.c") / @patch(...) — first positional
        # string is the target. patch.object(Mod, "attr") -> "<Mod>.attr".
        if tail1 == "patch" or tail2 in _PATCH_TAILS:
            if tail2.endswith("patch.object") or tail1 == "object":
                # patch.object(target_obj, "attr")
                if len(node.args) >= 2:
                    obj = _dotted(node.args[0])
                    attr = _const_value(node.args[1])
                    if obj and isinstance(attr, str):
                        return f"{obj}.{attr}"
                return None
            if tail2.endswith("patch.dict") or tail2.endswith("patch.multiple"):
                tgt = _const_value(node.args[0]) if node.args else _NO_CONST
                return tgt if isinstance(tgt, str) else None
            # plain patch(...)
            if node.args:
                tgt = _const_value(node.args[0])
                return tgt if isinstance(tgt, str) else None
            return None

        # monkeypatch.setattr("a.b.c", val) OR monkeypatch.setattr(mod, "name", val)
        if tail1 in _SETATTR_TAILS and func.split(".")[0] in ("monkeypatch", "mp"):
            if node.args:
                first = _const_value(node.args[0])
                if isinstance(first, str):
                    return first
                obj = _dotted(node.args[0])
                attr = _const_value(node.args[1]) if len(node.args) >= 2 else _NO_CONST
                if obj and isinstance(attr, str):
                    return f"{obj}.{attr}"
            return None

        return _NOT_PATCH

    # ------------------------------------------------------------------
    # Mock constructions
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_mocks(tree: ast.AST) -> List[Dict]:
        out: List[Dict] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = _dotted(node.func)
            if not func:
                continue
            if func.split(".")[-1] not in _MOCK_CLASSES:
                continue
            canned = any(
                kw.arg in ("return_value", "side_effect")
                and isinstance(kw.value, ast.Constant)
                for kw in node.keywords
            )
            out.append({
                "name": func.split(".")[-1],
                "lineno": node.lineno,
                "canned_output": canned,
            })
        return out

    # ------------------------------------------------------------------
    # Call counts + per-symbol fidelity facts
    # ------------------------------------------------------------------

    @staticmethod
    def _call_counts(tree: ast.AST) -> Dict[str, int]:
        """Count calls by the ROOT name of the callee (e.g. mod.run() -> 'mod')."""
        counts: Dict[str, int] = {}
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            dotted = _dotted(node.func)
            if not dotted:
                continue
            head = dotted.split(".")[0]
            counts[head] = counts.get(head, 0) + 1
        return counts

    def _build_symbols(self, prod_imports, patches, call_counts, subject) -> List[Dict]:
        target_keys: Set[str] = set()
        for p in patches:
            target_keys |= _target_keys(p["target"]) if p["target"] else set()

        subj_keys = _target_keys(subject) if subject else set()
        symbols: List[Dict] = []
        seen: Set[str] = set()
        for imp in prod_imports:
            local = imp["local_name"]
            qualified = imp["qualified_name"]
            if local in seen:
                continue
            seen.add(local)
            keys = _symbol_keys(local, qualified)
            patched = bool(keys & target_keys)
            patch_how = None
            if patched:
                for p in patches:
                    if p["target"] and (_target_keys(p["target"]) & keys):
                        patch_how = {"target": p["target"], "kind": p["kind"],
                                     "lineno": p["lineno"]}
                        break
            calls = call_counts.get(local, 0)
            if patched:
                fidelity = "MOCK_TRAP_CANDIDATE"
            elif calls > 0:
                fidelity = "CALLED_LIVE"
            else:
                fidelity = "IMPORTED_UNUSED"
            symbols.append({
                "name": local,
                "qualified_name": qualified,
                "patched": patched,
                "patch_how": patch_how,
                "call_count": calls,
                "fidelity": fidelity,
                "is_subject": bool(subj_keys and (keys & subj_keys)),
            })
        return symbols

    # ------------------------------------------------------------------
    # Hardcoded-assertion tautology
    # ------------------------------------------------------------------

    def _tautology_smells(self, tree: ast.AST) -> List[Dict]:
        canned: Dict[object, int] = {}   # literal value -> first canned lineno
        asserted: Dict[object, int] = {} # literal value -> first assert lineno

        for node in ast.walk(tree):
            # mock.return_value = <const>  /  x.side_effect = <const>
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if (isinstance(tgt, ast.Attribute)
                            and tgt.attr in ("return_value", "side_effect")):
                        val = _const_value(node.value)
                        if val is not _NO_CONST and _is_interesting_literal(val):
                            canned.setdefault(_key(val), node.lineno)
            # MagicMock(return_value=<const>)
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg in ("return_value", "side_effect"):
                        val = _const_value(kw.value)
                        if val is not _NO_CONST and _is_interesting_literal(val):
                            canned.setdefault(_key(val), node.lineno)
            # assert x == <const>  /  assert <const> == x
            if isinstance(node, ast.Assert) and isinstance(node.test, ast.Compare):
                if any(isinstance(op, ast.Eq) for op in node.test.ops):
                    for operand in [node.test.left, *node.test.comparators]:
                        val = _const_value(operand)
                        if val is not _NO_CONST and _is_interesting_literal(val):
                            asserted.setdefault(_key(val), node.lineno)
            # self.assertEqual(x, <const>)
            if isinstance(node, ast.Call):
                fn = _dotted(node.func)
                if fn and fn.split(".")[-1] in ("assertEqual", "assertEquals"):
                    for arg in node.args[:2]:
                        val = _const_value(arg)
                        if val is not _NO_CONST and _is_interesting_literal(val):
                            asserted.setdefault(_key(val), node.lineno)

        out: List[Dict] = []
        for key, canned_line in canned.items():
            if key in asserted:
                out.append({
                    "value_repr": key[:80],
                    "lineno_canned": canned_line,
                    "lineno_assert": asserted[key],
                })
        return out


_NOT_PATCH = object()


def _key(value) -> str:
    """Stable, hashable, printable key for a literal value."""
    return f"{type(value).__name__}:{value!r}"
