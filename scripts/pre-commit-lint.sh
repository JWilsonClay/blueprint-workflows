#!/bin/bash
# Sovereign Suite Linter — Pre-commit Gate
# Blocks commits with CRITICAL linter findings in workflow files.
# Install: cp scripts/pre-commit-lint.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

STAGED_WORKFLOWS=$(git diff --cached --name-only | grep "^claude-commands/.*\.md$")
if [ -z "$STAGED_WORKFLOWS" ]; then
    exit 0
fi

OUTPUT=$(python3 ~/blueprint-workflows/scripts/suite/lint_workflows.py \
    --workspace ~/blueprint-workflows --quiet 2>&1)

CRITICALS=$(echo "$OUTPUT" | grep "CRITICAL:" | head -1 | grep -o "[0-9]*")

if [ "$CRITICALS" != "0" ] && [ -n "$CRITICALS" ]; then
    echo ""
    echo "  PRE-COMMIT BLOCKED — $CRITICALS CRITICAL linter finding(s)"
    echo ""
    echo "$OUTPUT" | grep "\[CRITICAL\]"
    echo ""
    echo "Fix CRITICAL findings before committing workflow files."
    exit 1
fi

exit 0
