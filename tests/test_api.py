"""
Test cases for FastAPI endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.models import SQLRequest, TableSchema, ColumnSchema

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns service information."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Universal Text-to-SQL Agent"
    assert "version" in data


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_list_dialects():
    """Test dialects listing endpoint."""
    response = client.get("/dialects")

    assert response.status_code == 200
    data = response.json()
    assert "dialects" in data
    assert len(data["dialects"]) >= 6  # At least 6 dialects

    dialect_names = [d["name"] for d in data["dialects"]]
    assert "snowflake" in dialect_names
    assert "databricks" in dialect_names
    assert "duckdb" in dialect_names


def test_nl2sql_endpoint_success(sample_orders_table):
    """Test successful SQL generation via API."""
    request_data = {
        "dialect": "snowflake",
        "schema": "ANALYTICS",
        "tables": [
            {
                "name": "orders",
                "description": "Customer orders",
                "columns": [
                    {"name": "order_id", "type": "INTEGER"},
                    {"name": "total_amount", "type": "DECIMAL"}
                ]
            }
        ],
        "question": "What is the total order amount?"
    }

    response = client.post("/nl2sql", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "sql" in data
    assert "dialect" in data
    assert data["dialect"] == "snowflake"
    assert "execution_notes" in data
    assert "explain" in data


def test_nl2sql_endpoint_missing_tables():
    """Test API returns error when no tables provided."""
    request_data = {
        "dialect": "postgres",
        "tables": [],
        "question": "Show data"
    }

    response = client.post("/nl2sql", json=request_data)

    assert response.status_code == 400


def test_nl2sql_endpoint_invalid_dialect():
    """Test API rejects invalid dialect."""
    request_data = {
        "dialect": "invalid_db",
        "tables": [
            {
                "name": "test",
                "columns": [{"name": "id", "type": "INTEGER"}]
            }
        ],
        "question": "Test query"
    }

    response = client.post("/nl2sql", json=request_data)

    assert response.status_code == 422  # Validation error


def test_nl2sql_with_files():
    """Test SQL generation with file sources."""
    request_data = {
        "dialect": "duckdb",
        "tables": [],
        "files": [
            {
                "path": "/data/sales.csv",
                "format": "csv",
                "name": "sales"
            }
        ],
        "question": "Show sales data"
    }

    response = client.post("/nl2sql", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "read_csv_auto" in data["sql"]


def test_validate_endpoint_success():
    """Test request validation endpoint with valid request."""
    request_data = {
        "dialect": "postgres",
        "tables": [
            {
                "name": "users",
                "columns": [{"name": "id", "type": "INTEGER"}]
            }
        ],
        "question": "Show all users"
    }

    response = client.post("/nl2sql/validate", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["tables_count"] == 1


def test_validate_endpoint_warnings():
    """Test validation endpoint returns warnings."""
    request_data = {
        "dialect": "snowflake",
        "tables": [
            {"name": "table1", "columns": [{"name": "id", "type": "INTEGER"}]},
            {"name": "table2", "columns": [{"name": "id", "type": "INTEGER"}]}
        ],
        "question": "Join tables"
        # No join hints provided
    }

    response = client.post("/nl2sql/validate", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert len(data["warnings"]) > 0
    assert any("join" in w.lower() for w in data["warnings"])


def test_nl2sql_with_constraints():
    """Test SQL generation with constraints."""
    request_data = {
        "dialect": "databricks",
        "tables": [
            {
                "name": "events",
                "columns": [
                    {"name": "event_id", "type": "INTEGER"},
                    {"name": "event_date", "type": "DATE"},
                    {"name": "user_id", "type": "INTEGER"}
                ]
            }
        ],
        "constraints": {
            "time_range": "last_30_days",
            "filters": ["user_id > 0"]
        },
        "question": "Show recent events"
    }

    response = client.post("/nl2sql", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "sql" in data
    assert "event_date" in data["sql"]


def test_nl2sql_response_structure():
    """Test that response has all required fields."""
    request_data = {
        "dialect": "mysql",
        "tables": [
            {
                "name": "products",
                "columns": [
                    {"name": "product_id", "type": "INTEGER"},
                    {"name": "price", "type": "DECIMAL"}
                ]
            }
        ],
        "question": "Show expensive products"
    }

    response = client.post("/nl2sql", json=request_data)

    assert response.status_code == 200
    data = response.json()

    # Check all required fields
    assert "sql" in data
    assert "dialect" in data
    assert "execution_notes" in data
    assert "parameters" in data
    assert "validation_checks" in data
    assert "explain" in data

    # Check types
    assert isinstance(data["sql"], str)
    assert isinstance(data["execution_notes"], list)
    assert isinstance(data["parameters"], dict)
    assert isinstance(data["validation_checks"], list)
    assert isinstance(data["explain"], str)
