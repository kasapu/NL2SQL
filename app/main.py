"""
FastAPI application for Universal Text-to-SQL Agent.

Provides a REST API endpoint for converting natural language questions to SQL.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

from .core.models import SQLRequest, SQLResponse, ErrorResponse
from .core.sql_generator import generate_sql

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Universal Text-to-SQL Agent",
    description="Convert natural language questions into SQL for multiple database dialects",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with API information."""
    return {
        "service": "Universal Text-to-SQL Agent",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "POST /nl2sql": "Convert natural language to SQL"
        }
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/nl2sql", response_model=SQLResponse)
async def generate_sql_endpoint(request: SQLRequest) -> SQLResponse:
    """
    Convert a natural language question into SQL.

    This endpoint accepts a structured request with:
    - Target database dialect
    - Available tables and their schemas
    - Optional constraints (time ranges, filters, join hints)
    - Optional file sources (CSV/Excel)
    - Natural language question

    Returns:
    - Generated SQL query
    - Execution notes and assumptions
    - Validation checks
    - Explanation of the SQL structure
    """
    try:
        logger.info(
            f"Received SQL generation request: dialect={request.dialect}, "
            f"question='{request.question[:100]}...'"
        )

        # Validate request
        if not request.tables and not request.files:
            raise HTTPException(
                status_code=400,
                detail="Either tables or files must be provided"
            )

        # Generate SQL
        response = generate_sql(request)

        logger.info(f"Successfully generated SQL for dialect={request.dialect}")

        return response

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/nl2sql/validate")
async def validate_request(request: SQLRequest) -> Dict[str, Any]:
    """
    Validate a SQL generation request without generating SQL.

    Useful for checking if a request is well-formed before submission.
    """
    try:
        validation_results = {
            "valid": True,
            "dialect": request.dialect,
            "tables_count": len(request.tables),
            "files_count": len(request.files) if request.files else 0,
            "has_constraints": request.constraints is not None,
            "question_length": len(request.question),
            "warnings": []
        }

        # Check for potential issues
        if not request.tables and not request.files:
            validation_results["valid"] = False
            validation_results["warnings"].append(
                "Either tables or files must be provided"
            )

        if len(request.question) < 10:
            validation_results["warnings"].append(
                "Question seems very short, consider providing more detail"
            )

        if request.tables and len(request.tables) > 1:
            if not request.constraints or not request.constraints.join_hints:
                validation_results["warnings"].append(
                    "Multiple tables detected but no join hints provided - joins may be inferred"
                )

        if request.files and request.dialect != "duckdb":
            validation_results["warnings"].append(
                f"Files provided but dialect is {request.dialect}. Consider using 'duckdb' for file queries"
            )

        return validation_results

    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/dialects")
async def list_dialects() -> Dict[str, Any]:
    """
    List all supported SQL dialects and their capabilities.
    """
    return {
        "dialects": [
            {
                "name": "snowflake",
                "description": "Snowflake Data Warehouse",
                "features": [
                    "QUALIFY for window filters",
                    "DATEADD, IFF, TRY_TO_TIMESTAMP",
                    ":: casting operator",
                    "Full qualification: DATABASE.SCHEMA.TABLE"
                ],
                "file_support": False
            },
            {
                "name": "databricks",
                "description": "Databricks (Spark SQL)",
                "features": [
                    "Unity Catalog support",
                    "date_add, collect_set",
                    "Delta Lake optimizations",
                    "Backtick identifier quoting"
                ],
                "file_support": False
            },
            {
                "name": "duckdb",
                "description": "DuckDB (for CSV/Excel)",
                "features": [
                    "read_csv_auto() for CSV files",
                    "read_excel() for Excel files",
                    "Fast local analytics",
                    "Automatic type inference"
                ],
                "file_support": True
            },
            {
                "name": "postgres",
                "description": "PostgreSQL",
                "features": [
                    "Full ANSI SQL compliance",
                    "DATE_TRUNC for date operations",
                    "Rich data type support"
                ],
                "file_support": False
            },
            {
                "name": "mysql",
                "description": "MySQL",
                "features": [
                    "DATE_SUB for date operations",
                    "Backtick identifier quoting",
                    "LIMIT clause"
                ],
                "file_support": False
            },
            {
                "name": "sqlserver",
                "description": "Microsoft SQL Server",
                "features": [
                    "TOP instead of LIMIT",
                    "DATEADD for date operations",
                    "Square bracket identifiers",
                    "GETDATE() for current date"
                ],
                "file_support": False
            }
        ]
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
