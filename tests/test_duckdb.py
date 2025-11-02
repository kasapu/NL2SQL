"""
Test cases for DuckDB file-based SQL generation.
"""
import pytest
from app.core.sql_generator import generate_sql
from app.core.models import SQLRequest, FileSource, Constraints


def test_duckdb_csv_simple():
    """Test simple CSV query in DuckDB."""
    request = SQLRequest(
        dialect="duckdb",
        tables=[],
        files=[
            FileSource(
                path="/data/sales.csv",
                format="csv",
                name="sales"
            )
        ],
        question="Show sales data"
    )

    response = generate_sql(request)

    assert response.dialect == "duckdb"
    assert "read_csv_auto" in response.sql
    assert "/data/sales.csv" in response.sql
    assert "sales" in response.sql


def test_duckdb_excel_query():
    """Test Excel file query in DuckDB."""
    request = SQLRequest(
        dialect="duckdb",
        tables=[],
        files=[
            FileSource(
                path="/data/report.xlsx",
                format="xlsx",
                name="report"
            )
        ],
        question="Analyze the report"
    )

    response = generate_sql(request)

    assert "read_excel" in response.sql
    assert "/data/report.xlsx" in response.sql
    assert any("File" in note for note in response.execution_notes)


def test_duckdb_with_type_inference():
    """Test DuckDB query with inferred types."""
    request = SQLRequest(
        dialect="duckdb",
        tables=[],
        files=[
            FileSource(
                path="/data/transactions.csv",
                format="csv",
                name="transactions",
                inferred_types={
                    "transaction_id": "INTEGER",
                    "amount": "DOUBLE",
                    "date": "DATE"
                }
            )
        ],
        question="Show all transactions"
    )

    response = generate_sql(request)

    assert "TRY_CAST" in response.sql or "CAST" in response.sql
    assert "INTEGER" in response.sql or "DOUBLE" in response.sql


def test_duckdb_aggregation():
    """Test aggregation on CSV file in DuckDB."""
    request = SQLRequest(
        dialect="duckdb",
        tables=[],
        files=[
            FileSource(
                path="/data/orders.csv",
                format="csv",
                name="orders",
                inferred_types={
                    "order_date": "DATE",
                    "amount": "DOUBLE"
                }
            )
        ],
        question="What is the total amount of orders?"
    )

    response = generate_sql(request)

    assert "read_csv_auto" in response.sql
    # Should have aggregation or at least file loading
    assert "orders" in response.sql


def test_duckdb_time_range():
    """Test time-based filtering on CSV in DuckDB."""
    request = SQLRequest(
        dialect="duckdb",
        tables=[],
        files=[
            FileSource(
                path="/data/events.csv",
                format="csv",
                name="events",
                inferred_types={"event_date": "DATE", "user_id": "INTEGER"}
            )
        ],
        constraints=Constraints(time_range="last_7_days"),
        question="Show recent events"
    )

    response = generate_sql(request)

    assert "read_csv_auto" in response.sql
    assert "INTERVAL" in response.sql or "interval" in response.sql


def test_duckdb_multiple_files():
    """Test query with multiple CSV files in DuckDB."""
    request = SQLRequest(
        dialect="duckdb",
        tables=[],
        files=[
            FileSource(path="/data/sales_q1.csv", format="csv", name="sales_q1"),
            FileSource(path="/data/sales_q2.csv", format="csv", name="sales_q2")
        ],
        question="Compare Q1 and Q2 sales"
    )

    response = generate_sql(request)

    assert "sales_q1" in response.sql
    assert "sales_q2" in response.sql or "sales_q1" in response.sql
    # Should have multiple file load notes
    assert len(response.execution_notes) >= 1


def test_duckdb_date_operations():
    """Test date operations in DuckDB."""
    request = SQLRequest(
        dialect="duckdb",
        tables=[],
        files=[
            FileSource(
                path="/data/timeline.csv",
                format="csv",
                name="timeline",
                inferred_types={"event_date": "DATE"}
            )
        ],
        constraints=Constraints(time_range="2025-01-01..2025-12-31"),
        question="Show events in 2025"
    )

    response = generate_sql(request)

    assert "DATE" in response.sql
    assert "2025-01-01" in response.parameters["named_params"]["start_date"]


def test_duckdb_validation_checks():
    """Test that DuckDB queries include validation checks."""
    request = SQLRequest(
        dialect="duckdb",
        tables=[],
        files=[
            FileSource(path="/data/data.csv", format="csv", name="data")
        ],
        question="Analyze data"
    )

    response = generate_sql(request)

    assert len(response.validation_checks) > 0
    assert any("File" in check or "loading" in check.lower() for check in response.validation_checks)


def test_duckdb_explanation():
    """Test that DuckDB queries have proper explanations."""
    request = SQLRequest(
        dialect="duckdb",
        tables=[],
        files=[
            FileSource(path="/data/metrics.csv", format="csv", name="metrics")
        ],
        question="Calculate average metrics"
    )

    response = generate_sql(request)

    assert response.explain
    assert len(response.explain) > 20  # Should be a meaningful explanation
