# Quick Start Guide

Get up and running with the Universal Text-to-SQL Agent in 5 minutes.

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

1. **Clone or download the repository**

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

## Start the API Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## Test the API

### Option 1: Interactive API Docs

Open your browser and go to: `http://localhost:8000/docs`

This provides an interactive Swagger UI where you can test all endpoints.

### Option 2: curl

```bash
# Simple Snowflake query
curl -X POST "http://localhost:8000/nl2sql" \
  -H "Content-Type: application/json" \
  -d '{
    "dialect": "snowflake",
    "schema": "ANALYTICS",
    "tables": [{
      "name": "orders",
      "columns": [
        {"name": "order_id", "type": "INTEGER"},
        {"name": "total_amount", "type": "DECIMAL"},
        {"name": "order_date", "type": "DATE"}
      ]
    }],
    "constraints": {
      "time_range": "last_90_days"
    },
    "question": "What is the total order amount in the last 90 days?"
  }'
```

### Option 3: Python Script

```bash
# First, make sure the API is running
python examples/usage_example.py
```

## Run Tests

```bash
# Run all tests
./run_tests.sh

# Run specific test suite
./run_tests.sh snowflake
./run_tests.sh databricks
./run_tests.sh duckdb

# Run with coverage report
./run_tests.sh coverage
```

## Example Requests

See `examples/sample_requests.json` for comprehensive examples covering:

- **Snowflake**: Complex multi-table queries with metrics
- **Databricks**: Time-series analysis with Unity Catalog
- **DuckDB**: CSV/Excel file querying
- **PostgreSQL**: Custom metric calculations
- **MySQL**: Simple aggregations
- **SQL Server**: TOP N queries

## Common Use Cases

### 1. Query a CSV file

```json
{
  "dialect": "duckdb",
  "files": [{
    "path": "/path/to/your/data.csv",
    "format": "csv",
    "name": "mydata"
  }],
  "question": "Show me the top 10 rows"
}
```

### 2. Aggregate with time filter

```json
{
  "dialect": "snowflake",
  "tables": [{
    "name": "sales",
    "columns": [
      {"name": "sale_date", "type": "DATE"},
      {"name": "amount", "type": "DECIMAL"}
    ]
  }],
  "constraints": {
    "time_range": "last_30_days"
  },
  "question": "What is the total sales in the last 30 days?"
}
```

### 3. Join multiple tables

```json
{
  "dialect": "databricks",
  "tables": [
    {
      "name": "orders",
      "columns": [
        {"name": "order_id", "type": "BIGINT"},
        {"name": "customer_id", "type": "BIGINT"}
      ]
    },
    {
      "name": "customers",
      "columns": [
        {"name": "customer_id", "type": "BIGINT"},
        {"name": "name", "type": "STRING"}
      ]
    }
  ],
  "constraints": {
    "join_hints": ["orders.customer_id -> customers.customer_id"]
  },
  "question": "Show orders with customer names"
}
```

## API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /dialects` - List supported dialects
- `POST /nl2sql` - Generate SQL from natural language
- `POST /nl2sql/validate` - Validate request structure

## Troubleshooting

### Port already in use

If port 8000 is already in use, specify a different port:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Import errors

Make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

### Tests failing

Install test dependencies:

```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

## Next Steps

- Read the [full README](README.md) for detailed documentation
- Explore [example requests](examples/sample_requests.json)
- Check out the [usage examples](examples/usage_example.py)
- Contribute improvements (see CONTRIBUTING.md)

## Support

For issues or questions:
- Check the API docs at `/docs`
- Review examples in the `examples/` directory
- Open an issue on GitHub
