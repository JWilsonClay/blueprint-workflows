# Gemini `/execute-build` Handoff Guide

*How to open an Antigravity session and delegate a bounded `tasks.md` phase to Gemini, using the mechanism this suite actually has — not a hypothetical one.*

---

## 1. The mechanism, in one sentence

**Open an Antigravity session in this workspace and invoke `/execute-build`.** That's it. No special handoff file, no `/workstream` extension, no translation layer — `/execute-build` is already generic (no Claude-Code-specific tool assumptions), Gemini already has a pointer to `~/.gemini/antigravity/global_workflows/execute-build.md`, and it already consumes exactly the `implementation-plan.md` + `tasks.md` pair this suite uses natively.

This was corrected from an earlier, over-engineered design (a proposed single-engineer `/workstream` mode) once a direct re-read of `execute-build.md` confirmed the extension solved a problem that didn't exist. See `implementation-plan.md`'s "Phase 6 — Handoff Mechanism, Corrected" section for the full reasoning.

## 2. Before you hand anything to Gemini

**Not every phase in `tasks.md` is safe to hand off.** `implementation-plan.md` carries an "Execution-Readiness Per Phase" table — read it before invoking Gemini on anything. The short version:

- **Ready**: a phase whose acceptance criteria are fully mechanical — a named file, a naming convention, a bounded text edit driven by a staging file Claude already produced. Task 2.5a and 2.7 (STRICT RULES compression mechanical-apply) are the proven examples.
- **NOT ready**: anything requiring Honest-Design Discipline, judgment about what's mechanical vs. what's not, or open-ended design work. `/execute-build` Phase 2's own gate will legitimately **HALT** on an underspecified phase — that is correct, safe behavior, not a bug to route around by pushing more detail into the phase description.

**The one-line safety principle carried forward from the original (over-engineered) Phase 6 design, because it was correct even though the mechanism around it wasn't**: bound every delegation to one phase or slice at a time. Never hand off "build the whole plan." `/execute-build`'s own Phase 6 loop already enforces this shape — it builds one phase, issues one receipt, and only advances on success — so this isn't an extra rule to remember, just a description of what already happens.

## 3. The actual steps

1. **Confirm the target phase is ready.** Check `implementation-plan.md`'s Execution-Readiness table, or re-derive it yourself: does the phase's acceptance criteria name a specific file, a specific mechanical edit, and a way to verify it (lint, tests, a diff)? If not, do a Claude design-tightening pass first — that's what Phases 4-5 of this session's own campaign were.
2. **Open an Antigravity session** in this workspace (`~/blueprint-workflows`, or whichever project's root has the `implementation-plan.md`/`tasks.md` pair).
3. **Invoke `/execute-build`.** Gemini's own copy of the workflow runs Phase 0 (Workspace Discovery), builds a Phase Map from `tasks.md`, and starts on the first incomplete phase — or the specific phase you name, if you tell it which one.
4. **Let it run to completion or a legitimate HALT.** A HALT on an underspecified phase means step 1 wasn't done carefully enough — go back and tighten the design, don't push Gemini to guess.
5. **Read the results back yourself — a `git log`/`git diff` review is enough.** No special handoff file format is needed; `/execute-build` writes directly to the shared workspace, and `BUILD_RECEIPTS.md` records what it did.

## 4. How to tell HALT from COMPLETE

Check `.workflow_state/receipts/BUILD_RECEIPTS.md` for the phase's entry:

```
## 2026-07-07 — /execute-build — Phase 1 — Quick Wins
- Phase/Stage: Phase 1 — Quick Wins
- Grade/Status: PHASE COMPLETE
- Files: 5 created (.changelogs/*.md) | 6 modified (5 workflows + tasks.md)
- Commit: 9491958
---
```

`Grade/Status: PHASE COMPLETE` is the signal. If Gemini HALTed instead, there will be no receipt for that phase — the absence itself is the signal, not a special "HALTED" grade value. Cross-check against `tasks.md`'s own checkbox state: a HALT leaves tasks unchecked; a real completion checks them.

## 5. The audit — do not skip this, and do not trust Gemini's own "Evidence:" claims

**Claude runs an independent audit of every Gemini-built phase before accepting it.** This is not optional and it is not a rubber-stamp re-read of what Gemini said it did. The real audit performed on this suite's first live pilot (Phase 1, this session) checked:

- Byte-diff of the actual file changes against the pre-Gemini state (not a summary — the real diff)
- Independent re-counting of anything Gemini's receipt claimed a count for (entry counts, dates) via the same tools a human would use (`grep -c`, not trusting the pointer text)
- `content_hash` recomputed fresh and compared bit-for-bit against what Gemini wrote
- A full lint pass on every touched file (0 CRITICAL/WARNING required)
- File-mtime evidence confirming zero scope creep — only the declared files touched, nothing else

If the audit finds a defect (this suite's own history has one recorded example: `BUILD_RECEIPTS.md`'s `Commit:` field citing a stale pre-Gemini hash because nothing had actually been committed yet), log it — in `PROCESS_LEARNINGS.md`, per this suite's own retrospective discipline — but don't let a cosmetic finding block acceptance if the substantive work is correct. Do let a substantive finding block acceptance.

## 6. Worked example: Phase 1 — Quick Wins (2026-07-07, the suite's first live delegation)

This is the actual first real handoff performed on this workspace, not a hypothetical.

**What was delegated**: `tasks.md` Phase 1, tasks 1.2 and 1.3 — externalizing five workflow files' Change Log sections into `.changelogs/*.md` with a pointer left behind, then re-running the length analyzer to confirm the directional effect. Task 1.1 (a `lint_workflows.py` feature) was already done natively; the delegation was scoped to exactly the two remaining, fully-mechanical tasks.

**Why it was ready**: each of the five migrations was a byte-identical copy-then-pointer operation with an explicit verification command (`lint_workflows.py --file <name>`, 0 CRITICAL/WARNING required) already spelled out in the task text. Nothing in the task required judgment about *what* to compress or *how* — only mechanical execution of an already-fully-specified recipe.

**What happened**: Gemini ran the migration for all five files, re-ran the analyzer, and correctly halted at the phase boundary — its final action was updating `tasks.md`'s own 1.2/1.3 checkboxes, nothing else. `BUILD_RECEIPTS.md` recorded `PHASE COMPLETE`.

**The audit** (performed the same session, independently — not from Gemini's own claims): byte-diff confirmed identical Change Log extraction for all 5 `.changelogs/*.md` files against the pre-Gemini originals; pointer text verified against the exact template with entry counts and dates independently recounted; `content_hash` recomputed and bit-exact matched for all 5; lint scan confirmed 0 CRITICAL/WARNING on the 5 target files; file-mtime evidence confirmed zero scope creep. **Verdict: PASS**, with one cosmetic finding (the stale `Commit:` hash described above) logged to `PROCESS_LEARNINGS.md` and not treated as a blocker.

**The retrospective entry**: `process_learnings/PROCESS_LEARNINGS.md`, "Sovereign Scaling Cluster: First Live Gemini Delegation (Phase 1)" — recorded PASS with one low-priority workflow-improvement suggestion (the receipt writer should detect a batched-commit case rather than citing a stale `HEAD`).

## 7. What's proven and what isn't

As of this writing, this pattern has been exercised **twice** at the mechanical-apply granularity (tasks 2.5a and 2.7, both Claude-staged compression edits applied by hand/reviewed against a staging file) in addition to the one full live Gemini pilot above. It has not yet been exercised on a phase requiring Gemini to make any structural decision beyond "apply this exact, pre-specified change." Do not extrapolate readiness beyond that — every phase still needs its own Execution-Readiness check before handoff, per Section 2.
