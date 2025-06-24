#!/bin/bash
# Test runner script for embedding service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧪 Running Embedding Service Tests${NC}"
echo "=================================="

# Activate virtual environment
source .venv/bin/activate

# Run basic tests
echo -e "\n${YELLOW}📋 Running basic tests...${NC}"
python -m pytest test/test_embedding_service.py -v

# Run advanced tests
echo -e "\n${YELLOW}🚀 Running advanced tests...${NC}"
python -m pytest test/test_embedding_service_advanced.py -v

# Run all tests with coverage (if pytest-cov is available)
if python -c "import pytest_cov" 2>/dev/null; then
    echo -e "\n${YELLOW}📊 Running tests with coverage...${NC}"
    python -m pytest test/ --cov=app.services.embedding_service --cov-report=html --cov-report=term
    echo -e "\n${GREEN}✅ Coverage report generated in htmlcov/index.html${NC}"
else
    echo -e "\n${YELLOW}⚠️ pytest-cov not installed. Skipping coverage report.${NC}"
    echo "To install: uv add --dev pytest-cov"
fi

# Run all tests
echo -e "\n${YELLOW}🔍 Running all tests...${NC}"
python -m pytest test/ -v --tb=short

echo -e "\n${GREEN}✅ All tests completed successfully!${NC}"
echo -e "${GREEN}📈 Test Summary:${NC}"
python -m pytest test/ --tb=no -q | grep -E "(passed|failed|error)" || echo "Test execution completed"
