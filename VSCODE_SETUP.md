# VS Code Setup Guide for NL2SQL

This guide will help you set up and run the Universal Text-to-SQL Agent project locally in Visual Studio Code.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Opening the Project](#opening-the-project)
- [Setting up Python Environment](#setting-up-python-environment)
- [Installing Dependencies](#installing-dependencies)
- [Running the API Server](#running-the-api-server)
- [Testing the API](#testing-the-api)
- [Debugging](#debugging)
- [Running Tests](#running-tests)
- [VS Code Features](#vs-code-features)
- [Docker Setup (Alternative)](#docker-setup-alternative)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, make sure you have the following installed on your system:

1. **Visual Studio Code** - [Download here](https://code.visualstudio.com/)
2. **Python 3.8 or higher** - [Download here](https://www.python.org/downloads/)
3. **Git** - [Download here](https://git-scm.com/downloads)
4. **pip** - Usually comes with Python

Optional:
- **Docker** & **Docker Compose** - [Download here](https://www.docker.com/products/docker-desktop/) (for containerized setup)

## Initial Setup

### 1. Clone the Repository

Open your terminal and run:

```bash
git clone https://github.com/kasapu/NL2SQL.git
cd NL2SQL
```

### 2. Verify Python Installation

Check that Python is installed and accessible:

```bash
python --version
# or
python3 --version
```

You should see Python 3.8 or higher.

## Opening the Project

### Open in VS Code

There are several ways to open the project:

**Option 1: From Command Line**
```bash
cd NL2SQL
code .
```

**Option 2: From VS Code**
1. Launch VS Code
2. File → Open Folder...
3. Navigate to the `NL2SQL` directory and click "Open"

**Option 3: From File Explorer/Finder**
- Right-click on the `NL2SQL` folder
- Select "Open with Code"

### Install Recommended Extensions

When you first open the project, VS Code should prompt you to install recommended extensions. Click **"Install All"**.

If the prompt doesn't appear:
1. Open the Extensions view (Ctrl+Shift+X or Cmd+Shift+X on Mac)
2. Type `@recommended` in the search box
3. Install all workspace recommendations

**Essential Extensions:**
- **Python** (ms-python.python)
- **Pylance** (ms-python.vscode-pylance)
- **Black Formatter** (ms-python.black-formatter)
- **REST Client** (humao.rest-client) - for testing API endpoints

## Setting up Python Environment

### Create a Virtual Environment

Using VS Code's integrated terminal (Terminal → New Terminal or Ctrl+`):

**On Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### Select Python Interpreter

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) to open the Command Palette
2. Type: `Python: Select Interpreter`
3. Choose the interpreter from `.venv` (it should be listed first)
   - Should show something like: `Python 3.x.x ('.venv': venv)`

Alternatively, you can use the VS Code task:
1. Press `Ctrl+Shift+P`
2. Type: `Tasks: Run Task`
3. Select: `Create Virtual Environment`

## Installing Dependencies

With your virtual environment activated, install the required packages:

### Using VS Code Task (Recommended)

1. Press `Ctrl+Shift+P` to open Command Palette
2. Type: `Tasks: Run Task`
3. Select: `Install Dependencies`

### Using Terminal

```bash
pip install -r requirements.txt
```

**Note:** Some optional database connectors (like `snowflake-connector-python`) may require additional system dependencies. If you encounter build errors and don't need that specific connector, you can install the core dependencies separately:

```bash
pip install fastapi uvicorn pydantic pydantic-settings pytest pytest-asyncio pytest-cov httpx python-dateutil
```

## Running the API Server

### Method 1: Using VS Code Task

1. Press `Ctrl+Shift+P`
2. Type: `Tasks: Run Task`
3. Select: `Start API Server`

The server will start in a dedicated terminal panel.

### Method 2: Using Debug Configuration

1. Go to the Debug view (Ctrl+Shift+D or Cmd+Shift+D on Mac)
2. Select **"Python: FastAPI Server"** from the dropdown
3. Press F5 or click the green play button

This method allows you to set breakpoints and debug the server.

### Method 3: Using Terminal

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Verify Server is Running

The API server should now be running at:
- **API Base:** http://localhost:8000
- **Interactive Docs:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

You should see output like:
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## Testing the API

### Method 1: Interactive API Docs (Swagger UI)

1. Open your browser
2. Navigate to: http://localhost:8000/docs
3. Click on any endpoint (e.g., `POST /nl2sql`)
4. Click **"Try it out"**
5. Enter your request body
6. Click **"Execute"**

### Method 2: Using REST Client Extension

If you installed the REST Client extension:

1. Create a new file: `test-api.http`
2. Add the following content:

```http
### Health Check
GET http://localhost:8000/health

### List Supported Dialects
GET http://localhost:8000/dialects

### Generate SQL - Simple Snowflake Query
POST http://localhost:8000/nl2sql
Content-Type: application/json

{
  "dialect": "snowflake",
  "schema": "ANALYTICS",
  "tables": [{
    "name": "orders",
    "description": "Customer orders",
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
}

### Validate Request
POST http://localhost:8000/nl2sql/validate
Content-Type: application/json

{
  "dialect": "snowflake",
  "tables": [],
  "question": "test"
}
```

3. Click **"Send Request"** above any request

### Method 3: Using Python Examples

Make sure the server is running, then:

1. Run the usage example script:

**Using VS Code Task:**
- Press `Ctrl+Shift+P`
- Type: `Tasks: Run Task`
- Select: `Run Usage Examples`

**Using Terminal:**
```bash
python examples/usage_example.py
```

**Using Debug:**
- Go to Debug view (Ctrl+Shift+D)
- Select **"Python: Run Usage Examples"**
- Press F5

### Method 4: Using curl

```bash
curl -X POST "http://localhost:8000/nl2sql" \
  -H "Content-Type: application/json" \
  -d '{
    "dialect": "snowflake",
    "schema": "ANALYTICS",
    "tables": [{
      "name": "orders",
      "columns": [
        {"name": "order_id", "type": "INTEGER"},
        {"name": "total_amount", "type": "DECIMAL"}
      ]
    }],
    "question": "What is the total order amount?"
  }'
```

## Debugging

The project includes several pre-configured debug configurations:

### Debug the API Server

1. Set breakpoints in your code (click to the left of line numbers)
2. Go to Debug view (Ctrl+Shift+D)
3. Select **"Python: FastAPI Server"**
4. Press F5
5. Make API requests - execution will pause at breakpoints

### Debug Tests

1. Open a test file (e.g., `tests/test_api.py`)
2. Set breakpoints
3. Go to Debug view
4. Select **"Python: Pytest Current File"** or **"Python: Pytest All Tests"**
5. Press F5

### Debug a Python File

1. Open any Python file
2. Set breakpoints
3. Go to Debug view
4. Select **"Python: Current File"**
5. Press F5

## Running Tests

### Using VS Code Testing UI

1. Open the Testing view (flask icon in sidebar or Ctrl+Shift+T)
2. Click the refresh icon to discover tests
3. Run all tests or individual tests by clicking the play button
4. View results inline

### Using Tasks

**Run All Tests:**
1. Press `Ctrl+Shift+P`
2. Type: `Tasks: Run Task`
3. Select: `Run All Tests`

**Run with Coverage:**
1. Press `Ctrl+Shift+P`
2. Type: `Tasks: Run Task`
3. Select: `Run Tests with Coverage`

### Using Terminal

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_api.py -v

# Run with coverage
pytest --cov=app --cov-report=html tests/

# View coverage report
# Open htmlcov/index.html in browser
```

### Using Debug Configurations

1. Go to Debug view (Ctrl+Shift+D)
2. Select **"Python: Pytest All Tests"** or **"Python: Pytest Current File"**
3. Press F5

## VS Code Features

### Integrated Terminal

- Open: `Ctrl+`` (backtick) or Terminal → New Terminal
- Split terminal: Click the split icon
- Multiple terminals: Create new terminal instances
- Auto-activates virtual environment

### Code Navigation

- **Go to Definition:** F12 or Ctrl+Click
- **Find References:** Shift+F12
- **Symbol Search:** Ctrl+Shift+O
- **File Search:** Ctrl+P
- **Global Search:** Ctrl+Shift+F

### Code Formatting

Code is automatically formatted on save (using Black).

**Manual formatting:**
- Format entire file: Shift+Alt+F (or Shift+Option+F on Mac)
- Format selection: Ctrl+K Ctrl+F

**Format using task:**
1. Press `Ctrl+Shift+P`
2. Type: `Tasks: Run Task`
3. Select: `Format Code (Black)`

### IntelliSense & Auto-completion

- Trigger: Start typing or press Ctrl+Space
- Parameter hints: Ctrl+Shift+Space
- Quick fixes: Ctrl+. when on an error

### Git Integration

- **Source Control View:** Ctrl+Shift+G
- **Stage changes:** Click + next to files
- **Commit:** Enter message and press Ctrl+Enter
- **View diff:** Click on modified file
- **Git History:** Install GitLens extension (recommended)

### File Explorer

- Toggle: Ctrl+Shift+E
- New file: Right-click folder → New File
- Search in folder: Right-click → Find in Folder

## Docker Setup (Alternative)

If you prefer to run the application in Docker:

### Using VS Code Tasks

**Build Docker Image:**
1. Press `Ctrl+Shift+P`
2. Type: `Tasks: Run Task`
3. Select: `Docker: Build Image`

**Start Services:**
1. Press `Ctrl+Shift+P`
2. Type: `Tasks: Run Task`
3. Select: `Docker: Start Services`

**View Logs:**
1. Press `Ctrl+Shift+P`
2. Type: `Tasks: Run Task`
3. Select: `Docker: View Logs`

**Stop Services:**
1. Press `Ctrl+Shift+P`
2. Type: `Tasks: Run Task`
3. Select: `Docker: Stop Services`

### Using Terminal

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild
docker-compose up -d --build
```

The API will be available at http://localhost:8000

### Using Docker Extension

If you have the Docker extension installed:
1. Open Docker view (click whale icon in sidebar)
2. Right-click on compose files
3. Select "Compose Up" or "Compose Down"

## Troubleshooting

### Python Interpreter Not Found

**Problem:** VS Code can't find Python
**Solution:**
1. Make sure Python is installed: `python --version`
2. Press Ctrl+Shift+P → "Python: Select Interpreter"
3. Browse to your Python installation if not listed

### Virtual Environment Not Activating

**Problem:** Terminal doesn't activate .venv automatically
**Solution:**
1. Close and reopen VS Code
2. Or manually activate:
   - Linux/Mac: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate`

### Module Not Found Errors

**Problem:** `ModuleNotFoundError: No module named 'fastapi'`
**Solution:**
1. Ensure virtual environment is activated (you should see `(.venv)` in terminal)
2. Install dependencies: `pip install -r requirements.txt`
3. Verify: `pip list | grep fastapi`

### Port Already in Use

**Problem:** `Address already in use` error
**Solution:**
1. Find process using port 8000:
   - Linux/Mac: `lsof -i :8000`
   - Windows: `netstat -ano | findstr :8000`
2. Kill the process or use a different port:
   ```bash
   uvicorn app.main:app --port 8080 --reload
   ```

### Import Errors in Tests

**Problem:** Tests can't import app modules
**Solution:**
1. Make sure you're in the project root directory
2. Set PYTHONPATH if needed:
   ```bash
   export PYTHONPATH="${PYTHONPATH}:${PWD}"
   ```
3. Or run tests with: `python -m pytest tests/`

### Dependency Installation Fails

**Problem:** Some packages fail to install (especially snowflake-connector-python)
**Solution:**
1. Install system dependencies (Linux):
   ```bash
   sudo apt-get update
   sudo apt-get install gcc g++ python3-dev
   ```
2. Or install core dependencies only:
   ```bash
   pip install fastapi uvicorn pydantic pytest httpx
   ```
3. Skip optional database connectors if not needed

### Tests Not Discovered

**Problem:** No tests appear in Testing view
**Solution:**
1. Ensure pytest is installed: `pip install pytest pytest-asyncio`
2. Refresh tests: Click refresh icon in Testing view
3. Check test configuration in settings.json
4. Check pytest.ini file exists in project root

### Formatting Not Working

**Problem:** Code doesn't format on save
**Solution:**
1. Install Black formatter: `pip install black`
2. Check that "editor.formatOnSave" is true in settings
3. Verify Black is selected as formatter: Ctrl+Shift+P → "Format Document With..." → Black

### Docker Issues

**Problem:** Docker commands fail
**Solution:**
1. Ensure Docker is installed and running
2. Check Docker daemon: `docker ps`
3. On Linux, add user to docker group:
   ```bash
   sudo usermod -aG docker $USER
   ```
4. Log out and back in

### API Returns Errors

**Problem:** API requests return 500 errors
**Solution:**
1. Check server logs in terminal
2. Verify request format matches schema (see examples/)
3. Ensure request includes either tables or files
4. Check interactive docs at /docs for exact schema

## Additional Resources

- **Full README:** See [README.md](README.md) for complete API documentation
- **Quick Start:** See [QUICKSTART.md](QUICKSTART.md) for quick setup guide
- **API Examples:** See [examples/sample_requests.json](examples/sample_requests.json) for comprehensive examples
- **Usage Examples:** See [examples/usage_example.py](examples/usage_example.py) for programmatic usage

## Keyboard Shortcuts Summary

| Action | Windows/Linux | macOS |
|--------|--------------|-------|
| Command Palette | Ctrl+Shift+P | Cmd+Shift+P |
| Quick Open | Ctrl+P | Cmd+P |
| Terminal | Ctrl+` | Ctrl+` |
| Debug | Ctrl+Shift+D | Cmd+Shift+D |
| Testing | Ctrl+Shift+T | Cmd+Shift+T |
| Explorer | Ctrl+Shift+E | Cmd+Shift+E |
| Search | Ctrl+Shift+F | Cmd+Shift+F |
| Source Control | Ctrl+Shift+G | Cmd+Shift+G |
| Run Task | Ctrl+Shift+B | Cmd+Shift+B |
| Format Document | Shift+Alt+F | Shift+Option+F |
| Go to Definition | F12 | F12 |
| Find References | Shift+F12 | Shift+F12 |

## Getting Help

If you encounter issues not covered in this guide:

1. Check the [GitHub Issues](https://github.com/kasapu/NL2SQL/issues)
2. Review API documentation at http://localhost:8000/docs (when server is running)
3. Consult the [FastAPI documentation](https://fastapi.tiangolo.com/)
4. Check [VS Code Python documentation](https://code.visualstudio.com/docs/python/python-tutorial)

Happy coding! 🚀
