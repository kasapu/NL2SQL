"""
Pydantic models for Universal Text-to-SQL Agent input/output schemas.
"""
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field, validator


class ColumnSchema(BaseModel):
    """Metadata for a single column."""
    name: str = Field(..., description="Column name")
    type: str = Field(..., description="SQL data type")
    description: Optional[str] = Field(None, description="Semantic meaning of the column")
    sample_values: Optional[List[str]] = Field(None, description="Example values")


class TableSchema(BaseModel):
    """Metadata for a single table."""
    name: str = Field(..., description="Table name (qualified or unqualified)")
    description: Optional[str] = Field(None, description="What this table contains")
    columns: List[ColumnSchema] = Field(..., description="Column definitions")
    rowcount_estimate: Optional[int] = Field(None, description="Approximate row count")


class Constraints(BaseModel):
    """Query constraints and hints."""
    time_range: Optional[str] = Field(None, description="Time filter (e.g., 'last_90_days' or '2025-01-01..2025-03-31')")
    filters: Optional[List[str]] = Field(None, description="Human-readable filter expressions")
    join_hints: Optional[List[str]] = Field(None, description="Join key relationships (e.g., 'orders.customer_id -> customers.id')")
    metric_definitions: Optional[Dict[str, str]] = Field(None, description="Named metric formulas")


class FileSource(BaseModel):
    """External file source (CSV/Excel)."""
    path: str = Field(..., description="File path")
    format: Literal["csv", "xlsx"] = Field(..., description="File format")
    name: str = Field(..., description="Logical table name to use in queries")
    inferred_types: Optional[Dict[str, str]] = Field(None, description="Column name to type mapping")


class SQLRequest(BaseModel):
    """Input request for SQL generation."""
    dialect: Literal["snowflake", "databricks", "postgres", "mysql", "sqlserver", "duckdb"] = Field(
        ..., description="Target SQL dialect"
    )
    catalog: Optional[str] = Field(None, description="Catalog or database name")
    schema_name: Optional[str] = Field(None, alias="schema", description="Schema name")
    tables: List[TableSchema] = Field(..., description="Available tables and their schemas")
    constraints: Optional[Constraints] = Field(None, description="Query constraints and hints")
    files: Optional[List[FileSource]] = Field(None, description="External file sources")
    question: str = Field(..., description="Natural language question")

    class Config:
        populate_by_name = True

    @validator('tables')
    def validate_tables_not_empty(cls, v):
        if not v:
            raise ValueError("At least one table must be provided")
        return v


class SQLResponse(BaseModel):
    """Output response with generated SQL."""
    sql: str = Field(..., description="Generated SQL query")
    dialect: str = Field(..., description="Target dialect used")
    execution_notes: List[str] = Field(
        default_factory=list,
        description="Step-by-step execution instructions and assumptions"
    )
    parameters: Dict[str, Dict[str, any]] = Field(
        default_factory=dict,
        description="Named parameters and safe limits"
    )
    validation_checks: List[str] = Field(
        default_factory=list,
        description="Validation points (joins, filters, edge cases)"
    )
    explain: str = Field(..., description="2-4 sentence rationale mapping question to SQL")


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    clarifying_question: Optional[str] = Field(None, description="Question to resolve ambiguity")
