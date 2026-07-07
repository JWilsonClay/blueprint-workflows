"""
secretary — Session Close Evidence Engine
============================================
Deterministic engine (sibling of doorway / focus / receipt / build) backing
`/secretary`'s claim that a session's close artifacts were actually produced,
not merely narrated. `/secretary` claims 4-5 artifacts change every run
(`SUITE_HEALTH.md`, a `manifest/history/` shard, `HANDOFF.md`,
`ANOMALY_LOG.md`, a `PROCESS_LEARNINGS.md` entry) — this package answers
whether they actually did, as filesystem facts (mtime, presence, last dated
entry), never as a judgment on the *content* of what was written.

Three modules:

  1. freshness.py            — did a given path's mtime change since a
                                supplied reference time?
  2. retrospective_check.py  — the last dated entry in a file/glob, and the
                                Retrospective Lag gap comparison (formalizes
                                secretary.md's Step 0b.5 and ADDENDUM E,
                                which already specify this as shell greps —
                                this package moves the *comparison itself*
                                out of eyeballed shell output into a boolean
                                the model reads as a fact).
  3. receipt_presence.py     — generalizes the TRIAGE_RECEIPTS.md /
                                DESIGN_RECEIPTS.md existence+tail pattern
                                secretary.md already hardcodes twice, into
                                one filename-parameterized check.

None of these three judge whether the session was well-scoped, the
retrospective's content insightful, or an anomaly's rationale sound — that
stays with the model, per this suite's Honest-Design Discipline (see
implementation-plan.md's HONEST-DESIGN DISCIPLINE section and
docs/compression-staging/secretary-honest-design.md, Phase 4.3).

Read-only; writes nothing.

Origin: implementation-plan.md Phase 4.3-4.4 (Sovereign Scaling Cluster).
"""

__version__ = "1.0.0"
