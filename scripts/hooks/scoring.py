"""Stdlib scorers for executable lines, cognitive cost, McCabe, and arguments."""

import ast
import io
import re
import tokenize


class GateSyntaxError(Exception):
    def __init__(self, message, filename=None, line=None):
        super().__init__(message)
        self.message = message
        self.filename = filename
        self.line = line


class Exemptions:
    """File-level LOC reason and per-function COG / ARGS reasons.

    ``by_lineno`` maps ``fn.lineno`` to ``(cog_reason, args_reason)``. A missing
    entry, or a None reason, means that check is not exempt.
    """

    def __init__(self, loc_reason, loc_empty, by_lineno):
        self.loc_reason = loc_reason
        self.loc_empty = loc_empty
        self.by_lineno = by_lineno

    def cog(self, lineno):
        pair = self.by_lineno.get(lineno)
        return None if pair is None else pair[0]

    def args(self, lineno):
        pair = self.by_lineno.get(lineno)
        return None if pair is None else pair[1]


class FunctionFact:
    def __init__(self, node, qualname, nested, base_nesting, start, end):
        self.node = node
        self.qualname = qualname
        self.nested = nested
        self.base_nesting = base_nesting
        self.start = start
        self.end = end


_EXEMPT_RE = re.compile(r"^[ \t]*#[ \t]*(LOC|COG|ARGS)-EXEMPT:[ \t]*(.*?)\s*$")

_SKIP_TOKENS = frozenset({
    tokenize.NL,
    tokenize.NEWLINE,
    tokenize.COMMENT,
    tokenize.ENCODING,
    tokenize.ENDMARKER,
    tokenize.INDENT,
    tokenize.DEDENT,
})

_TRY_TYPES = (ast.Try, ast.TryStar) if hasattr(ast, "TryStar") else (ast.Try,)
_MATCH = getattr(ast, "Match", None)

_DOC_OWNERS = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
_NESTED_FN = (ast.FunctionDef, ast.AsyncFunctionDef)


def _wrap_syntax(exc):
    if isinstance(exc, SyntaxError):
        return GateSyntaxError(exc.msg or str(exc), filename=getattr(exc, "filename", None), line=exc.lineno)
    if isinstance(exc, tokenize.TokenError):
        message = exc.args[0] if exc.args else str(exc)
        line = None
        if len(exc.args) > 1 and isinstance(exc.args[1], tuple) and exc.args[1]:
            line = exc.args[1][0]
        return GateSyntaxError(str(message), line=line)
    return GateSyntaxError(str(exc))


def syntax_line(path, exc):
    if exc.line is None:
        return f"syntax error in {path}: {exc.message}"
    return f"syntax error in {path}: {exc.message} (line {exc.line})"


def decode_source(source):
    if not isinstance(source, (bytes, bytearray)):
        raise TypeError("source must be bytes")
    raw = bytes(source)
    try:
        encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
    except (SyntaxError, UnicodeError, LookupError, tokenize.TokenError) as exc:
        raise _wrap_syntax(exc) from exc
    try:
        return raw.decode(encoding)
    except UnicodeDecodeError as exc:
        raise GateSyntaxError(str(exc)) from exc


def parse_module(text):
    try:
        return ast.parse(text)
    except SyntaxError as exc:
        raise _wrap_syntax(exc) from exc


def _tokens(source):
    try:
        return list(tokenize.tokenize(io.BytesIO(source).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError, UnicodeDecodeError) as exc:
        raise _wrap_syntax(exc) from exc


def _token_end_line(tok):
    line, col = tok.end
    if col == 0 and line > tok.start[0]:
        return line - 1
    return line


def _docstring_lines(tree):
    lines = set()
    for node in ast.walk(tree):
        if not isinstance(node, _DOC_OWNERS) or not node.body:
            continue
        first = node.body[0]
        if not isinstance(first, ast.Expr):
            continue
        value = first.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            end = first.end_lineno or first.lineno
            lines.update(range(first.lineno, end + 1))
    return lines


def executable_line_count(source):
    text = decode_source(source)
    tree = parse_module(text)
    doc_lines = _docstring_lines(tree)
    counted = set()
    for tok in _tokens(source):
        if tok.type in _SKIP_TOKENS:
            continue
        start = tok.start[0]
        end = _token_end_line(tok)
        if end < start:
            continue
        if tok.type == tokenize.STRING and all(n in doc_lines for n in range(start, end + 1)):
            continue
        counted.update(range(start, end + 1))
    return len(counted)


def _children(node, nesting):
    cost = 0
    for child in ast.iter_child_nodes(node):
        cost += _cost(child, nesting)
    return cost


def _cost(node, nesting):
    if isinstance(node, ast.stmt):
        return _stmt(node, nesting)
    if isinstance(node, ast.expr):
        return _expr(node, nesting)
    return _children(node, nesting)


def _expr(node, nesting):
    if node is None:
        return 0
    if isinstance(node, ast.BoolOp):
        cost = len(node.values) - 1
        for value in node.values:
            cost += _expr(value, nesting)
        return cost
    if isinstance(node, ast.IfExp):
        return (
            1 + nesting
            + _expr(node.test, nesting + 1)
            + _expr(node.body, nesting + 1)
            + _expr(node.orelse, nesting + 1)
        )
    return _children(node, nesting)


def _block(stmts, nesting):
    return sum(_stmt(stmt, nesting) for stmt in stmts)


def _if_cost(node, nesting):
    cost = 1 + nesting
    cost += _expr(node.test, nesting)
    cost += _block(node.body, nesting + 1)
    # A sole If in orelse is elif (including else whose only statement is an if).
    # Same nesting, no flat else cost. Any other non-empty orelse is a real else.
    if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
        cost += _if_cost(node.orelse[0], nesting)
    elif node.orelse:
        cost += 1
        cost += _block(node.orelse, nesting + 1)
    return cost


def _loop(node, nesting, tested):
    cost = 1 + nesting + _expr(tested, nesting)
    if isinstance(node, (ast.For, ast.AsyncFor)):
        cost += _expr(node.target, nesting)
    cost += _block(node.body, nesting + 1)
    if node.orelse:
        cost += 1
        cost += _block(node.orelse, nesting + 1)
    return cost


def _try_cost(node, nesting):
    cost = _block(node.body, nesting)
    for handler in node.handlers:
        cost += 1 + nesting
        if handler.type is not None:
            cost += _expr(handler.type, nesting)
        cost += _block(handler.body, nesting + 1)
    if node.orelse:
        cost += 1
        cost += _block(node.orelse, nesting + 1)
    cost += _block(node.finalbody, nesting)
    return cost


def _match_cost(node, nesting):
    cost = 1 + nesting + _expr(node.subject, nesting)
    for case in node.cases:
        if case.guard is not None:
            cost += _expr(case.guard, nesting + 1)
        cost += _block(case.body, nesting + 1)
    return cost


def _stmt(node, nesting):
    if isinstance(node, _NESTED_FN):
        return 0
    if isinstance(node, ast.If):
        return _if_cost(node, nesting)
    if isinstance(node, (ast.For, ast.AsyncFor)):
        return _loop(node, nesting, node.iter)
    if isinstance(node, ast.While):
        return _loop(node, nesting, node.test)
    if isinstance(node, _TRY_TYPES):
        return _try_cost(node, nesting)
    if _MATCH is not None and isinstance(node, _MATCH):
        return _match_cost(node, nesting)
    if isinstance(node, (ast.Break, ast.Continue)):
        return 1
    return _children(node, nesting)


def cognitive(fn, base_nesting):
    return _block(fn.body, base_nesting)


def _span(fn):
    start = fn.lineno
    if fn.decorator_list:
        start = min(start, min(deco.lineno for deco in fn.decorator_list))
    end = fn.end_lineno if fn.end_lineno is not None else fn.lineno
    return start, end


def mccabe_display(fn, nested):
    if nested:
        return 1
    count = 1
    for stmt in fn.body:
        for node in ast.walk(stmt):
            if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler)):
                count += 1
            elif _MATCH is not None and isinstance(node, _MATCH):
                count += len(node.cases) if node.cases else 1
    return count


def argument_count(fn):
    positional = list(fn.args.posonlyargs) + list(fn.args.args)
    if positional and positional[0].arg in ("self", "cls"):
        positional = positional[1:]
    extra = int(fn.args.vararg is not None) + int(fn.args.kwarg is not None)
    return len(positional) + len(fn.args.kwonlyargs) + extra


def iter_functions(tree):
    found = []

    def visit(node, names, in_function):
        if isinstance(node, _NESTED_FN):
            qualname = ".".join([*names, node.name])
            start, end = _span(node)
            found.append(FunctionFact(
                node,
                qualname,
                in_function,
                1 if in_function else 0,
                start,
                end,
            ))
            for stmt in node.body:
                visit(stmt, names + [node.name], True)
            return
        if isinstance(node, ast.ClassDef):
            for stmt in node.body:
                visit(stmt, names + [node.name], in_function)
            return
        for child in ast.iter_child_nodes(node):
            visit(child, names, in_function)

    visit(tree, [], False)
    return found


def _legal_lines(fn):
    lines = {fn.lineno}
    if not fn.body:
        if fn.end_lineno and fn.end_lineno > fn.lineno:
            lines.update(range(fn.lineno + 1, fn.end_lineno + 1))
        return lines
    first = fn.body[0]
    boundary = first.lineno
    decos = getattr(first, "decorator_list", None) or []
    if decos:
        boundary = min(boundary, min(deco.lineno for deco in decos))
    if boundary > fn.lineno:
        lines.update(range(fn.lineno + 1, boundary))
    return lines


def exemptions(source):
    text = decode_source(source)
    tree = parse_module(text)
    loc_reason = None
    loc_empty = False
    pending = []
    for tok in _tokens(source):
        if tok.type != tokenize.COMMENT:
            continue
        match = _EXEMPT_RE.match(tok.string)
        if match is None:
            continue
        kind = match.group(1)
        reason = match.group(2).strip()
        if kind == "LOC":
            if reason:
                if loc_reason is None:
                    loc_reason = reason
            else:
                loc_empty = True
            continue
        pending.append((tok.start[0], kind, reason))
    by_lineno = {}
    for fact in iter_functions(tree):
        legal = _legal_lines(fact.node)
        cog_reason = None
        args_reason = None
        for line, kind, reason in pending:
            if line not in legal or not reason:
                continue
            if kind == "COG" and cog_reason is None:
                cog_reason = reason
            elif kind == "ARGS" and args_reason is None:
                args_reason = reason
        if cog_reason is not None or args_reason is not None:
            by_lineno[fact.node.lineno] = (cog_reason, args_reason)
    return Exemptions(loc_reason, loc_empty, by_lineno)
