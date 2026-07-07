# Honest-Design Discipline — /sentinel (Phase 5.2)

Produced by Claude, 2026-07-07, under `/quality` Maximum rigor. Second of
the remaining 5 Verification-Spine targets.

## 1. What is mechanically verifiable here?

`/sentinel` is already, by a wide margin, the most engine-delegated
workflow in this suite — it calls `doorway.py` (drift detection),
`gitignore_seeder.py` (hygiene), and `ensure_plan_templates.py` (plan
scaffolding) directly, and its own tasks.md seed note ("augment
`scripts/doorway/` with a drift-delta layer") assumed a gap that turns out
to already be built: `doorway.py`'s own snapshot/hash-compare mechanism
(`_load_snapshot`/`_save_snapshot`) already computes `drift.new/modified/
deleted` session-over-session — this **is** the drift-delta layer. There is
no unbuilt drift-delta gap to close.

What IS a real gap, found by direct comparison rather than assumed: Phase
2b's Routing Map table (Doorway Protocol ID → Workflow Trigger) is a
**hand-maintained duplicate** of logic `scripts/doorway/recommender.py`
already owns and emits per-recommendation via each JSON object's own
`workflow` field. Comparing the two directly (not just reading the
`.md`'s claim about itself) surfaces that the duplicate has ALREADY DRIFTED:

1. **A row is missing entirely.** `recommender.py`'s `recommend()` emits a
   *second* `SEQ-SUBSTRATE-HEALTH` recommendation for Tier-1 issues
   (`stale_index`/`ownership_incomplete`) — this recommendation exists in
   the engine's real output but has no corresponding row in Phase 2b's
   table at all.
2. **A severity value is undocumented.** `recommender.py` emits
   `severity: "INFO"` for the `SEQ-SUBSTRATE-MAINTAIN` (missing README)
   recommendation — but Phase 2a's Severity Tally only counts
   `HIGH`/`MEDIUM`/`LOW`, and the GLOSSARY's Severity Tier term only names
   those three. An `INFO`-severity recommendation is silently uncounted:
   it appears in `recommendations` (so `TOTAL = len(recommendations)`
   includes it) but contributes to none of `HIGH`/`MEDIUM`/`LOW`, so the
   three counted tiers will never sum to `TOTAL` and nothing in the report
   template has a line for it.

This is a live instance of exactly the failure this campaign exists to
close: prose *describing* what an engine does, rather than the workflow
*reading* what the engine actually emits — and the prose had already gone
stale relative to the code by the time this pass found it.

## 2. What is irreducible judgment?

Which downstream workflow the user actually chooses to run (Phase 4b),
whether a HIGH finding genuinely warrants a ticket in a given session
context (though Phase 4a's rule is already largely mechanical: HIGH exists
→ file, unless opted out), interpretation of `zero_finding`/repair counts
into the report's prose framing, and all judgment already correctly
reserved elsewhere in this suite (Phase 1.5's optional agent-enrichment
summaries, which are explicitly LLM-authored by design).

## 3. Mock-Trap test

Extracting the literal `id`/`workflow`/`severity` triples `recommender.py`'s
source emits, and diffing them against Phase 2b's table rows, is a pure
text comparison — it does not judge whether the routing decision itself is
*correct* (e.g., whether `/investigate` is the right workflow for a new
directory), only whether the `.md`'s documentation of the engine's
existing, already-decided behavior is complete and current. Safe.

## 4. Engine design for Phase 5.2's build

New package `scripts/sentinel/` — narrower than every prior engine, because
the underlying drift-detection work is already done by `doorway.py`:

1. **`recommender_parity.py`**: `extract_recommender_triples(recommender_py_path) -> List[dict]`
   (regex over `recs.append({...})` blocks in the source, extracting
   `id`/`workflow`/`severity` — a static-analysis-over-known-source-shape
   pattern, safe because `recommender.py` is this repo's own fixed file,
   not an arbitrary external target) and
   `extract_routing_table(sentinel_md_path) -> List[dict]` (parses Phase
   2b's markdown table rows), then `compute_parity(...)` reporting
   `missing_from_table` (IDs the engine emits that the table doesn't
   document) and `undocumented_severities` (severity values the engine
   uses that the table/GLOSSARY doesn't name).
2. **`reporter.py` + `sentinel_audit.py` CLI**.

**Immediate correction, alongside the engine build**: fix the two
discovered defects directly in `sentinel.md` (add the missing Tier-1-issues
`SEQ-SUBSTRATE-HEALTH` row; add `INFO` to the Severity Tier vocabulary and
Phase 2a's tally) — the parity checker's job going forward is to catch the
*next* drift before it ships stale, not to be the only thing fixing this
one.

**Explicitly not built**: anything re-implementing `doorway.py`'s own
drift/hash/snapshot logic (already built, already correct, already the
"drift-delta layer" the seed note asked for); anything for Phase 1.5's
agent-enrichment (explicitly, deliberately LLM-authored); Phase 4's
user-routing judgment.

## 5. Disposition

Seed design **corrected**: the assumed drift-delta gap doesn't exist —
`doorway.py` already does it. The real, higher-value gap was found by
directly diffing the workflow's own documentation against the engine it
already calls, not by re-reading the seed note's assumption uncritically —
and that diff surfaced two live, shipping defects (a missing routing row, an
uncounted severity tier), not a hypothetical risk. Ready for the build.
