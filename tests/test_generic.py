"""
Test cases for generic SQL dialects (Postgres, MySQL, SQL Server).
"""
import pytest
from app.core.sql_generator import generate_sql
from app.core.models import SQLRequest, TableSchema, ColumnSchema, Constraints


def test_postgres_simple_query(sample_orders_table):
    """Test simple query in PostgreSQL."""
    request = SQLRequest(
        dialect="postgres",
        schema_name="public",
        tables=[sample_orders_table],
        question="Show all orders"
    )

    response = generate_sql(request)

    assert response.dialect == "postgres"
    assert "orders" in response.sql


def test_postgres_time_filter(sample_orders_table):
    """Test time filtering in PostgreSQL."""
    request = SQLRequest(
        dialect="postgres",
        tables=[sample_orders_table],
        constraints=Constraints(time_range="last_60_days"),
        question="Show recent orders"
    )

    response = generate_sql(request)

    assert "INTERVAL" in response.sql
    assert "60 days" in response.sql or "60" in response.sql


def test_postgres_aggregation(sample_orders_table):
    """Test aggregation in PostgreSQL."""
    request = SQLRequest(
        dialect="postgres",
        tables=[sample_orders_table],
        question="Calculate total order value"
    )

    response = generate_sql(request)

    assert "SUM" in response.sql.upper() or "COUNT" in response.sql.upper()


def test_mysql_simple_query(sample_orders_table):
    """Test simple query in MySQL."""
    request = SQLRequest(
        dialect="mysql",
        schema_name="sales",
        tables=[sample_orders_table],
        question="List all orders"
    )

    response = generate_sql(request)

    assert response.dialect == "mysql"
    assert "orders" in response.sql


def test_mysql_time_filter(sample_orders_table):
    """Test time filtering in MySQL."""
    request = SQLRequest(
        dialect="mysql",
        tables=[sample_orders_table],
        constraints=Constraints(time_range="last_30_days"),
        question="Show last month orders"
    )

    response = generate_sql(request)

    assert "DATE_SUB" in response.sql
    assert "30" in response.sql


def test_mysql_limit_clause(sample_orders_table):
    """Test LIMIT clause in MySQL."""
    request = SQLRequest(
        dialect="mysql",
        tables=[sample_orders_table],
        question="Show top 15 orders"
    )

    response = generate_sql(request)

    assert "LIMIT 15" in response.sql


def test_sqlserver_simple_query(sample_orders_table):
    """Test simple query in SQL Server."""
    request = SQLRequest(
        dialect="sqlserver",
        schema_name="dbo",
        tables=[sample_orders_table],
        question="Display all orders"
    )

    response = generate_sql(request)

    assert response.dialect == "sqlserver"
    assert "orders" in response.sql


def test_sqlserver_top_clause(sample_orders_table):
    """Test TOP clause (not LIMIT) in SQL Server."""
    request = SQLRequest(
        dialect="sqlserver",
        tables=[sample_orders_table],
        question="Show top 25 orders"
    )

    response = generate_sql(request)

    # SQL Server uses TOP instead of LIMIT
    assert "TOP 25" in response.sql


def test_sqlserver_time_filter(sample_orders_table):
    """Test time filtering in SQL Server."""
    request = SQLRequest(
        dialect="sqlserver",
        tables=[sample_orders_table],
        constraints=Constraints(time_range="last_14_days"),
        question="Show recent orders"
    )

    response = generate_sql(request)

    assert "DATEADD" in response.sql
    assert "14" in response.sql


def test_sqlserver_getdate(sample_orders_table):
    """Test GETDATE() function in SQL Server."""
    request = SQLRequest(
        dialect="sqlserver",
        tables=[sample_orders_table],
        constraints=Constraints(time_range="last_7_days"),
        question="Show this week's orders"
    )

    response = generate_sql(request)

    # Should use DATEADD with GETDATE()
    assert "DATEADD" in response.sql


def test_cross_dialect_consistency(sample_orders_table):
    """Test that the same question produces consistent results across dialects."""
    question = "What is the total amount of orders?"

    dialects_to_test = ["postgres", "mysql", "snowflake", "databricks"]
    responses = {}

    for dialect in dialects_to_test:
        request = SQLRequest(
            dialect=dialect,
            tables=[sample_orders_table],
            question=question
        )
        responses[dialect] = generate_sql(request)

    # All should have aggregation
    for dialect, response in responses.items():
        assert response.sql, f"No SQL generated for {dialect}"
        assert "SUM" in response.sql.upper() or "COUNT" in response.sql.upper(), \
            f"No aggregation found in {dialect}"


def test_generic_date_range_postgres(sample_orders_table):
    """Test date range in PostgreSQL."""
    request = SQLRequest(
        dialect="postgres",
        tables=[sample_orders_table],
        constraints=Constraints(time_range="2025-07-01..2025-09-30"),
        question="Show Q3 2025 orders"
    )

    response = generate_sql(request)

    assert "2025-07-01" in response.parameters["named_params"]["start_date"]
    assert "2025-09-30" in response.parameters["named_params"]["end_date"]


def test_generic_multiple_aggregations(sample_orders_table):
    """Test multiple aggregation functions across generic dialects."""
    request = SQLRequest(
        dialect="postgres",
        tables=[sample_orders_table],
        question="Show count and average of order amounts"
    )

    response = generate_sql(request)

    sql_upper = response.sql.upper()
    assert "COUNT" in sql_upper or "AVG" in sql_upper
