# Universal Text-to-SQL Agent

A production-grade agent that converts natural language questions into correct, efficient SQL for multiple database backends:

- **Snowflake**
- **Databricks (Spark SQL)**
- **Excel/CSV files via DuckDB**
- **Generic SQL** (Postgres, MySQL, SQL Server)

## Features

- Multi-dialect SQL generation with dialect-specific optimizations
- Smart query optimization (filter pushdown, CTE usage, deduplication)
- File-based data querying (CSV/Excel via DuckDB)
- Comprehensive validation and safety checks
- RESTful API with JSON input/output
- Extensive test coverage

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run the API Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

Interactive API docs: `http://localhost:8000/docs`

### Example API Request

```bash
curl -X POST "http://localhost:8000/nl2sql" \
  -H "Content-Type: application/json" \
  -d @examples/sample_requests.json
```

## API Usage

### POST /nl2sql

**Input Schema:**

```json
{
  "dialect": "snowflake | databricks | postgres | mysql | sqlserver | duckdb",
  "catalog": "optional catalog/database name",
  "schema": "optional schema name",
  "tables": [
    {
      "name": "table_name",
      "description": "what this table contains",
      "columns": [
        {
          "name": "column_name",
          "type": "data_type",
          "description": "semantic meaning",
          "sample_values": ["example1", "example2"]
        }
      ],
      "rowcount_estimate": 100000
    }
  ],
  "constraints": {
    "time_range": "last_90_days | YYYY-MM-DD..YYYY-MM-DD",
    "filters": ["human-readable filter expressions"],
    "join_hints": ["table1.col -> table2.col"],
    "metric_definitions": {
      "metric_name": "SQL expression"
    }
  },
  "files": [
    {
      "path": "/path/to/file.csv",
      "format": "csv | xlsx",
      "name": "logical_table_name"
    }
  ],
  "question": "natural language question"
}
```

**Output Schema:**

```json
{
  "sql": "generated SQL query",
  "dialect": "target dialect",
  "execution_notes": ["implementation notes"],
  "parameters": {
    "named_params": {},
    "safe_limits": {}
  },
  "validation_checks": ["validation points"],
  "explain": "rationale for the SQL structure"
}
```

## Architecture

```
app/
├── main.py                    # FastAPI application
├── core/
│   ├── models.py             # Pydantic models for I/O
│   ├── sql_generator.py      # Main SQL generation logic
│   └── dialect_handlers.py   # Dialect-specific implementations
└── utils/
    └── validators.py         # Validation utilities

tests/
├── test_snowflake.py         # Snowflake-specific tests
├── test_databricks.py        # Databricks-specific tests
├── test_duckdb.py           # DuckDB/file tests
└── test_generic.py          # Generic SQL tests

examples/
└── sample_requests.json     # Example requests
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific dialect tests
pytest tests/test_snowflake.py -v
```

## Dialect-Specific Features

### Snowflake
- `QUALIFY` for window function filters
- `DATEADD`, `IFF`, `TRY_TO_TIMESTAMP`
- Fully qualified names: `DATABASE.SCHEMA.TABLE`

### Databricks (Spark SQL)
- Unity Catalog support: `catalog.schema.table`
- `date_add`, `collect_set`
- Delta Lake optimizations

### DuckDB (for CSV/Excel)
- `read_csv_auto()`, `read_excel()` for direct file querying
- Automatic type inference
- Fast local analytics

### Generic SQL
- ANSI SQL standard compliance
- Portable across Postgres, MySQL, SQL Server

## Safety & Best Practices

- **SELECT-only**: No DML operations (INSERT/UPDATE/DELETE)
- **Explicit joins**: No accidental cross joins
- **Null handling**: Explicit COALESCE/IFNULL
- **Performance**: Filter pushdown, column pruning
- **Validation**: Comprehensive checks before execution

## Examples

See `examples/` directory for full request/response examples for each dialect.

## License

MIT
