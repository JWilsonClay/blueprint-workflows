#!/bin/bash
# run_tests.sh — Post-Modularization Test Runner
# Sovereign Refactor Protocol — Script Suite

# Ensure we are in the scripts directory
cd "$(dirname "$0")"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "🏗️  Starting Refactor Script Suite Test Package..."
echo "------------------------------------------------"

# Run all unit tests with coverage if available
if command -v coverage &> /dev/null
then
    echo "🔬 Running tests with coverage..."
    PYTHONPATH=. coverage run -m unittest discover tests/
    coverage report -m
else
    echo "🔬 Running tests with unittest..."
    PYTHONPATH=. python3 -m unittest discover tests/
fi

RESULT=$?

echo "------------------------------------------------"
if [ $RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
fi

exit $RESULT
