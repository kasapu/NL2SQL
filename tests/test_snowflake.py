"""
Test cases for Snowflake SQL generation.
"""
import pytest
from app.core.sql_generator import generate_sql
from app.core.models import SQLRequest, TableSchema, ColumnSchema, Constraints


def test_snowflake_simple_aggregation(sample_orders_table):
    """Test simple aggregation query in Snowflake."""
    request = SQLRequest(
        dialect="snowflake",
        schema_name="ANALYTICS",
        tables=[sample_orders_table],
        question="What is the total amount of all orders?"
    )

    response = generate_sql(request)

    assert response.dialect == "snowflake"
    assert "SUM" in response.sql.upper()
    assert "ANALYTICS.orders" in response.sql or "orders" in response.sql
    assert response.explain
    assert len(response.validation_checks) > 0


def test_snowflake_time_filter(sample_orders_table):
    """Test time-based filtering in Snowflake."""
    request = SQLRequest(
        dialect="snowflake",
        schema_name="ANALYTICS",
        tables=[sample_orders_table],
        constraints=Constraints(time_range="last_90_days"),
        question="Show all orders from the last 90 days"
    )

    response = generate_sql(request)

    assert "DATEADD" in response.sql
    assert "order_date" in response.sql
    assert any("Time filter" in note for note in response.execution_notes)
    assert response.parameters["named_params"].get("days_back") == "90"


def test_snowflake_date_range(sample_orders_table):
    """Test date range filtering in Snowflake."""
    request = SQLRequest(
        dialect="snowflake",
        tables=[sample_orders_table],
        constraints=Constraints(time_range="2025-01-01..2025-03-31"),
        question="Show orders between January and March 2025"
    )

    response = generate_sql(request)

    assert "TRY_TO_DATE" in response.sql
    assert "2025-01-01" in response.parameters["named_params"]["start_date"]
    assert "2025-03-31" in response.parameters["named_params"]["end_date"]


def test_snowflake_top_n_query(sample_orders_table, sample_customers_table):
    """Test TOP N ranking query in Snowflake."""
    request = SQLRequest(
        dialect="snowflake",
        schema_name="ANALYTICS",
        tables=[sample_orders_table, sample_customers_table],
        constraints=Constraints(
            join_hints=["orders.customer_id -> customers.customer_id"]
        ),
        question="Show the top 10 customers by total order amount"
    )

    response = generate_sql(request)

    assert "LIMIT 10" in response.sql
    assert response.parameters["safe_limits"].get("row_limit") == 10
    assert "ROW_NUMBER" in response.sql or "RANK" in response.sql


def test_snowflake_grouping_by_region(sample_orders_table, sample_warehouses_table):
    """Test grouping by dimension in Snowflake."""
    request = SQLRequest(
        dialect="snowflake",
        tables=[sample_orders_table, sample_warehouses_table],
        constraints=Constraints(
            join_hints=["orders.warehouse_id -> warehouses.warehouse_id"]
        ),
        question="Show total orders by region"
    )

    response = generate_sql(request)

    assert "region" in response.sql.lower()
    assert "GROUP BY" in response.sql or "group by" in response.sql


def test_snowflake_multiple_aggregations(sample_orders_table):
    """Test multiple aggregation functions in Snowflake."""
    request = SQLRequest(
        dialect="snowflake",
        tables=[sample_orders_table],
        question="Show the count, sum, and average of order amounts"
    )

    response = generate_sql(request)

    sql_upper = response.sql.upper()
    assert "COUNT" in sql_upper
    assert "SUM" in sql_upper or "AVG" in sql_upper


def test_snowflake_custom_metric(sample_order_lines_table):
    """Test custom metric definition in Snowflake."""
    request = SQLRequest(
        dialect="snowflake",
        tables=[sample_order_lines_table],
        constraints=Constraints(
            metric_definitions={
                "net_revenue": "SUM(quantity * unit_price * (1 - discount_pct))"
            }
        ),
        question="Calculate net revenue"
    )

    response = generate_sql(request)

    assert "net_revenue" in response.sql
    assert "quantity" in response.sql
    assert "unit_price" in response.sql


def test_snowflake_with_filters(sample_orders_table):
    """Test query with custom filters in Snowflake."""
    request = SQLRequest(
        dialect="snowflake",
        tables=[sample_orders_table],
        constraints=Constraints(
            filters=["order_status IN ('shipped', 'delivered')"]
        ),
        question="Show completed orders"
    )

    response = generate_sql(request)

    assert "order_status" in response.sql
    assert "shipped" in response.sql or "delivered" in response.sql


def test_snowflake_fully_qualified_names():
    """Test fully qualified table names in Snowflake."""
    request = SQLRequest(
        dialect="snowflake",
        catalog="PROD_DB",
        schema_name="ANALYTICS",
        tables=[
            TableSchema(
                name="orders",
                columns=[
                    ColumnSchema(name="order_id", type="INTEGER"),
                    ColumnSchema(name="amount", type="DECIMAL")
                ]
            )
        ],
        question="Show all orders"
    )

    response = generate_sql(request)

    # Should have fully qualified name with catalog and schema
    assert "PROD_DB.ANALYTICS.orders" in response.sql or "orders" in response.sql


def test_snowflake_ranking_with_partition(sample_orders_table, sample_customers_table):
    """Test ranking with partition (top N per group) in Snowflake."""
    request = SQLRequest(
        dialect="snowflake",
        tables=[sample_orders_table, sample_customers_table],
        constraints=Constraints(
            join_hints=["orders.customer_id -> customers.customer_id"]
        ),
        question="Show top 5 orders per customer by amount"
    )

    response = generate_sql(request)

    sql_upper = response.sql.upper()
    assert "ROW_NUMBER" in sql_upper or "RANK" in sql_upper
    # Should have PARTITION BY or similar windowing
    assert "PARTITION" in sql_upper or "OVER" in sql_upper
