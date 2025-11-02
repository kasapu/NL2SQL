"""
Example usage of the Universal Text-to-SQL Agent API.

This script demonstrates how to call the API programmatically.
"""
import requests
import json
from typing import Dict, Any


API_BASE_URL = "http://localhost:8000"


def generate_sql(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call the /nl2sql endpoint to generate SQL.

    Args:
        request_data: Dictionary with request parameters

    Returns:
        Response dictionary with generated SQL
    """
    response = requests.post(
        f"{API_BASE_URL}/nl2sql",
        json=request_data
    )
    response.raise_for_status()
    return response.json()


def validate_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a request before submission.

    Args:
        request_data: Dictionary with request parameters

    Returns:
        Validation results
    """
    response = requests.post(
        f"{API_BASE_URL}/nl2sql/validate",
        json=request_data
    )
    response.raise_for_status()
    return response.json()


def list_supported_dialects() -> Dict[str, Any]:
    """Get list of all supported SQL dialects."""
    response = requests.get(f"{API_BASE_URL}/dialects")
    response.raise_for_status()
    return response.json()


# Example 1: Simple Snowflake query
def example_snowflake_simple():
    """Simple aggregation query in Snowflake."""
    print("\n=== Example 1: Snowflake Simple Aggregation ===\n")

    request = {
        "dialect": "snowflake",
        "schema": "ANALYTICS",
        "tables": [
            {
                "name": "orders",
                "description": "Customer orders",
                "columns": [
                    {"name": "order_id", "type": "INTEGER"},
                    {"name": "customer_id", "type": "INTEGER"},
                    {"name": "total_amount", "type": "DECIMAL"},
                    {"name": "order_date", "type": "DATE"}
                ]
            }
        ],
        "constraints": {
            "time_range": "last_90_days"
        },
        "question": "What is the total order amount in the last 90 days?"
    }

    result = generate_sql(request)

    print(f"Generated SQL:\n{result['sql']}\n")
    print(f"Explanation: {result['explain']}\n")
    print(f"Execution notes: {', '.join(result['execution_notes'])}\n")


# Example 2: Databricks with multiple tables
def example_databricks_joins():
    """Query with joins in Databricks."""
    print("\n=== Example 2: Databricks with Joins ===\n")

    request = {
        "dialect": "databricks",
        "catalog": "main",
        "schema": "sales",
        "tables": [
            {
                "name": "orders",
                "columns": [
                    {"name": "order_id", "type": "BIGINT"},
                    {"name": "customer_id", "type": "BIGINT"},
                    {"name": "amount", "type": "DOUBLE"}
                ]
            },
            {
                "name": "customers",
                "columns": [
                    {"name": "customer_id", "type": "BIGINT"},
                    {"name": "customer_name", "type": "STRING"},
                    {"name": "region", "type": "STRING"}
                ]
            }
        ],
        "constraints": {
            "join_hints": ["orders.customer_id -> customers.customer_id"]
        },
        "question": "Show top 10 customers by total order amount per region"
    }

    result = generate_sql(request)

    print(f"Generated SQL:\n{result['sql']}\n")
    print(f"Validation checks:\n")
    for check in result['validation_checks']:
        print(f"  - {check}")


# Example 3: DuckDB with CSV file
def example_duckdb_csv():
    """Query CSV file using DuckDB."""
    print("\n=== Example 3: DuckDB CSV Query ===\n")

    request = {
        "dialect": "duckdb",
        "tables": [],
        "files": [
            {
                "path": "/data/sales.csv",
                "format": "csv",
                "name": "sales",
                "inferred_types": {
                    "date": "DATE",
                    "amount": "DOUBLE",
                    "quantity": "INTEGER"
                }
            }
        ],
        "question": "Calculate monthly revenue from the sales file"
    }

    result = generate_sql(request)

    print(f"Generated SQL:\n{result['sql']}\n")
    print(f"File handling notes:\n")
    for note in result['execution_notes']:
        print(f"  - {note}")


# Example 4: PostgreSQL with custom metrics
def example_postgres_metrics():
    """PostgreSQL query with custom metric definitions."""
    print("\n=== Example 4: PostgreSQL with Custom Metrics ===\n")

    request = {
        "dialect": "postgres",
        "schema": "public",
        "tables": [
            {
                "name": "order_lines",
                "columns": [
                    {"name": "line_id", "type": "INTEGER"},
                    {"name": "order_id", "type": "INTEGER"},
                    {"name": "quantity", "type": "INTEGER"},
                    {"name": "unit_price", "type": "NUMERIC"},
                    {"name": "discount_pct", "type": "NUMERIC"}
                ]
            }
        ],
        "constraints": {
            "metric_definitions": {
                "net_revenue": "SUM(quantity * unit_price * (1 - discount_pct))",
                "avg_discount": "AVG(discount_pct)"
            }
        },
        "question": "Calculate net revenue and average discount"
    }

    result = generate_sql(request)

    print(f"Generated SQL:\n{result['sql']}\n")
    print(f"Parameters: {json.dumps(result['parameters'], indent=2)}\n")


# Example 5: Validate before generating
def example_validation():
    """Validate a request before generating SQL."""
    print("\n=== Example 5: Request Validation ===\n")

    request = {
        "dialect": "snowflake",
        "tables": [
            {"name": "table1", "columns": [{"name": "id", "type": "INTEGER"}]},
            {"name": "table2", "columns": [{"name": "id", "type": "INTEGER"}]}
        ],
        "question": "Join both tables"
        # Missing join hints - should get a warning
    }

    validation = validate_request(request)

    print(f"Valid: {validation['valid']}")
    print(f"Tables: {validation['tables_count']}")
    print(f"Warnings:")
    for warning in validation['warnings']:
        print(f"  - {warning}")


# Example 6: List available dialects
def example_list_dialects():
    """List all supported SQL dialects."""
    print("\n=== Example 6: Supported Dialects ===\n")

    dialects_info = list_supported_dialects()

    print("Supported SQL dialects:\n")
    for dialect in dialects_info['dialects']:
        print(f"  • {dialect['name']}: {dialect['description']}")
        print(f"    File support: {dialect['file_support']}")
        print(f"    Features: {', '.join(dialect['features'][:2])}")
        print()


def main():
    """Run all examples."""
    print("=" * 70)
    print("Universal Text-to-SQL Agent - Usage Examples")
    print("=" * 70)

    try:
        # Check if API is running
        response = requests.get(f"{API_BASE_URL}/health")
        response.raise_for_status()
        print("\n✓ API is running and healthy\n")
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Error: API is not running at {API_BASE_URL}")
        print("  Please start the API with: uvicorn app.main:app --reload")
        return

    # Run examples
    try:
        example_list_dialects()
        example_snowflake_simple()
        example_databricks_joins()
        example_duckdb_csv()
        example_postgres_metrics()
        example_validation()

        print("\n" + "=" * 70)
        print("All examples completed successfully!")
        print("=" * 70 + "\n")

    except requests.exceptions.HTTPError as e:
        print(f"\n✗ API Error: {e}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")


if __name__ == "__main__":
    main()
