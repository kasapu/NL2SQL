"""
Dialect-specific SQL generation handlers.

Each dialect handler knows how to format SQL for its specific database engine.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re


class BaseDialectHandler:
    """Base class for dialect-specific SQL formatting."""

    def __init__(self, catalog: Optional[str] = None, schema: Optional[str] = None):
        self.catalog = catalog
        self.schema = schema

    def qualify_table(self, table_name: str) -> str:
        """Fully qualify a table name based on catalog/schema."""
        # If already fully qualified, return as-is
        if '.' in table_name:
            return table_name

        parts = []
        if self.catalog:
            parts.append(self.catalog)
        if self.schema:
            parts.append(self.schema)
        parts.append(table_name)

        return '.'.join(parts) if len(parts) > 1 else table_name

    def format_date_filter(self, time_range: str) -> Tuple[Optional[str], Dict[str, str]]:
        """
        Convert time_range to SQL filter expression.
        Returns (filter_sql, parameters_dict)
        """
        if not time_range:
            return None, {}

        # Handle "last_N_days" pattern
        if time_range.startswith("last_") and time_range.endswith("_days"):
            days = int(time_range.replace("last_", "").replace("_days", ""))
            return self._format_last_n_days(days), {"days_back": str(days)}

        # Handle date range "YYYY-MM-DD..YYYY-MM-DD"
        if ".." in time_range:
            start, end = time_range.split("..")
            return self._format_date_range(start.strip(), end.strip()), {
                "start_date": start.strip(),
                "end_date": end.strip()
            }

        return None, {}

    def _format_last_n_days(self, days: int) -> str:
        """Format 'last N days' filter - override in subclasses."""
        raise NotImplementedError()

    def _format_date_range(self, start_date: str, end_date: str) -> str:
        """Format date range filter - override in subclasses."""
        raise NotImplementedError()

    def format_limit(self, limit: int) -> str:
        """Format LIMIT clause."""
        return f"LIMIT {limit}"

    def escape_identifier(self, identifier: str) -> str:
        """Escape an identifier (table/column name)."""
        return identifier

    def coalesce_function(self) -> str:
        """Return the COALESCE function name."""
        return "COALESCE"

    def current_date_function(self) -> str:
        """Return current date function."""
        return "CURRENT_DATE()"


class SnowflakeDialectHandler(BaseDialectHandler):
    """Snowflake-specific SQL formatting."""

    def _format_last_n_days(self, days: int) -> str:
        return f"DATEADD(day, -{days}, CURRENT_DATE())"

    def _format_date_range(self, start_date: str, end_date: str) -> str:
        return f"TRY_TO_DATE('{start_date}') AND TRY_TO_DATE('{end_date}')"

    def current_date_function(self) -> str:
        return "CURRENT_DATE()"

    def cast_to_type(self, expression: str, target_type: str) -> str:
        """Snowflake-style casting using :: operator."""
        return f"{expression}::{target_type}"


class DatabricksDialectHandler(BaseDialectHandler):
    """Databricks (Spark SQL) specific formatting."""

    def qualify_table(self, table_name: str) -> str:
        """Qualify table with backticks if needed."""
        qualified = super().qualify_table(table_name)
        # Add backticks for special characters or reserved words
        if ' ' in qualified or '-' in qualified:
            return f"`{qualified}`"
        return qualified

    def _format_last_n_days(self, days: int) -> str:
        return f"date_add(current_date(), -{days})"

    def _format_date_range(self, start_date: str, end_date: str) -> str:
        return f"to_date('{start_date}') AND to_date('{end_date}')"

    def current_date_function(self) -> str:
        return "current_date()"


class DuckDBDialectHandler(BaseDialectHandler):
    """DuckDB-specific formatting for CSV/Excel file queries."""

    def _format_last_n_days(self, days: int) -> str:
        return f"CURRENT_DATE - INTERVAL '{days}' DAY"

    def _format_date_range(self, start_date: str, end_date: str) -> str:
        return f"DATE '{start_date}' AND DATE '{end_date}'"

    def format_file_read(self, path: str, file_format: str, name: str) -> str:
        """Generate DuckDB file reading SQL."""
        if file_format == "csv":
            return f"SELECT * FROM read_csv_auto('{path}')"
        elif file_format == "xlsx":
            return f"SELECT * FROM read_excel('{path}')"
        else:
            raise ValueError(f"Unsupported file format: {file_format}")


class PostgresDialectHandler(BaseDialectHandler):
    """PostgreSQL-specific formatting."""

    def _format_last_n_days(self, days: int) -> str:
        return f"CURRENT_DATE - INTERVAL '{days} days'"

    def _format_date_range(self, start_date: str, end_date: str) -> str:
        return f"DATE '{start_date}' AND DATE '{end_date}'"

    def escape_identifier(self, identifier: str) -> str:
        """Use double quotes for identifiers."""
        if identifier.isupper() or ' ' in identifier:
            return f'"{identifier}"'
        return identifier


class MySQLDialectHandler(BaseDialectHandler):
    """MySQL-specific formatting."""

    def _format_last_n_days(self, days: int) -> str:
        return f"DATE_SUB(CURRENT_DATE, INTERVAL {days} DAY)"

    def _format_date_range(self, start_date: str, end_date: str) -> str:
        return f"'{start_date}' AND '{end_date}'"

    def escape_identifier(self, identifier: str) -> str:
        """Use backticks for identifiers."""
        return f"`{identifier}`"

    def format_limit(self, limit: int) -> str:
        return f"LIMIT {limit}"


class SQLServerDialectHandler(BaseDialectHandler):
    """SQL Server-specific formatting."""

    def _format_last_n_days(self, days: int) -> str:
        return f"DATEADD(day, -{days}, GETDATE())"

    def _format_date_range(self, start_date: str, end_date: str) -> str:
        return f"CAST('{start_date}' AS DATE) AND CAST('{end_date}' AS DATE)"

    def escape_identifier(self, identifier: str) -> str:
        """Use square brackets for identifiers."""
        return f"[{identifier}]"

    def format_limit(self, limit: int) -> str:
        """SQL Server uses TOP instead of LIMIT."""
        return f"TOP {limit}"

    def current_date_function(self) -> str:
        return "GETDATE()"


def get_dialect_handler(dialect: str, catalog: Optional[str] = None, schema: Optional[str] = None) -> BaseDialectHandler:
    """Factory function to get the appropriate dialect handler."""
    handlers = {
        "snowflake": SnowflakeDialectHandler,
        "databricks": DatabricksDialectHandler,
        "duckdb": DuckDBDialectHandler,
        "postgres": PostgresDialectHandler,
        "mysql": MySQLDialectHandler,
        "sqlserver": SQLServerDialectHandler,
    }

    handler_class = handlers.get(dialect.lower())
    if not handler_class:
        raise ValueError(f"Unsupported dialect: {dialect}")

    return handler_class(catalog=catalog, schema=schema)
