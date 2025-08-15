#!/bin/bash
# Comprehensive test runner with formatting and reporting

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Starting comprehensive test suite...${NC}"

# Create test output directory
mkdir -p test_outputs

# 1. Code Formatting
echo -e "\n${YELLOW}Running code formatting checks...${NC}"
if flake8 scripts/; then
    echo -e "${GREEN}✓ Code formatting passed${NC}"
else
    echo -e "${RED}× Code formatting failed${NC}"
    exit 1
fi

# 2. Type Checking
echo -e "\n${YELLOW}Running type checks...${NC}"
if mypy scripts/ --ignore-missing-imports; then
    echo -e "${GREEN}✓ Type checking passed${NC}"
else
    echo -e "${RED}× Type checking failed${NC}"
    exit 1
fi

# 3. Run Tests with Coverage
echo -e "\n${YELLOW}Running test suite with coverage...${NC}"
pytest --cov=scripts \
      --cov-report=html:test_outputs/coverage \
      --cov-report=term-missing \
      scripts/test_suite.py

# 4. Generate Reports
echo -e "\n${YELLOW}Generating test reports...${NC}"

# Flake8 HTML report
flake8 scripts/ --format=html --htmldir=test_outputs/flake8

# Create summary report
cat > test_outputs/TEST_SUMMARY.md << EOF
# Test Suite Summary

Run Date: $(date)

## Coverage Report
- See test_outputs/coverage/index.html

## Code Quality Report
- See test_outputs/flake8/index.html

## Test Results
$(pytest scripts/test_suite.py -v)
EOF

echo -e "\n${GREEN}Test suite complete!${NC}"
echo "Reports available in test_outputs/"
echo "- Coverage: test_outputs/coverage/index.html"
echo "- Flake8: test_outputs/flake8/index.html"
echo "- Summary: test_outputs/TEST_SUMMARY.md"