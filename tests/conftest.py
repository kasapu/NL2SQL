"""
Pytest configuration and fixtures for tests.
"""
import pytest
from typing import Dict, List

from app.core.models import (
    SQLRequest, TableSchema, ColumnSchema,
    Constraints, FileSource
)


@pytest.fixture
def sample_orders_table() -> TableSchema:
    """Sample orders table schema."""
    return TableSchema(
        name="orders",
        description="Customer orders",
        columns=[
            ColumnSchema(name="order_id", type="INTEGER", description="Order ID"),
            ColumnSchema(name="customer_id", type="INTEGER", description="Customer ID"),
            ColumnSchema(name="order_date", type="DATE", description="Order date"),
            ColumnSchema(name="order_status", type="VARCHAR", description="Order status"),
            ColumnSchema(name="total_amount", type="DECIMAL", description="Total order amount"),
            ColumnSchema(name="warehouse_id", type="INTEGER", description="Warehouse ID"),
        ],
        rowcount_estimate=1000000
    )


@pytest.fixture
def sample_customers_table() -> TableSchema:
    """Sample customers table schema."""
    return TableSchema(
        name="customers",
        description="Customer information",
        columns=[
            ColumnSchema(name="customer_id", type="INTEGER", description="Customer ID"),
            ColumnSchema(name="customer_name", type="VARCHAR", description="Customer name"),
            ColumnSchema(name="email", type="VARCHAR", description="Email address"),
            ColumnSchema(name="region", type="VARCHAR", description="Geographic region"),
            ColumnSchema(name="vip_tier", type="VARCHAR", description="VIP tier level"),
        ],
        rowcount_estimate=50000
    )


@pytest.fixture
def sample_order_lines_table() -> TableSchema:
    """Sample order line items table."""
    return TableSchema(
        name="order_lines",
        description="Individual line items in orders",
        columns=[
            ColumnSchema(name="line_id", type="INTEGER", description="Line item ID"),
            ColumnSchema(name="order_id", type="INTEGER", description="Order ID"),
            ColumnSchema(name="product_id", type="INTEGER", description="Product ID"),
            ColumnSchema(name="quantity", type="INTEGER", description="Quantity ordered"),
            ColumnSchema(name="unit_price", type="DECIMAL", description="Unit price"),
            ColumnSchema(name="discount_pct", type="DECIMAL", description="Discount percentage"),
        ],
        rowcount_estimate=5000000
    )


@pytest.fixture
def sample_warehouses_table() -> TableSchema:
    """Sample warehouses table."""
    return TableSchema(
        name="warehouses",
        description="Warehouse locations",
        columns=[
            ColumnSchema(name="warehouse_id", type="INTEGER", description="Warehouse ID"),
            ColumnSchema(name="warehouse_name", type="VARCHAR", description="Warehouse name"),
            ColumnSchema(name="region", type="VARCHAR", description="Geographic region"),
            ColumnSchema(name="capacity", type="INTEGER", description="Storage capacity"),
        ],
        rowcount_estimate=100
    )


@pytest.fixture
def sample_constraints() -> Constraints:
    """Sample query constraints."""
    return Constraints(
        time_range="last_90_days",
        filters=["order_status IN ('shipped', 'delivered')"],
        join_hints=[
            "orders.customer_id -> customers.customer_id",
            "orders.warehouse_id -> warehouses.warehouse_id",
            "orders.order_id -> order_lines.order_id"
        ],
        metric_definitions={
            "net_revenue": "SUM(quantity * unit_price * (1 - discount_pct))"
        }
    )
