#!/bin/bash
# Test runner script for Universal Text-to-SQL Agent

set -e

echo "======================================"
echo "Universal Text-to-SQL Agent - Tests"
echo "======================================"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "Error: pytest is not installed"
    echo "Please install requirements: pip install -r requirements.txt"
    exit 1
fi

# Default: run all tests
TEST_SUITE="${1:-all}"

case $TEST_SUITE in
    all)
        echo "Running all tests..."
        pytest tests/ -v --cov=app --cov-report=term-missing
        ;;
    snowflake)
        echo "Running Snowflake tests..."
        pytest tests/test_snowflake.py -v
        ;;
    databricks)
        echo "Running Databricks tests..."
        pytest tests/test_databricks.py -v
        ;;
    duckdb)
        echo "Running DuckDB tests..."
        pytest tests/test_duckdb.py -v
        ;;
    generic)
        echo "Running Generic SQL tests..."
        pytest tests/test_generic.py -v
        ;;
    api)
        echo "Running API tests..."
        pytest tests/test_api.py -v
        ;;
    quick)
        echo "Running quick test suite..."
        pytest tests/ -v -x --tb=line
        ;;
    coverage)
        echo "Running tests with detailed coverage..."
        pytest tests/ -v --cov=app --cov-report=html --cov-report=term
        echo ""
        echo "Coverage report generated at: htmlcov/index.html"
        ;;
    *)
        echo "Usage: $0 [all|snowflake|databricks|duckdb|generic|api|quick|coverage]"
        echo ""
        echo "Options:"
        echo "  all        - Run all tests (default)"
        echo "  snowflake  - Run Snowflake tests only"
        echo "  databricks - Run Databricks tests only"
        echo "  duckdb     - Run DuckDB file tests only"
        echo "  generic    - Run generic SQL tests only"
        echo "  api        - Run FastAPI endpoint tests only"
        echo "  quick      - Run fast test suite"
        echo "  coverage   - Run with detailed coverage report"
        exit 1
        ;;
esac

echo ""
echo "======================================"
echo "Tests completed!"
echo "======================================"
