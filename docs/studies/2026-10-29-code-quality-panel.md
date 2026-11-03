# Code quality panel, 2026-02-27 through 2026-10-29

**Status:** record of one measurement run. Not a workflow. Not a gate.
**Measured:** 2026-10-29. One ruler applied to every snapshot.
**Privacy:** project names, paths, and symbol names are not in this file. The decode key is `docs/studies/.quality-panel-key.md`. That file is gitignored and is the only place the names live. Snapshot labels below (A0, E4, FN-PUMP) match the key.

The chat answer that preceded this file is the verdict. The tables are the part of the run that the verdict stands on. Raw dumps that did not move the verdict were not copied in. The results file was deleted after the run. These numbers are a transcription of that run.

---

## Verdict

Function shape got simpler across the year. File length, and one function inside an exempt long file, got worse in October. Those are different facts, and the length hook can see only the first of them.

On the long-running engine (P-ENG), once the tree was a real engine and not a stub:

| | 2026-09-01 | 2026-10-01 | 2026-10-29 |
|--|------------|------------|------------|
| Excess cognitive points per 1,000 code lines | 35.5 | 27.4 | 35.6 |
| Cognitive p90 of substantive functions | 11.8 | 10.2 | 12.2 |
| Share of substantive functions with McCabe > 10 | 1.6% | 1.9% | 2.0% |
| Arrow-shaped substantive functions | 1.3% | 0.8% | 1.3% |
| Share of physical lines sitting in files over 500 lines | 5.7% | 8.3% | 16.1% |

Against the early large agent product (P-AGT-A, May 2026, no length hook): excess 80.1, cognitive p90 21, McCabe-over-10 share 11.3%, arrow share 7.7%. The engine at the end of October is about half as tangled by those four shape measures, on a tree three times as large.

The same engine's lab (docs, scripts, benches, operations notes) moved the other way: excess 21.8 on 2026-08-01, then 43.9, 63.7, 73.1. Arrow share in the lab ended at 4.1%. The suite's own scripts, measured in August, still look like the spring agent products: excess 76.2, cognitive p90 22, McCabe-over-10 share 10.2%.

A research scratch pocket (P-RSCH) is the worst tree in the panel: excess 86.2, arrow share 15.0%, one function at cognitive 171. It is scratch, and the classifier called it product. It is not the application trend.

Hygiene moved with the shape, not with the god-file share. Blind `except` fell from about 12–17 per 1,000 code lines in the spring agent products to 0.38 on the engine's product tree. Pyflakes fell, and what remains is mostly unused imports. Undefined names stayed rare. The share of code lines longer than 100 characters shrank. The share in the 80–99 band grew, which is why the raw "line too long" rate went up.

No local flake8 log exists. Shell history had no flake8, ruff, pylint, or radon. Git trees are the record.

Three causes, one committed artifact. Model change, the length hook, and practice cannot be separated by this panel. One later web product (P-WEB-C) has no length hook and the simplest functions in the panel, so the shape improvement is not only the hook. Domain still confounds any cross-project comparison. The within-engine monthly series is the cleanest read.

---

## What a year-2 gate has to see

The engine's length hook has been on since 2026-07-30. Since 2026-09-11 it is a commit-scoped ratchet: a file already over the ceiling is left alone until the commit touches it, and an explicit exemption line with a reason lets a touched file pass. The hook's own header asks whether the file got big. It does not ask whether a function got hard to follow.

At the last snapshot, 19 files under the engine's source and script trees were over 500 physical lines. Eighteen carried the exemption. One, at 575 physical lines, did not. Mentioning the exemption string is common (the checker and the docs mention it too) and is not itself a god-file count.

The function the hook cannot see (FN-PUMP) thickened inside an exempt file during October:

| | 2026-10-01 | 2026-10-29 |
|--|------------|------------|
| Cognitive | 59 | 125 |
| McCabe | 58 | 93 |
| Fanout | 39 | 73 |
| Physical range | about 168 lines of body | lines 53–761 |

A nested helper inside it (FN-TICK, 99 lines, 19 `if`s, depth 5, cognitive 109) displays McCabe 1. That 1 is a measurement artifact: the McCabe visitor folds a nested function into the parent and keeps no graph of its own. Cognitive complexity and nesting depth are the numbers to trust for nested helpers. Parent McCabe does not fall when a branch is moved into a nested function.

Argument count moved the wrong way on the same tree. Ruff's too-many-arguments rule fired 0.64 times per 1,000 code lines on the May agent product and 3.4 times on the engine's product tree. A length ceiling does not look at parameter lists.

The highest-leverage missing mechanism is a commit-scoped, per-function complexity check with the same grandfather and the same explicit exemption the length hook already uses. Detail is in "Year 2" below. This file does not install that check.

---

## Method

One ruler for every snapshot. Project configs were not consulted.

**flake8 7.3.0** (mccabe 0.7.0, pycodestyle 2.14.0, pyflakes 3.4.0), its own CPython 3.10. Flags: `--isolated --disable-noqa --max-complexity 10`. Default ignore list still dropped E121, E123, E126, E226, E24, E704, W503, W504. Default line length 79. `# noqa` comments were counted separately and did not silence a hit.

**ruff 0.15.2.** Flags: `--isolated --ignore-noqa`, selected C90, PLR0911, PLR0912, PLR0913, PLR0914, PLR0915, PLR1702, B, BLE, RET. PLR1702 (nesting deeper than 5) fired zero times on every tree. Bugbear hits on the later engine are dominated by B905 (`zip` without `strict`), which is not a tangle measure.

**Cognitive complexity.** A Sonar-style subset, unit-tested before the run. `if` / `elif` / `for` / `while` / `except` / `match` cost 1 plus the current nesting. `else`, `break`, `continue`, and each `and` / `or` cost 1. A ternary costs 1 plus nesting. Nested functions are scored on their own, starting at nesting 1, and their body is not added to the parent. `return` adds nothing. The Python AST cannot tell `elif` from `else` plus `if`; both were scored as `elif`. Review line used here is 15. Excess is the sum of `max(0, cognitive − 15)` per 1,000 code lines.

**Cyclomatic complexity.** The mccabe `PathGraphingAstVisitor` (edges − nodes + 2). It does not count boolean operators, ternaries, or comprehension filters. Nested functions have no graph of their own. A displayed McCabe of 1 on a nested helper understates it. flake8 C901 is the parent-level number and is the one used in the tables.

**Arrow code.** A substantive function (span at least 8, after subtracting the spans of functions nested directly inside it) with nesting depth at least 4 and cognitive complexity at least 15. The span subtraction understates wrappers. For FN-PUMP the real range from the AST probe is the one cited above.

**Code lines (SLOC).** Tokenized code lines. Blanks and comments are out. Line-length buckets were recomputed on the same non-blank, non-comment lines, because raw E501 per 1,000 SLOC misleads.

**God file.** More than 500 physical lines. That matches the engine project's own reminder. Physical lines include blanks and comments, so a comment-heavy file can clear 500 without holding a long procedure.

**Import cycles.** Tarjan on module-level internal imports. Imports written inside functions were counted separately and are not cycle edges.

**Clones.** SHA1 of normalized tokens (names, numbers, and strings collapsed). Functions of at least 40 tokens. Extra SLOC is every copy except the largest.

**Roles.** Excluded from grading: virtualenvs, `site-packages`, `node_modules`, caches, `staticfiles`, migrations, `dist`, `build`, `htmlcov`, `target`, `vendor`, `third_party`. Tests are `tests/` / `test/` or `test_*.py` / `*_test.py` / `conftest.py`. Lab is docs, scripts, tools, benches, and operations notes. Product is everything else. Lint ran on product and lab. Tests were measured for structure and were not flake8'd. Headline numbers are product unless a row says lab or test.

**Self-test, before the measured run.** Five cognitive cases: a single `if` scores 1 at depth 1; a nested `if` scores 3 at depth 2; `and` / `or` scores 3; `for` plus `if` plus `continue` scores 4 at depth 2; `if` / `else` scores 2. One `if` has McCabe 2. The third run finished in 41.4 seconds, exit 0. Two earlier attempts were discarded: the first deadlocked by asking git for a virtualenv, the second crashed the tokenizer on a file with a non-Python indent. Both were fixed before the recorded run. A planned end-of-July snapshot id was not the tree the successful run hashed. The August 1 row is the measured tree. Both ids are in the key.

**Not run.** radon maintainability index, pylint (not installed), mypy, pyright, pytest coverage, mutmut, vulture, bandit, lizard (so the Rust tree stays out of grade), import-linter, tach. complexipy was named by an outside research list and was not checked as installed.

---

## Product series

Excess is cognitive points over 15, per 1,000 code lines. Arrow and McCabe-over-10 are shares of substantive functions. God share is the share of physical lines in files over 500 physical lines. F, E501, and E-other are flake8 hits per 1,000 code lines. C901 is a count, not a rate. B is ruff bugbear hits per 1,000 code lines.

| Snap | Date | Files | SLOC | Fns | Subst | Arrow | Excess | Cog p90 | CC p90 | CC>10 | Nest≥4 | God files | God share | Cycles | In cycles | Clone extra | F | E501 | E other | C901 | B | noqa |
|------|------|------:|-----:|----:|------:|------:|-------:|--------:|-------:|------:|-------:|----------:|----------:|-------:|----------:|------------:|--:|-----:|--------:|-----:|--:|-----:|
| A0 | 02-27 | 104 | 1742 | 115 | 34 | 8.8% | 5.2 | 10.4 | 6 | 0% | 8.8% | 0 | 0 | 0 | 0 | 1.7% | 16.1 | 105.6 | 64.3 | 0 | 5.2 | 0 |
| A1 | 04-13 | 118 | 3196 | 197 | 66 | 10.6 | 45.7 | 15.5 | 8 | 4.5 | 10.6 | 0 | 0 | 1 | 2.5% | 1.7 | 11.9 | 121.7 | 68.5 | 3 | 9.4 | 0 |
| B1 | 05-14 | 273 | 15526 | 756 | 478 | 7.7 | 80.1 | 21.0 | 11 | 11.3 | 8.8 | 0 | 0 | 0 | 0 | 0.4 | 8.4 | 107.0 | 19.8 | 52 | 12.9 | 0.3 |
| C1 | 05-15 | 192 | 13445 | 769 | 468 | 7.5 | 55.8 | 19 | 11 | 10.7 | 8.3 | 0 | 0 | 0 | 0 | 2.3 | 20.3 | 153.1 | 50.1 | 51 | 17.4 | 0 |
| D1 | 05-09 | 62 | 1130 | 53 | 20 | 5.0 | 6.2 | 15.3 | — | 5 | — | 0 | 0 | — | — | — | 26.5 | 100.9 | 58.4 | 1 | 5.3 | — |
| E0 | 07-30 | 8 | 1134 | 56 | 29 | 3.4 | 62.6 | 8.2 | — | 6.9 | — | 1 | 33.1% | — | — | — | 13.2 | 113.8 | 5.3 | 2 | 0 | 0.9 |
| E1 | 08-01 | 25 | 1361 | 94 | 55 | 0 | 1.5 | 6.6 | — | 0 | — | 0 | 0 | — | — | — | 5.9 | 173.4 | 0 | 0 | — | — |
| E2 | 09-01 | 146 | 12833 | 951 | 623 | 1.3 | 35.5 | 11.8 | — | 1.6 | — | 2 | 5.7% | 2 | 3.4% | 0.5 | 1.5 | 476.7 | 0.3 | 10 | 0.5 | 0.7 |
| E3 | 10-01 | 299 | 30756 | 2221 | 1419 | 0.8 | 27.4 | 10.2 | — | 1.9 | 0.9 | 7 | 8.3% | 4 | 4.3% | 3.8 | 2.4 | 253.2 | 0.5 | 27 | 1.2 | 0.3 |
| E4 | 10-29 | 367 | 42223 | 3097 | 1919 | 1.3 | 35.6 | 12.2 | — | 2.0 | 1.4 | 15 | 16.1% | 5 | 3.0% | 2.8 | 2.4 | 290.6 | 1.4 | 39 | 1.9 | 0.3 |
| F1 | 10-07 | 60 | 3406 | 172 | 124 | 0 | 11.5 | 7.0 | — | 1.6 | 0 | 5 | 45.5% | 0 | 0 | 0.6 | 5.3 | 497.1 | 1.8 | 2 | 0.9 | 2.1 |
| G1 | 08-17 | 180 | 9669 | 211 | 140 | 15.0 | 86.2 | 30.2 | — | 14.3 | 17.1 | 3 | 11.2% | — | — | — | 4.2 | 409.1 | 11.7 | 21 | 1.9 | 0.7 |

A dash means that cell was not recorded, not that the value is zero. Percent signs are omitted inside the table to keep the columns aligned; Arrow, CC>10, Nest≥4, God share, In cycles, and Clone extra are percents. Excess, the p90s, and the flake8 rates are not percents.

Reads that the table supports:

- A0 to A1 is the first product, six weeks, no hook. It started flat and grew one hard function. That function (FN-IMPORT, cognitive 96) is about half of A1's excess mass (45.7 × 3.196 ≈ 146 points; the function contributes 81).
- B0, the end-of-March stub of the same agent repo, was 3 files and 154 code lines. It is not in the table. It is not a trend point.
- B1 is the fair large comparison. No file over 500 lines. Shape is the spring peak.
- C1 matches B1. Its lab is two files, and an arrow share on two files is noise.
- D1 is a small early web product. Worst pyflakes rate in the panel (26.5). Its tests, not shown in this table, were 2180 code lines, clone extra 12.9%, excess 31.2.
- E0 is eight source files from the pre-rewrite bundle. One file held a third of the physical lines. Excess was already high because the tree was small.
- E1 is the measured August 1 tree, still small, and the flattest the engine ever measured. Do not treat E1 as "the engine got clean." The engine was not there yet.
- E2 to E4 is the engine. Shape stays in a band. God-file share triples. Excess mass at E4 is 35.6 × 42.223 ≈ 1503 points. The top five functions are about a quarter of that mass. It is a fat tail, not one monster. Arrow counts: about 37 of 478 substantive functions at B1, about 25 of 1919 at E4.
- Prefer the McCabe-over-10 share to the raw C901 count. B1 is 52 functions and 3.35 per 1,000 code lines. E4 is 39 functions and 0.92 per 1,000.
- F1, the later web product, has the simplest functions and the highest god-file share. The largest files are comment- and docstring-heavy. One file is 1056 physical lines and 240 code lines. Physical god-file share overstates tangle there. Its tests are 11364 code lines, 18 god files, 97.4% of test physical lines inside those files.
- G1 is the scratch pocket. Leave it out of the application series.
- Coupling p90 (internal module fanout), where recorded: A1 = 1, B1 = 3, E2 = 5, E3 = 6, E4 = 5.4, F1 = 2. Fanout rose inside the engine and stayed moderate.

H1, the suite's own scripts, is lab rather than product: 133 files, 10479 code lines, 480 functions, 344 substantive, arrow 7.3%, excess 76.2, cognitive p90 22, McCabe-over-10 10.2%, nesting-at-least-4 7.8%, 2 god files, 6.1% of lines, no cycles, clone extra 1.4%, F 5.1, E501 142.1, E other 17.4, C901 35, B 1.7, noqa 0.4. The suite's tests were flat: 798 functions, arrow 0, excess 0.

---

## Engine lab, and the test tree

Lab is where experiments, scripts, and notes live. On P-ENG it did not get the product tree's cleanup.

| Snap | Files | SLOC | Fns | Subst | Arrow | Excess | Cog p90 | CC>10 | Nest≥4 | God files | God share | F | E501 | E other | C901 | B | noqa |
|------|------:|-----:|----:|------:|------:|-------:|--------:|------:|-------:|----------:|----------:|--:|-----:|--------:|-----:|--:|-----:|
| E0 | 23 | 3763 | — | — | — | 51.8 | — | — | — | 5 | 51.3% | — | — | — | — | — | — |
| E1 | 161 | 9814 | — | — | 1.8% | 21.8 | — | — | — | 0 | 0 | 9.7 | 364.5 | — | — | — | — |
| E2 | — | — | — | — | 2.6 | 43.9 | — | — | — | 6 | 13.4% | — | — | — | — | — | — |
| E3 | — | — | — | — | 3.8 | 63.7 | — | — | — | — | — | — | — | — | — | — | — |
| E4 | 412 | 41040 | 2599 | 1622 | 4.1 | 73.1 | 18 | 3.5 | 4.9 | 7 | 9.4% | 6.0 | 425.2 | 10.1 | 56 | 2.3 | 5.5 |

E4 lab arrow is about 66 of 1622 substantive functions. noqa per 1,000 code lines is 5.5 in the lab and 0.3 in product. The lab silences the linter more often, and it is the more tangled of the two.

E4 tests, structure only, not linted: 857 files, 149844 code lines, 13223 functions, 6758 substantive, arrow 1.4%, excess 17.8, cognitive p90 10, McCabe-over-10 0.6%, 65 god files, 25.1% of physical lines, clone extra 9.7%, noqa 1.2. The test tree got large. It did not get arrow-shaped. The smell in the tests is duplication, which matches the spring test trees.

---

## Line length is two different tails

Buckets are non-blank, non-comment lines. No project in this comparison had a configured line length in its project metadata. Recent code is not formatter-clean: a Black-style 88-column format would leave about 0% over 88.

| Tree | Files | Lines | >79 | >88 | >100 | >120 | Longest |
|------|------:|------:|----:|----:|-----:|-----:|--------:|
| A1 product | 123 | 3544 | 10.4% | 7.2% | 4.3% | 2.2% | 259 |
| B1 product | 273 | 16639 | 9.1 | 4.1 | 2.1 | 0.6 | 689 |
| E4 source | 367 | 58112 | 18.2 | 8.7 | 0.4 | 0.1 | 281 |
| F1 product | 60 | 5911 | 19.4 | 2.3 | 0.4 | 0.2 | 138 |

The 80–99 band grew. The over-100 tail shrank. E501 per 1,000 code lines rose because flake8's default wall is 79, and the new code sits just past it. That rise is not a spaghetti rise.

---

## What the linters actually flagged

Blind `except` (BLE001), counts and per 1,000 code lines:

| Tree | Count | Per 1,000 |
|------|------:|----------:|
| A1 | 29 | 9.1 |
| B1 | 190 | 12.2 |
| C1 | 226 | 16.8 |
| E4 product | 16 | 0.38 |
| F1 | 2 | — |

Spring flake8, top of the list, was whitespace, blank lines, and unused imports. A1: E501 389, W293 167, E302 151, F401 29, E402 21. B1: E501 1662, W293 553, E302 112, F401 79, W291 72, C901 52, E402 49. C1: E501 2058, W293 1295, E302 237, F401 205, W291 194, E701 130.

E4 product flake8, top of the list: E501 12270, F401 81, C901 39, E127 23, E128 18, E302 10, F821 8, F541 6. August's product tree had F821 = 2. Undefined names stayed rare. Unused imports are the remaining pyflakes mass, and they are a fraction of the spring rate (81 on 42223 code lines is about 1.9 per 1,000; B1 was 79 on 15526, about 5.1 per 1,000).

E4 product ruff, the rules that fired: PLR0913 (too many arguments) 143, B905 56, C901 38, PLR0912 25, PLR0915 20, BLE001 16. PLR1702 = 0. The argument-count rate is the hygiene number that got worse.

F1 top of flake8: E501 1693, F401 11, F405 4, F403 3. No F821 in the top eight.

---

## Cycles, clones, exemptions

E4 product import cycles: five groups, four of size 2 and one of size 3, about 3% of modules. The usual shape is a package init that imports a submodule which imports back. That is a mild smell. It is not a ball of mud. Spring products were at or near zero; A1 had one group and 2.5% of modules. The module names are in the key.

Clone extra on product trees stayed small (E4 2.8%, B1 0.4%, A1 1.7%). The duplication that shows up is in tests.

Exemption comments on the long engine files say, repeatedly, that a split would be a fake seam, or that the long function is one dispatch chain. The length gate is satisfied by the marker. Complexity of the marked file is a separate fact. One source file grew from 838 physical lines on October 1 to 1781 at the last snapshot (FL-MEMO) under that marker.

---

## Coverage of the research list

An outside list grouped eight families of checks and recommended a build order starting at Ruff, then cognitive complexity, then a living metrics page. This section says which of those already exist in the Sovereign Suite, whether that existence is honed for the job it claims, and which items leave the active list.

"Accept" means the workflow does a real job, the job is specific, and rewriting it would not create the missing meter. Nothing in this commit edits a workflow. A hone that turned a checklist into a commit gate would be a new mechanism.

### Accept, and take off the active list

These have a real surface. They are manual, invoked, and already specific. They are not commit gates, and they do not need a rewrite to keep doing their job.

| Item | Where it already lives | Hone? |
|------|------------------------|-------|
| Separation of concerns as a campaign | `/soc`. Eight-step strangler extraction. Step 0 tells the agent to look at file size, cyclomatic complexity, imports, callers, and a dependency graph. Success bar is a new module under about 250 lines, independently testable, suite green, and the leftover file under about 300 lines. | No. It is a refactor campaign. The cyclomatic mention is agent judgment during an extraction, not a meter. Turning Step 0 into a linter would replace the campaign. |
| Code review | `/deepcode` reviews workspace scripts for smells, including duplication, complexity, long functions, and deep nesting, when triage or a person invokes it. `/redteam` is a six-phase adversarial audit. | No. Neither is a required pre-merge review of product code. Both are honed for the review they are. |
| pytest coverage, as an audit | `/redteam` Phase 1 runs coverage and parses gaps with `scripts/redteam/redteam_audit.py` (default attention at 80%, 100% on the surface-map files). `/testpackage` tells the author to aim above 85% when writing the suite for a decomposed module. | No. Invoked and engine-backed. Not a CI or pre-push gate. The absence of a gate is not a dull blade on the audit. |
| Hollow tests | `/iterate-test` is the Mock Trap workflow: a test that mocks the intelligence it claims to test. Engine-backed, and the engine is forbidden to decide the primary-versus-infrastructure call. `/redteam` Phase 1 also audits mocks. | No. This is the suite's answer to "the suite is green and the intelligence was never reached." |
| Mutation, as a concept inside that audit | `/redteam` defines mutation and asks the audit to name a missed mutation. The built engine does not run mutmut. It parses coverage, enumerates mocks, and scans secrets. | No. Do not hone `/redteam` into a mutmut runner. mutmut stays on the slow list below. |
| Security smells, as a hardening pass | `/harden` is a 19-item checklist with grades, backed by `scripts/harden/harden_audit.py`. Credential scan is grep, with redaction. The agent cannot grade above the engine's ceiling. | No. It is not bandit, and it is honed for the checklist. |
| History hygiene | `/gitclean` scrubs history and repairs the index. | No. It does not enforce feature branches. |
| Workflow-markdown lint on this repo | `scripts/pre-commit-lint.sh` blocks a commit when staged `claude-commands/*.md` files have a CRITICAL finding from `lint_workflows.py`. | No. It does not look at project Python. Pillar 5 is the design note for that suite-linter family. It is not a product-code quality program. |

### Thin mentions, not coverage

These sentences exist. They do not measure, and they do not gate. They leave the list as "solved" and they also leave the list as "needs a hone." There is nothing there to tighten.

- `/execute-build` says new functions get type hints and docstrings if the codebase already uses them.
- `/soc` Step 0 names cyclomatic complexity as one input to a human extraction decision.

### Uncovered, still on the list

No workflow runs these on project Python, and sentinel does not install them.

- Formatter (Black or Ruff format).
- Ruff or flake8 as a project-Python gate (unused imports, undefined names, blind `except`, pycodestyle).
- Cognitive complexity as a gate. complexipy was not verified here.
- McCabe / C90 as a gate. C901 was measured. Nothing blocks on it.
- Nesting depth as a gate. PLR1702 fired zero times everywhere, so it is a weak additional gate once a complexity gate exists.
- God-file / file-length gate inside the suite. One external project has the 500-line ratchet and the exemption marker. The suite does not deliver that hook.
- Maintainability index.
- mypy or pyright.
- Vulture.
- Bandit as a tool.
- Clone detection as a recurring scan.
- Import cycles, tach, import-linter, or a layering fitness function.
- Feature-branch enforcement.
- TDD / red-green-refactor as a mechanical or even a prompted protocol.
- A living generated quality page. `docs/DESIGN_Machine_Documents.md` is a ratified design (2026-09-30). Its own status says nothing in it has been built. It is the conceptual home for a generated page. It does not install a linter, and it is not a current capability.

### Active list after that cut

Order is leverage against this panel, which disagrees with the outside list's "Ruff first" for the long-running engine. Hygiene on that engine already moved without a suite hook. What got worse, and what no workflow measures, is per-function complexity inside exempt long files, argument count, and the lab.

1. Commit-scoped complexity on changed functions, with grandfather and an explicit exemption. Cognitive complexity is the measure that matched "hard to follow." McCabe C90 is the measure already in Ruff. Argument count (PLR0913) belongs in the same gate because that rate rose. Thresholds to start from, not laws: cognitive 15, McCabe 10, on a function the commit touched. Existing hotspots stay until touched, and a touched hotspot needs an exemption line with a reason, the same way the length hook works.
2. Ruff, selected rules, as the instrument for (1) and as the first tool for a repo that still looks like spring (unused imports, blind `except`, whitespace). A full Ruff format run is a large diff. The line-length table says the over-100 tail is already small and the 80–99 band is where the new code sits. Format is real, and it is not the regression.
3. A short reminder of the live gates, in the session, and a generated metrics page only after a gate exists to report. The ratified machine-document spec is the place a generated page belongs. Pasting PEP 8 into every workspace is the wrong document: the models already keep undefined names and bare `except` rare. The reminder that can change a commit is the one that names the ceiling, the exemption, and the contract the file is under.
4. Import cycles and layer rules. Current cycles are small. Worth a fitness function once the complexity gate exists. Not the fire.
5. Gradual types on public functions. mypy in CI or on changed files. Not on every keystroke.
6. Vulture on changed files, or on a schedule.
7. Off the commit path: full pylint, radon as a report, mutmut, deep coverage, bandit, clone scan. `/redteam` and `/harden` remain the invoked audits for the hollow-test and security questions.

---

## Year 2

Stronger models did not, by themselves, keep October from thickening FN-PUMP. The length hook did not either: the file was exempt, and the hook does not score functions. A year-2 mechanism has to fire when a function in a touched file crosses the line, including a file the length hook has agreed to ignore.

That is prevention that compounds. Each commit is checked. Exemptions are written down. The next year cannot re-accumulate the October pattern without a recorded reason. It is not an exponential rewrite of the existing tree, and a linter will not produce one. Grandfathering is the point. The existing hotspots stay legal until a commit touches them.

### Shape of the first gate

Opt-in, per workspace. A suite script the workspace chooses to point a hook at. Same two ideas as the length hook:

- Commit-scoped. Only functions in files the commit touches are judged. The rest of the tree is grandfathered.
- An exemption marker, with a reason on the same line, escapes the function or the file. The reason is the record. A silent skip is not.

Fail the commit when a touched, non-exempt function is over the ceiling. Report the function, the score, and the ceiling. Do not fail the commit for a file nobody touched.

Ruff is the practical first instrument (C90, PLR0913, and the hygiene codes a given repo still fails). A dedicated cognitive tool is the better match to the pump, and it was not verified as installed during this study. Either instrument is valid if it scores per function and honors the exemption. A 500-line file check cannot see FN-PUMP.

Do not turn this on for every repo from sentinel. Spring-style repos need the hygiene rules first. The engine needs the complexity rule first. One hook with a per-repo selection covers both.

### What not to build first

- A full pylint hook. Too slow for every commit, and Ruff already covers the high-value subset that this panel can see.
- A dump of PEP 8, or of any spec the models were trained on, into a file every agent reads. A short `PROJECT_RULES` / designer-intent reminder is the useful document: the ceilings, the exemption spelling, the module ownership, and a pointer at the locked contract. Five to ten lines that bite. Not the style guide.
- A living `QUALITY.md` before a gate exists. A generated page of last month's numbers is a report. The gate is the mechanism. The page becomes worth generating once the gate is writing the same numbers on each commit. The machine-document spec is the right home for that page, and it is unbuilt on purpose until a workspace captures its own designer intent.
- Feature-branch law, TDD order, and mandatory review, as automation. They are process. `/deepcode`, `/redteam`, and `/soc` already cover the invoked forms. Branch protection, if a host supports it, is a host setting.

### Sentinel is not the installer

Sentinel cannot set up these hooks, on a new repo or an old one.

Its writes, on a confirmed workspace, are three channels: the hidden `.doorway/` state (and the scan tool's own README self-heal), the managed block of `.gitignore`, and `tasks.md` / `implementation-plan.md` only when those files are absent. It does not run downstream workflows on its own except helpdesk-ticket filing when a finding is HIGH. Installing a hook is a new write channel (`.githooks/`, `core.hooksPath`, or `.git/hooks/`) and a new behavior. Detect-and-recommend would fit the workflow it already is. Silent installation would not.

A delivery mechanism that matches the rest of the suite is a separate opt-in installer, or a sentinel step that is written down as a new authorized channel and asks before it writes. Neither exists today. This commit does not add one.

The full execution list is the next section, so a later session can see the boundary without re-reading the workflow.

---

## What sentinel does, executed in full

Source of this list: `claude-commands/sentinel.md` as it stood on 2026-10-29. Default `/sentinel` runs items 1 through 22 and skips Phase 1.5. "In full" below includes the optional enrichment path and the invocation flags, marked so a default run is not confused with a flagged one.

1. **Activate.** On invoke, start Phase 0 immediately. Phases 1 and 2 stay silent. The user sees Phase 3. A pre-flight failure and a scan failure surface immediately, because there is no report to wait for.
2. **Resolve the path (Step 0a), in order.** An explicit `--workspace` path wins. Otherwise infer a provisional root from the deepest common ancestor of open documents. If neither works, ask one question — the absolute path to scan — and halt.
3. **Confirm an inferred path (Step 0a.1).** This step runs only for an inferred path. Print the path, say that a scan may seed an absent `tasks.md`, `implementation-plan.md`, or `.gitignore` entries, and ask `y` / `n`. `y` continues. `n` or any other answer drops the guess and asks the one path question. A non-interactive session refuses, writes nothing, and tells the caller to re-invoke with an explicit `--workspace`. An explicit path skips this gate.
4. **Pre-flight (Step 0b).** The path exists and is a directory. `doorway.py` exists at the suite path. `python3` is on `PATH`. The path is not a system path (`/etc`, `/usr`, `/bin`, `/sbin`, `/lib`, `/proc`, `/sys`, `/home` itself, or a direct child of `/home`). Any failure halts and names the check. No scan.
5. **Declare scope (Step 0c).** Print one line: `[SENTINEL] Scanning: {path} — {UTC timestamp}`. Then stay silent until the report.
6. **Scan (Step 1a).** Run `doorway.py --workspace {path} --output-json`. `--full-scan` is added only when the invocation asked for a deep scan that bypasses the hash cache.
7. **On scan failure (Step 1b).** Print `SCAN FAILURE` and the raw error. File a helpdesk ticket (`source: scan_failure`). Halt. Do not route, and do not invent a partial report.
8. **Parse the JSON (Step 1c).** Drift: new, modified, deleted, unowned, missing README. Recommendations: id, workflow, reason, severity. Metrics: READMEs created, repairs. `zero_finding` (Tier-1 index plus ownership). The substrate index payload.
9. **During that scan, the scan tool may self-heal.** It can create READMEs under the workspace and record that in `metrics.repairs` / `metrics.created`. The agent does not rewrite a README itself. A corrupt README is reported. That is the Mute Witness rule.
10. **Seed `.gitignore` (Step 1d).** Run `gitignore_seeder.py` with `--output-json`. Pass `--workspace-confirmed` only after an explicit path or a confirmed inference. Without the flag the seeder computes the block and scans for tracked secrets, and writes nothing. The write is the managed block between its markers. It is idempotent. Entries outside the block are left alone. Record `block_action` (`created`, `block-appended`, `block-updated`, `unchanged`), tracked secrets, and whether the path is a git repo. A non-empty tracked-secret list becomes a HIGH item, with `/gitclean --mode a` as the recommendation. The seeder does not rewrite history and must not imply the secret is now safe. Seeder failure is non-fatal: log `GITIGNORE SEED SKIPPED` and continue.
11. **Skip agent enrichment on the default path (Phase 1.5).** The core run does not sample files and does not write breadcrumb prose. Enrichment runs only with `--enrich-breadcrumbs`. When it runs: read `.doorway/context_updates.log`; if nothing is marked pending, skip; for each pending directory, sample one to three files and write one compact key/value summary back by replacing that pending token once; run `doorway.py --auto-apply --quiet`; check that the README breadcrumb holds the summary; if the placeholder remains, retry with `--full-scan`; if it still fails, log `BREADCRUMB POPULATION FAILED` and continue. Breadcrumb text stays in the key/value form. Prose goes outside the breadcrumb region, and this phase does not write that prose.
12. **Seed absent plan files (Phase 1.6).** Run `ensure_plan_templates.py` with the same confirmation flag. Create-only. A file that already has non-whitespace content is never overwritten. The check is root-only, so a workspace that keeps its plans elsewhere can receive an empty root `tasks.md` or `implementation-plan.md` the first time. The report's plan line is the place to notice that, and the file can be deleted. After the file exists, the populator does not offer it again. Store populated, skipped, errors, and each action. Errors do not halt. A missing template is a suite-install problem, noted in the report.
13. **Tally (Step 2a).** Count HIGH, MEDIUM, LOW, and INFO. They must sum to the recommendation count. An unknown severity is itself a finding. Also count structural mutations (new + deleted), content drift (modified), and hygiene gaps (unowned + missing README). Hygiene gaps are Tier-2 and do not change `zero_finding`.
14. **Check the routing table against the engine (Step 2b).** Run `sentinel_audit.py` for recommender parity. A non-empty `missing_from_table`, `undercounted_ids`, or `undocumented_severities` means the written table has drifted from `recommender.py`. Routing itself is read from the scan JSON, not re-derived by the agent. The table the engine is supposed to match: `SEQ-SUBSTRATE-HEALTH` → `/investigate` (new or deleted directories, and a second row for a stale index or incomplete ownership); `SEQ-SUBSTRATE-HYGIENE` → `/document` (unowned); `SEQ-SUBSTRATE-MAINTAIN` → `/document` at INFO (missing READMEs; promote only if Tier-2 is configured or the user asks); `SEQ-SUBSTRATE-ASSIMILATE` → `/focus-plan` (more than five directories modified); `SEQ-STRATEGIC-ARCHIVAL` → `/investigate` (deleted); scan failure → `/helpdesk-tickets`.
15. **Apply the extra routing rules.** Repairs greater than zero: tell the user READMEs were created; informational. `zero_finding` and no repairs: route nowhere. `zero_finding` and repairs: `/document`. Index freshness and a bootstrap tag are reported and do not auto-route unless there is structural drift. A missing README does not route to `/document` by default.
16. **Prepare a ticket if anything is HIGH (Step 2c).** Filing waits until after the report, unless the user opted out with `--no-ticket`.
17. **Print the report (Phase 3).** Every field: workspace, scanned-at, duration, directories scanned versus hash-matched, context source (ownership file plus substrate index), substrate state, drift summary including self-heal repairs and the index note, the plan-and-tasks line, findings, routing map, ticket status. Define a piece of jargon on first use. Declare confidence: HIGH if the JSON is valid, MEDIUM if it is partial, LOW if the scan failed and the report is estimated from the last snapshot. A report without confidence is incomplete.
18. **Print the next action.** Name the top workflow and the reason. `proceed` runs it. Naming a workflow runs that one. `skip`, or silence, exits. On a zero-finding with no repairs, print the zero-finding lines instead of a routing prompt.
19. **File the ticket (Step 4a), when HIGH findings exist and the user did not opt out.** Invoke `/helpdesk-tickets` with source, workspace, severity, findings, and trigger time. The ticket records the finding. It does not block the session. This is the only workflow sentinel starts on its own.
20. **Wait for the routing decision (Step 4b).** `proceed`, a named workflow, `skip` / silence, or `rescan`. `rescan` repeats Phases 0–3 with `--full-scan`.
21. **Multi-workspace (Step 4c), only when several `--workspace` paths were given.** Run Phases 0–3 in order, one report section each, then one combined routing map.
22. **Hold the rules the whole time.** Read-only except the three write channels. One question when the path cannot be resolved. No autonomous downstream workflow except the HIGH ticket. Halt on scan failure. Refuse system paths. No undefined jargon. Confidence declared. Do not hand-fix a corrupt README. An inferred workspace is never scanned or written until confirmed. Context comes from the index and the ownership file, not from the count of README files.

Invocation forms, for completeness: `/sentinel`; `/sentinel --workspace /abs/path`; several paths in one invocation; `--full-scan`; `--no-ticket`; `--context-only` (index, ownership, and `zero_finding` only); `--materialize-readmes` (optional human READMEs from the index; not the core path).

What that full execution never does: install a git hook, set `core.hooksPath`, run Ruff, flake8, pylint, vulture, mypy, or a complexity tool, format the tree, or edit project source.

---

## Record limits

- Names, paths, and the snapshot-to-commit map are in the gitignored key. This file is the public record of the measurements.
- The results file and the analyzer were deleted after the run. A later session cannot re-open them. Re-running is a new measurement.
- Tests were not linted.
- Nested-function McCabe of 1 is an artifact. FN-TICK is the worked example.
- Arrow span subtracts nested functions, so wrapper length in the arrow metric is shorter than the source range.
- `elif` and `else`/`if` are scored the same.
- P-RSCH landed in the product role because its research directory was not on the lab list.
- E1 is a small flat tree. The engine series that matters is E2–E4.
- Physical god-file share on F1 overstates tangle. Those files are comment-heavy.
- B905 on the later engine is `zip` strictness, not tangle.
- Model, hook, and practice are not separable here.

### Change log

1. **2026-10-29.** Created from the panel run of this date. Verdict, the tables the verdict uses, the research-list disposition, the year-2 gate, and the sentinel execution list. No workflow was edited.
