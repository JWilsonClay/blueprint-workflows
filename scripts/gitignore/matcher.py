"""
matcher.py — Focused gitignore-pattern matching for secret detection
====================================================================
Implements the subset of gitignore semantics needed to intersect the security
patterns with `git ls-files` output (a list of tracked file paths). It is NOT a
full gitignore engine — it deterministically covers the pattern shapes the suite's
security category uses:

  * Directory patterns ("secrets/", ".aws/") — match if the directory name appears
    as a path component of a tracked file (gitignore: a dir pattern matches the dir
    anywhere and everything beneath it).
  * Path patterns containing "/"  — fnmatch against the full relative path.
  * Basename globs (".env", ".env.*", "*.key", "id_rsa*", "credentials*.json") —
    fnmatch against the file's basename (gitignore: an unanchored pattern matches
    at any depth).

Matching is the read-only half of the detect-and-warn flow; it changes nothing.
"""

import fnmatch


def pattern_matches(relpath: str, pattern: str) -> bool:
    """True if tracked file *relpath* (a forward-slash relative path) is matched by
    gitignore *pattern* under the supported subset above."""
    relpath = (relpath or "").strip()
    if relpath.startswith("./"):  # prefix strip — NOT lstrip (would eat dotfile dots)
        relpath = relpath[2:]
    relpath = relpath.strip("/")  # slashes only; safe for ".env" etc.
    pattern = (pattern or "").strip()
    if not relpath or not pattern:
        return False

    parts = relpath.split("/")
    base = parts[-1]

    # Directory pattern, e.g. "secrets/" or ".aws/".
    if pattern.endswith("/"):
        directory = pattern.rstrip("/")
        if "/" in directory:  # nested dir pattern, e.g. "a/secrets/"
            return relpath == directory or relpath.startswith(directory + "/")
        # Match the dir name as any non-final path component (it must be a
        # directory containing the tracked file, not the file itself).
        return directory in parts[:-1]

    # Path pattern with a slash — match against the full relative path.
    if "/" in pattern:
        return fnmatch.fnmatch(relpath, pattern) or fnmatch.fnmatch(relpath, pattern + "/*")

    # Unanchored basename glob — match the file's basename at any depth.
    return fnmatch.fnmatch(base, pattern)


def find_tracked_secrets(tracked_files, patterns) -> list:
    """
    Intersect *tracked_files* (paths from `git ls-files`) with security *patterns*.
    Returns a list of {"path": ..., "pattern": ...} dicts — one per matched file
    (first matching pattern wins). Empty list = no already-tracked secrets.
    """
    hits = []
    for f in tracked_files or []:
        for pat in patterns or []:
            if pattern_matches(f, pat):
                hits.append({"path": f, "pattern": pat})
                break
    return hits
