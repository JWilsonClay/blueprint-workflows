"""Library tests for the stdlib commit-gate scorers. No git."""

import ast
import unittest

from hooks import config
from hooks.scoring import (
    GateSyntaxError,
    argument_count,
    cognitive,
    executable_line_count,
    exemptions,
    mccabe_display,
)


def _fn(src):
    return ast.parse(src).body[0]


def _inner(src):
    outer = _fn(src)
    for stmt in outer.body:
        if isinstance(stmt, ast.FunctionDef):
            return outer, stmt
    raise AssertionError("no nested function")


class TestCognitive(unittest.TestCase):
    def test_one_if(self):
        src = "def f(a):\n    if a:\n        return 1\n"
        self.assertEqual(cognitive(_fn(src), 0), 1)

    def test_if_inside_if(self):
        src = "def f(a, b):\n    if a:\n        if b:\n            return 1\n"
        self.assertEqual(cognitive(_fn(src), 0), 3)

    def test_bool_operators_in_if(self):
        src = "def f(a, b, c):\n    if a and b or c:\n        return 1\n"
        self.assertEqual(cognitive(_fn(src), 0), 3)

    def test_for_if_continue(self):
        src = "def f(xs):\n    for x in xs:\n        if x:\n            continue\n"
        self.assertEqual(cognitive(_fn(src), 0), 4)

    def test_if_else_without_nested_if(self):
        src = "def f(a):\n    if a:\n        return 1\n    else:\n        return 2\n"
        self.assertEqual(cognitive(_fn(src), 0), 2)

    def test_else_whose_only_statement_is_if_scores_two(self):
        src = (
            "def f(a, b):\n"
            "    if a:\n"
            "        return 1\n"
            "    else:\n"
            "        if b:\n"
            "            return 2\n"
        )
        self.assertEqual(cognitive(_fn(src), 0), 2)

    def test_elif_scores_two(self):
        src = (
            "def f(a, b):\n"
            "    if a:\n"
            "        return 1\n"
            "    elif b:\n"
            "        return 2\n"
        )
        self.assertEqual(cognitive(_fn(src), 0), 2)

    def test_else_with_if_and_another_statement(self):
        src = (
            "def f(a, b):\n"
            "    if a:\n"
            "        return 1\n"
            "    else:\n"
            "        if b:\n"
            "            return 2\n"
            "        return 3\n"
        )
        self.assertEqual(cognitive(_fn(src), 0), 4)

    def test_parent_skips_nested_body(self):
        src = (
            "def outer(a):\n"
            "    if a:\n"
            "        return 1\n"
            "    def inner(b):\n"
            "        if b:\n"
            "            return 1\n"
            "        if b:\n"
            "            return 2\n"
        )
        outer, inner = _inner(src)
        self.assertEqual(cognitive(outer, 0), 1)
        self.assertEqual(cognitive(inner, 1), 4)

    def test_comprehension_filter_is_not_a_decision(self):
        src = "def f(xs):\n    return [x for x in xs if x]\n"
        self.assertEqual(cognitive(_fn(src), 0), 0)

    def test_boolop_inside_comprehension_counts(self):
        src = "def f(xs, y):\n    return [x for x in xs if x and y]\n"
        self.assertEqual(cognitive(_fn(src), 0), 1)

    def test_lambda_boolop_counts(self):
        src = "def f(a, b):\n    return lambda: a and b\n"
        self.assertEqual(cognitive(_fn(src), 0), 1)

    def test_assert_with_and_raise_add_nothing(self):
        src = "def f(a):\n    assert a\n    with a:\n        raise SystemExit\n"
        self.assertEqual(cognitive(_fn(src), 0), 0)

    def test_assert_boolop_counts(self):
        src = "def f(a, b):\n    assert a and b\n"
        self.assertEqual(cognitive(_fn(src), 0), 1)

    def test_match_and_guard(self):
        src = (
            "def f(a, b):\n"
            "    match a:\n"
            "        case 1 if a and b:\n"
            "            return 1\n"
            "        case 2:\n"
            "            return 2\n"
        )
        self.assertEqual(cognitive(_fn(src), 0), 2)

    def test_except_and_except_star(self):
        src = (
            "def f(a):\n"
            "    try:\n"
            "        return a\n"
            "    except Exception:\n"
            "        return 0\n"
        )
        self.assertEqual(cognitive(_fn(src), 0), 1)
        star = (
            "def f(a):\n"
            "    try:\n"
            "        return a\n"
            "    except* Exception:\n"
            "        return 0\n"
        )
        self.assertEqual(cognitive(_fn(star), 0), 1)

    def test_try_else_and_loop_else(self):
        src = (
            "def f(a):\n"
            "    try:\n"
            "        return a\n"
            "    except Exception:\n"
            "        return 0\n"
            "    else:\n"
            "        return 1\n"
        )
        self.assertEqual(cognitive(_fn(src), 0), 2)
        loop = (
            "def f(xs):\n"
            "    for x in xs:\n"
            "        return x\n"
            "    else:\n"
            "        return 0\n"
        )
        self.assertEqual(cognitive(_fn(loop), 0), 2)

    def test_doubly_nested_still_starts_at_one(self):
        src = (
            "def outer():\n"
            "    def mid():\n"
            "        def inner(a):\n"
            "            if a:\n"
            "                return 1\n"
        )
        tree = ast.parse(src)
        outer = tree.body[0]
        mid = outer.body[0]
        inner = mid.body[0]
        self.assertEqual(cognitive(inner, 1), 2)
        self.assertEqual(cognitive(outer, 0), 0)
        self.assertEqual(cognitive(mid, 1), 0)


class TestMccabe(unittest.TestCase):
    def test_one_if_is_two(self):
        src = "def f(a):\n    if a:\n        return 1\n"
        self.assertEqual(mccabe_display(_fn(src), False), 2)

    def test_nested_display_is_one_parent_includes_nested_decisions(self):
        src = (
            "def outer(a):\n"
            "    if a:\n"
            "        return 1\n"
            "    def inner(b):\n"
            "        if b:\n"
            "            return 1\n"
            "        if b:\n"
            "            return 2\n"
        )
        outer, inner = _inner(src)
        self.assertEqual(mccabe_display(inner, True), 1)
        self.assertEqual(mccabe_display(outer, False), 4)
        self.assertEqual(cognitive(outer, 0), 1)

    def test_match_cases_and_empty_match(self):
        src = (
            "def f(a):\n"
            "    match a:\n"
            "        case 1:\n"
            "            return 1\n"
            "        case 2:\n"
            "            return 2\n"
        )
        self.assertEqual(mccabe_display(_fn(src), False), 3)


class TestArgumentCount(unittest.TestCase):
    def _count(self, src):
        return argument_count(_fn(src))

    def test_self_cls_and_varargs(self):
        self.assertEqual(self._count("def f(self, a):\n    pass\n"), 1)
        self.assertEqual(self._count("def f(cls, a, b):\n    pass\n"), 2)
        self.assertEqual(self._count("def f(a, b, *args):\n    pass\n"), 3)
        self.assertEqual(self._count("def f(a, **kwargs):\n    pass\n"), 2)
        self.assertEqual(self._count("def f(self, *args, **kwargs):\n    pass\n"), 2)

    def test_keyword_only_self_is_counted(self):
        self.assertEqual(self._count("def f(*, self):\n    pass\n"), 1)
        self.assertEqual(self._count("def f(a, *, self):\n    pass\n"), 2)

    def test_exactly_five_after_dropped_name_and_a_sixth_fails(self):
        self.assertEqual(self._count("def f(self, a, b, c, d, e):\n    pass\n"), 5)
        self.assertEqual(self._count("def f(cls, a, b, c, d, e):\n    pass\n"), 5)
        self.assertEqual(self._count("def f(self, a, b, c, d, e, g):\n    pass\n"), 6)
        self.assertEqual(self._count("def f(a, b, c, d, e):\n    pass\n"), 5)
        self.assertEqual(self._count("def f(a, b, c, d, e, g):\n    pass\n"), 6)

    def test_module_level_self_is_still_dropped(self):
        self.assertEqual(self._count("def f(self, a, b):\n    pass\n"), 2)


class TestExecutableLines(unittest.TestCase):
    def test_five_hundred_statements(self):
        src = "\n".join(["x = 1"] * 500) + "\n"
        self.assertEqual(executable_line_count(src.encode()), 500)

    def test_comment_block_is_not_executable(self):
        src = "\n".join(["# note"] * 500 + ["x = 1"] * 10) + "\n"
        self.assertEqual(executable_line_count(src.encode()), 10)

    def test_module_docstring_is_not_executable(self):
        doc = ["\"\"\""] + ["prose"] * 398 + ["\"\"\""]
        self.assertEqual(len(doc), 400)
        src = "\n".join(doc + ["x = 1"] * 10) + "\n"
        self.assertEqual(executable_line_count(src.encode()), 10)

    def test_docstring_comment_and_blank_excluded(self):
        src = "def f():\n    \"\"\"doc\n    still\n    \"\"\"\n    x = 1  # comment\n    # only\n\n    y = 2\n"
        self.assertEqual(executable_line_count(src.encode()), 3)

    def test_two_statements_one_line_and_closing_paren(self):
        self.assertEqual(executable_line_count(b"x = 1; y = 2\n"), 1)
        src = "def f(\n    a,\n):\n    return a\n"
        self.assertEqual(executable_line_count(src.encode()), 4)

    def test_non_docstring_string_counts_each_physical_line(self):
        src = 'x = """a\nb\n"""\n'
        self.assertEqual(executable_line_count(src.encode()), 3)

    def test_syntax_error_raises_rather_than_zero(self):
        with self.assertRaises(GateSyntaxError) as caught:
            executable_line_count(b"x =\n")
        self.assertIsInstance(caught.exception, GateSyntaxError)
        self.assertIsNotNone(caught.exception.line)
        self.assertTrue(caught.exception.message)

    def test_non_utf8_raises_rather_than_zero(self):
        with self.assertRaises(GateSyntaxError) as caught:
            executable_line_count(b"\xff")
        self.assertIsInstance(caught.exception, GateSyntaxError)
        self.assertIsNone(caught.exception.line)


class TestExemptions(unittest.TestCase):
    def test_empty_reason_does_not_attach(self):
        src = "def f():  # COG-EXEMPT:\n    return 1\n"
        exempt = exemptions(src.encode())
        self.assertIsNone(exempt.cog(_fn(src).lineno))

    def test_empty_then_real_uses_the_real_reason(self):
        src = "def f():  # COG-EXEMPT:\n    # COG-EXEMPT: real\n    return 1\n"
        exempt = exemptions(src.encode())
        self.assertEqual(exempt.cog(_fn(src).lineno), "real")

    def test_decorator_does_not_attach_and_leading_comment_does(self):
        src = (
            "@deco  # COG-EXEMPT: nope\n"
            "def f(a, b, c, d, e, f):  # ARGS-EXEMPT: dispatcher\n"
            "    # COG-EXEMPT: one chain\n"
            "    \"\"\"doc\"\"\"\n"
            "    # COG-EXEMPT: below\n"
            "    return a\n"
        )
        exempt = exemptions(src.encode())
        fn = _fn(src)
        self.assertEqual(exempt.cog(fn.lineno), "one chain")
        self.assertEqual(exempt.args(fn.lineno), "dispatcher")

    def test_marker_below_docstring_does_not_attach(self):
        src = (
            "def f():\n"
            "    \"\"\"doc\"\"\"\n"
            "    # COG-EXEMPT: below\n"
            "    return 1\n"
        )
        exempt = exemptions(src.encode())
        self.assertIsNone(exempt.cog(_fn(src).lineno))

    def test_decorator_only_does_not_attach(self):
        src = "@deco  # COG-EXEMPT: nope\ndef f():\n    return 1\n"
        exempt = exemptions(src.encode())
        self.assertIsNone(exempt.cog(_fn(src).lineno))

    def test_nested_marker_does_not_cover_the_outer_function(self):
        src = (
            "def outer():\n"
            "    def inner():  # COG-EXEMPT: inner\n"
            "        return 1\n"
            "    return 0\n"
        )
        outer, inner = _inner(src)
        exempt = exemptions(src.encode())
        self.assertIsNone(exempt.cog(outer.lineno))
        self.assertEqual(exempt.cog(inner.lineno), "inner")

    def test_string_and_docstring_are_not_markers(self):
        src = '"""# LOC-EXEMPT: reason"""\ns = "# COG-EXEMPT: reason"\nx = 1\n'
        exempt = exemptions(src.encode())
        self.assertIsNone(exempt.loc_reason)
        self.assertFalse(exempt.loc_empty)

    def test_loc_empty_then_real_reason(self):
        src = "# LOC-EXEMPT:\n# LOC-EXEMPT: real reason\nx = 1\n"
        exempt = exemptions(src.encode())
        self.assertEqual(exempt.loc_reason, "real reason")
        self.assertTrue(exempt.loc_empty)

    def test_loc_empty_alone(self):
        src = "# LOC-EXEMPT:\nx = 1\n"
        exempt = exemptions(src.encode())
        self.assertIsNone(exempt.loc_reason)
        self.assertTrue(exempt.loc_empty)


class TestConfigDefaults(unittest.TestCase):
    def test_constants_and_missing_path(self):
        self.assertEqual(config.REJECT, 500)
        self.assertEqual(config.MAINTAIN, 200)
        self.assertEqual(config.AIM, 150)
        self.assertEqual(config.COGNITIVE, 15)
        self.assertEqual(config.MAX_ARGS, 5)
        cfg = config.load(None)
        self.assertTrue(cfg.missing_file)
        self.assertEqual(cfg.reject, 500)
        self.assertEqual(cfg.maintain, 200)
        self.assertEqual(cfg.aim, 150)
        self.assertEqual(cfg.cognitive, 15)
        self.assertEqual(cfg.max_args, 5)
        self.assertEqual(cfg.missing_keys, [])


if __name__ == "__main__":
    unittest.main()
