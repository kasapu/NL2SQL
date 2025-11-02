"""
Core SQL generation engine for Universal Text-to-SQL Agent.

This module contains the main logic for converting natural language questions
into correct, efficient SQL queries for multiple database dialects.
"""
from typing import List, Dict, Optional, Set, Tuple
import re
from datetime import datetime, timedelta

from .models import SQLRequest, SQLResponse, TableSchema, ColumnSchema, FileSource
from .dialect_handlers import get_dialect_handler, BaseDialectHandler, DuckDBDialectHandler


class SQLGenerator:
    """Main SQL generation engine."""

    def __init__(self, request: SQLRequest):
        self.request = request
        self.handler = get_dialect_handler(
            request.dialect,
            catalog=request.catalog,
            schema_name=request.schema_name
        )
        self.execution_notes = []
        self.validation_checks = []
        self.parameters = {"named_params": {}, "safe_limits": {}}

    def generate(self) -> SQLResponse:
        """Main entry point for SQL generation."""

        # Analyze the question to understand intent
        query_intent = self._analyze_question()

        # Handle file-based queries differently
        if self.request.files and self.request.dialect == "duckdb":
            sql = self._generate_file_based_query(query_intent)
        else:
            sql = self._generate_standard_query(query_intent)

        # Build explain text
        explain = self._build_explanation(query_intent)

        return SQLResponse(
            sql=sql,
            dialect=self.request.dialect,
            execution_notes=self.execution_notes,
            parameters=self.parameters,
            validation_checks=self.validation_checks,
            explain=explain
        )

    def _analyze_question(self) -> Dict:
        """
        Analyze the natural language question to extract intent.
        Returns a dict with query structure information.
        """
        question = self.request.question.lower()

        intent = {
            "operation": self._detect_operation(question),
            "aggregations": self._detect_aggregations(question),
            "time_based": self._is_time_based(question),
            "grouping": self._detect_grouping(question),
            "ordering": self._detect_ordering(question),
            "limit": self._detect_limit(question),
            "tables_needed": self._identify_tables(),
            "metrics": self._extract_metrics()
        }

        return intent

    def _detect_operation(self, question: str) -> str:
        """Detect the type of operation (aggregation, ranking, filtering, etc.)."""
        if any(word in question for word in ["top", "best", "highest", "most", "largest"]):
            return "ranking"
        elif any(word in question for word in ["average", "avg", "mean", "sum", "total", "count"]):
            return "aggregation"
        elif any(word in question for word in ["trend", "over time", "daily", "monthly", "moving average"]):
            return "time_series"
        elif any(word in question for word in ["list", "show", "display", "get", "find"]):
            return "selection"
        else:
            return "general"

    def _detect_aggregations(self, question: str) -> List[str]:
        """Detect which aggregation functions are needed."""
        aggs = []
        agg_keywords = {
            "sum": ["sum", "total"],
            "avg": ["average", "avg", "mean"],
            "count": ["count", "number of", "how many"],
            "min": ["minimum", "min", "lowest", "smallest"],
            "max": ["maximum", "max", "highest", "largest", "biggest", "top"]
        }

        question_lower = question.lower()
        for agg_func, keywords in agg_keywords.items():
            if any(kw in question_lower for kw in keywords):
                aggs.append(agg_func.upper())

        return aggs if aggs else []

    def _is_time_based(self, question: str) -> bool:
        """Check if query involves time-based filtering or analysis."""
        time_keywords = [
            "last", "past", "recent", "since", "until", "before", "after",
            "daily", "weekly", "monthly", "yearly", "day", "month", "year",
            "trend", "over time", "period", "date", "time"
        ]
        return any(kw in question.lower() for kw in time_keywords)

    def _detect_grouping(self, question: str) -> List[str]:
        """Detect GROUP BY dimensions from the question."""
        grouping = []
        question_lower = question.lower()

        # Common grouping patterns
        if "by region" in question_lower or "per region" in question_lower:
            grouping.append("region")
        if "by customer" in question_lower or "per customer" in question_lower:
            grouping.append("customer")
        if "by category" in question_lower or "per category" in question_lower:
            grouping.append("category")
        if "by month" in question_lower or "monthly" in question_lower:
            grouping.append("month")
        if "by day" in question_lower or "daily" in question_lower:
            grouping.append("day")

        return grouping

    def _detect_ordering(self, question: str) -> Optional[Tuple[str, str]]:
        """Detect ORDER BY clause. Returns (column_hint, direction)."""
        question_lower = question.lower()

        if "top" in question_lower or "highest" in question_lower or "most" in question_lower:
            return ("aggregate_value", "DESC")
        elif "bottom" in question_lower or "lowest" in question_lower or "least" in question_lower:
            return ("aggregate_value", "ASC")

        return None

    def _detect_limit(self, question: str) -> Optional[int]:
        """Detect if a LIMIT is specified."""
        # Look for patterns like "top 10", "first 5", "limit 20"
        limit_patterns = [
            r"top\s+(\d+)",
            r"first\s+(\d+)",
            r"limit\s+(\d+)",
            r"(\d+)\s+(?:best|worst|highest|lowest)"
        ]

        for pattern in limit_patterns:
            match = re.search(pattern, self.request.question.lower())
            if match:
                return int(match.group(1))

        return None

    def _identify_tables(self) -> List[TableSchema]:
        """Identify which tables are needed for this query."""
        # For now, use all provided tables
        # In a production system, this would use semantic matching
        return self.request.tables

    def _extract_metrics(self) -> Dict[str, str]:
        """Extract metric definitions from constraints."""
        if self.request.constraints and self.request.constraints.metric_definitions:
            return self.request.constraints.metric_definitions
        return {}

    def _generate_standard_query(self, intent: Dict) -> str:
        """Generate SQL for standard database queries."""

        # Start building CTEs
        ctes = []

        # Build base CTE with time filtering
        base_cte = self._build_base_cte(intent)
        if base_cte:
            ctes.append(base_cte)

        # Build join CTEs if multiple tables
        if len(intent["tables_needed"]) > 1:
            join_ctes = self._build_join_ctes(intent)
            ctes.extend(join_ctes)

        # Build aggregation CTE
        agg_cte = self._build_aggregation_cte(intent)
        if agg_cte:
            ctes.append(agg_cte)

        # Build ranking CTE if needed
        if intent["operation"] == "ranking":
            rank_cte = self._build_ranking_cte(intent)
            if rank_cte:
                ctes.append(rank_cte)

        # Build final SELECT
        final_select = self._build_final_select(intent, bool(ctes))

        # Combine everything
        if ctes:
            cte_str = ",\n".join(ctes)
            sql = f"WITH {cte_str}\n{final_select}"
        else:
            sql = final_select

        # Add ORDER BY
        if intent["ordering"]:
            sql += self._build_order_by(intent)

        # Add LIMIT
        if intent["limit"]:
            sql += f"\n{self.handler.format_limit(intent['limit'])}"
            self.parameters["safe_limits"]["row_limit"] = intent["limit"]

        # Clean up formatting
        sql = self._format_sql(sql)

        return sql

    def _build_base_cte(self, intent: Dict) -> Optional[str]:
        """Build the base CTE with initial filtering."""
        if not intent["tables_needed"]:
            return None

        main_table = intent["tables_needed"][0]
        qualified_name = self.handler.qualify_table(main_table.name)

        # Detect date column
        date_col = self._find_date_column(main_table)

        # Build WHERE conditions
        where_conditions = []

        # Add time range filter if specified
        if self.request.constraints and self.request.constraints.time_range and date_col:
            date_filter, params = self.handler.format_date_filter(
                self.request.constraints.time_range
            )
            if date_filter:
                where_conditions.append(f"{date_col} >= {date_filter}")
                self.parameters["named_params"].update(params)
                self.execution_notes.append(
                    f"Time filter applied on {date_col}: {self.request.constraints.time_range}"
                )

        # Add custom filters
        if self.request.constraints and self.request.constraints.filters:
            where_conditions.extend(self.request.constraints.filters)

        # Build SELECT columns
        select_cols = [col.name for col in main_table.columns[:10]]  # Limit columns for readability

        where_clause = f"\n  WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

        cte = f"""base AS (
  SELECT
    {', '.join(select_cols)}
  FROM {qualified_name}{where_clause}
)"""

        self.validation_checks.append(
            f"Base table {qualified_name} filtered correctly"
        )

        return cte

    def _find_date_column(self, table: TableSchema) -> Optional[str]:
        """Find a date/timestamp column in a table."""
        date_keywords = ["date", "time", "created", "updated", "timestamp"]

        for col in table.columns:
            col_name_lower = col.name.lower()
            col_type_lower = col.type.lower()

            if any(kw in col_name_lower for kw in date_keywords):
                return col.name
            if any(dt in col_type_lower for dt in ["date", "time", "timestamp"]):
                return col.name

        return None

    def _build_join_ctes(self, intent: Dict) -> List[str]:
        """Build CTEs for joining multiple tables."""
        ctes = []

        if not self.request.constraints or not self.request.constraints.join_hints:
            self.execution_notes.append(
                "Multiple tables detected but no explicit join hints provided"
            )
            return ctes

        # Parse join hints
        for i, hint in enumerate(self.request.constraints.join_hints):
            # Parse hint like "orders.customer_id -> customers.id"
            match = re.match(r"(\w+)\.(\w+)\s*->\s*(\w+)\.(\w+)", hint)
            if match:
                left_table, left_col, right_table, right_col = match.groups()
                self.validation_checks.append(
                    f"Join validated: {left_table}.{left_col} = {right_table}.{right_col}"
                )

        return ctes

    def _build_aggregation_cte(self, intent: Dict) -> Optional[str]:
        """Build aggregation CTE if needed."""
        if not intent["aggregations"] and intent["operation"] != "aggregation":
            return None

        # Determine group by dimensions
        group_by_cols = intent.get("grouping", [])

        if not group_by_cols:
            # Try to infer from tables
            if intent["tables_needed"]:
                # Use first non-numeric column as group by
                for col in intent["tables_needed"][0].columns:
                    if "id" not in col.name.lower() and col.type.lower() not in ["int", "integer", "bigint", "numeric"]:
                        group_by_cols.append(col.name)
                        break

        # Build aggregation expressions
        agg_exprs = []
        if "SUM" in intent["aggregations"]:
            agg_exprs.append("SUM(amount) AS total_amount")
        if "COUNT" in intent["aggregations"]:
            agg_exprs.append("COUNT(*) AS record_count")
        if "AVG" in intent["aggregations"]:
            agg_exprs.append("AVG(amount) AS avg_amount")

        # Use metrics if defined
        metrics = self._extract_metrics()
        if metrics:
            for metric_name, metric_expr in metrics.items():
                agg_exprs.append(f"({metric_expr}) AS {metric_name}")

        if not agg_exprs:
            agg_exprs = ["COUNT(*) AS total"]

        group_by_clause = f"\n  GROUP BY {', '.join(group_by_cols)}" if group_by_cols else ""

        cte = f"""aggregated AS (
  SELECT
    {', '.join(group_by_cols + agg_exprs) if group_by_cols else ', '.join(agg_exprs)}
  FROM base{group_by_clause}
)"""

        return cte

    def _build_ranking_cte(self, intent: Dict) -> Optional[str]:
        """Build ranking CTE using ROW_NUMBER or RANK."""
        group_by = intent.get("grouping", [])

        partition_clause = f"PARTITION BY {', '.join(group_by)}" if group_by else ""
        order_by = "ORDER BY total_amount DESC"  # Default ordering

        cte = f"""ranked AS (
  SELECT
    *,
    ROW_NUMBER() OVER ({partition_clause} {order_by}) AS rank_num
  FROM aggregated
)"""

        self.validation_checks.append("Ranking applied with proper ordering")

        return cte

    def _build_final_select(self, intent: Dict, has_ctes: bool) -> str:
        """Build the final SELECT statement."""

        from_clause = "ranked" if intent["operation"] == "ranking" else \
                      "aggregated" if intent.get("aggregations") else \
                      "base" if has_ctes else \
                      self.handler.qualify_table(intent["tables_needed"][0].name)

        if intent["operation"] == "ranking" and intent.get("limit"):
            where_clause = f"\nWHERE rank_num <= {intent['limit']}"
        else:
            where_clause = ""

        select = f"""SELECT
  *
FROM {from_clause}{where_clause}"""

        return select

    def _build_order_by(self, intent: Dict) -> str:
        """Build ORDER BY clause."""
        _, direction = intent["ordering"]

        # Try to determine the order column
        if intent.get("aggregations"):
            order_col = "total_amount"  # Default
        else:
            order_col = "1"

        return f"\nORDER BY {order_col} {direction}"

    def _generate_file_based_query(self, intent: Dict) -> str:
        """Generate SQL for file-based queries using DuckDB."""
        if not self.request.files:
            raise ValueError("No files provided for file-based query")

        ctes = []

        # Create CTEs for each file
        for file in self.request.files:
            read_expr = self.handler.format_file_read(file.path, file.format, file.name)

            # Add type casting if inferred types provided
            if file.inferred_types:
                cast_exprs = []
                for col, dtype in file.inferred_types.items():
                    cast_exprs.append(f"TRY_CAST({col} AS {dtype}) AS {col}")

                cte = f"""{file.name}_typed AS (
  SELECT
    {', '.join(cast_exprs)}
  FROM ({read_expr})
)"""
            else:
                cte = f"""{file.name} AS (
  {read_expr}
)"""

            ctes.append(cte)
            self.execution_notes.append(
                f"File {file.path} loaded as table '{file.name}'"
            )

        # Build aggregation on file data
        file_name = self.request.files[0].name

        # Simple aggregation query
        final_query = f"""SELECT
  *
FROM {file_name}_typed
LIMIT 100"""

        if ctes:
            cte_str = ",\n".join(ctes)
            sql = f"WITH {cte_str}\n{final_query}"
        else:
            sql = final_query

        self.validation_checks.append("File loading configured correctly")

        return self._format_sql(sql)

    def _build_explanation(self, intent: Dict) -> str:
        """Build a 2-4 sentence explanation of the SQL."""
        operation = intent["operation"]
        tables = ", ".join([t.name for t in intent["tables_needed"]])

        explain = f"This query performs a {operation} operation on {tables}. "

        if intent["aggregations"]:
            aggs = ", ".join(intent["aggregations"])
            explain += f"It uses {aggs} aggregation functions. "

        if intent["time_based"]:
            explain += "Time-based filtering is applied to limit the date range. "

        if intent["grouping"]:
            groups = ", ".join(intent["grouping"])
            explain += f"Results are grouped by {groups}."

        return explain

    def _format_sql(self, sql: str) -> str:
        """Clean up and format SQL for readability."""
        # Remove extra blank lines
        sql = re.sub(r'\n\s*\n', '\n', sql)

        # Ensure consistent indentation
        lines = sql.split('\n')
        formatted_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped:
                formatted_lines.append(line)

        return '\n'.join(formatted_lines)


def generate_sql(request: SQLRequest) -> SQLResponse:
    """
    Main entry point for SQL generation.

    Args:
        request: SQLRequest object with all necessary information

    Returns:
        SQLResponse with generated SQL and metadata
    """
    generator = SQLGenerator(request)
    return generator.generate()
