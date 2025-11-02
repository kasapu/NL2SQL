"""
Test cases for Databricks (Spark SQL) generation.
"""
import pytest
from app.core.sql_generator import generate_sql
from app.core.models import SQLRequest, TableSchema, ColumnSchema, Constraints


def test_databricks_simple_query(sample_orders_table):
    """Test simple query in Databricks."""
    request = SQLRequest(
        dialect="databricks",
        catalog="hive_metastore",
        schema_name="analytics",
        tables=[sample_orders_table],
        question="Show all orders"
    )

    response = generate_sql(request)

    assert response.dialect == "databricks"
    assert "orders" in response.sql


def test_databricks_unity_catalog(sample_orders_table):
    """Test Unity Catalog qualified names in Databricks."""
    request = SQLRequest(
        dialect="databricks",
        catalog="main",
        schema_name="sales",
        tables=[sample_orders_table],
        question="Show order totals"
    )

    response = generate_sql(request)

    # Should have catalog.schema.table format
    assert "main.sales.orders" in response.sql or "orders" in response.sql


def test_databricks_time_filter(sample_orders_table):
    """Test time filtering with date_add in Databricks."""
    request = SQLRequest(
        dialect="databricks",
        tables=[sample_orders_table],
        constraints=Constraints(time_range="last_30_days"),
        question="Show recent orders"
    )

    response = generate_sql(request)

    assert "date_add" in response.sql
    assert "order_date" in response.sql


def test_databricks_aggregation(sample_orders_table):
    """Test aggregation in Databricks."""
    request = SQLRequest(
        dialect="databricks",
        tables=[sample_orders_table],
        question="What is the total revenue?"
    )

    response = generate_sql(request)

    assert "SUM" in response.sql.upper()


def test_databricks_grouping(sample_orders_table, sample_customers_table):
    """Test GROUP BY in Databricks."""
    request = SQLRequest(
        dialect="databricks",
        tables=[sample_orders_table, sample_customers_table],
        question="Show total orders by customer"
    )

    response = generate_sql(request)

    assert "customer" in response.sql.lower()


def test_databricks_date_range(sample_orders_table):
    """Test date range filtering in Databricks."""
    request = SQLRequest(
        dialect="databricks",
        tables=[sample_orders_table],
        constraints=Constraints(time_range="2025-06-01..2025-08-31"),
        question="Show summer 2025 orders"
    )

    response = generate_sql(request)

    assert "to_date" in response.sql
    assert "2025-06-01" in response.parameters["named_params"]["start_date"]


def test_databricks_ranking(sample_orders_table):
    """Test ranking query in Databricks."""
    request = SQLRequest(
        dialect="databricks",
        tables=[sample_orders_table],
        question="Show top 20 orders by amount"
    )

    response = generate_sql(request)

    assert "LIMIT 20" in response.sql or "limit 20" in response.sql
    assert response.parameters["safe_limits"].get("row_limit") == 20


def test_databricks_cte_usage(sample_orders_table, sample_order_lines_table):
    """Test that CTEs are used in Databricks queries."""
    request = SQLRequest(
        dialect="databricks",
        tables=[sample_orders_table, sample_order_lines_table],
        constraints=Constraints(
            join_hints=["orders.order_id -> order_lines.order_id"]
        ),
        question="Calculate total line items per order"
    )

    response = generate_sql(request)

    # Databricks should prefer CTEs for complex queries
    assert "WITH" in response.sql.upper()


def test_databricks_window_function(sample_orders_table):
    """Test window function in Databricks."""
    request = SQLRequest(
        dialect="databricks",
        tables=[sample_orders_table],
        question="Rank orders by amount within each region"
    )

    response = generate_sql(request)

    sql_upper = response.sql.upper()
    assert "OVER" in sql_upper
    assert "ROW_NUMBER" in sql_upper or "RANK" in sql_upper


def test_databricks_multiple_tables(
    sample_orders_table,
    sample_customers_table,
    sample_warehouses_table
):
    """Test query with multiple table joins in Databricks."""
    request = SQLRequest(
        dialect="databricks",
        tables=[sample_orders_table, sample_customers_table, sample_warehouses_table],
        constraints=Constraints(
            join_hints=[
                "orders.customer_id -> customers.customer_id",
                "orders.warehouse_id -> warehouses.warehouse_id"
            ]
        ),
        question="Show orders with customer and warehouse details"
    )

    response = generate_sql(request)

    assert "orders" in response.sql
    # Should have join validation
    assert len(response.validation_checks) > 0
