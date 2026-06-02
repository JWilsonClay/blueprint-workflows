"""
smell_linter.py — Mechanical Anti-Pattern Smell Linter (read-only, advisory)
=============================================================================
Detects the SPECIFIC mechanical anti-patterns /quality already names
(quality.md Step 4 anti-patterns + Step 7 "no closing pleasantries"):
hedge-language, closing pleasantries, filler openers, and truncation signals.

⚠ ONE-DIRECTIONAL AND ADVISORY. This module is the single highest Mock-Trap risk
in the package, so the contract is stated bluntly:

    smells FOUND      => the output likely has a mechanical defect worth fixing.
    NO smells found   => says NOTHING about quality. NOT a pass. NOT a verdict.

Reading "no smells" as "high quality" is the Mock Trap. Quality is judgment and
is owned by the /quality 7-step protocol, not by this linter. The linter exists
only to catch cheap, mechanical, deterministic defects a human would also catch
at a glance — never to assess excellence.
"""

from typing import Dict, List

_HEDGE = [
    "it depends", "you might want to consider", "you may want to consider",
    "as an ai", "i'm just an ai", "there are a few ways", "it's worth noting that",
    "it is worth noting that", "generally speaking",
]
_PLEASANTRY = [
    "i hope this helps", "hope this helps", "let me know if", "feel free to",
    "happy to help", "hope that helps",
]
_OPENERS = [
    "great question", "sure,", "certainly", "absolutely", "of course",
    "i'd be happy to", "i would be happy to", "great,",
]
_SENTENCE_END = set(".!?:)]}\"'`")


def _line_of(text: str, idx: int) -> int:
    return text.count("\n", 0, max(idx, 0)) + 1


class SmellLinter:
    """Read-only, advisory detector of mechanical anti-pattern smells."""

    def scan(self, text: str) -> Dict:
        smells: List[Dict] = []
        low = text.lower()

        def collect(label: str, phrases: List[str]) -> None:
            samples, count = [], 0
            for phrase in phrases:
                start = 0
                while True:
                    j = low.find(phrase, start)
                    if j == -1:
                        break
                    count += 1
                    if len(samples) < 5:
                        samples.append({"line_no": _line_of(text, j), "excerpt": phrase})
                    start = j + len(phrase)
            if count:
                smells.append({"pattern": label, "count": count, "samples": samples})

        collect("hedge_language", _HEDGE)
        collect("closing_pleasantry", _PLEASANTRY)

        # Filler openers — only meaningful at the very start of the output.
        stripped = text.lstrip()
        first_line = stripped.splitlines()[0].lower() if stripped else ""
        for opener in _OPENERS:
            if first_line.startswith(opener):
                smells.append({"pattern": "filler_opener", "count": 1,
                               "samples": [{"line_no": 1, "excerpt": first_line[:60]}]})
                break

        # Truncation signals.
        trunc = self._truncation_signals(text)
        if trunc:
            last_idx = len(text.rstrip()) - 1
            smells.append({"pattern": "truncation", "count": len(trunc),
                           "samples": [{"line_no": _line_of(text, last_idx), "excerpt": t}
                                       for t in trunc]})

        return {"smells": smells, "smell_total": sum(s["count"] for s in smells)}

    @staticmethod
    def _truncation_signals(text: str) -> List[str]:
        signals = []
        if text.count("```") % 2 != 0:
            signals.append("unclosed code fence")
        rstr = text.rstrip()
        if not rstr:
            return signals
        if rstr.endswith("..."):
            signals.append("trailing ellipsis")
        elif rstr[-1] not in _SENTENCE_END:
            # Only flag prose; tables / lists / headings legitimately lack
            # terminal punctuation.
            last_line = rstr.splitlines()[-1].strip()
            structural = last_line.startswith(("|", "-", "*", "#", ">")) or last_line.endswith("|")
            if last_line and not structural:
                signals.append("output ends without terminal punctuation (possible truncation)")
        return signals
