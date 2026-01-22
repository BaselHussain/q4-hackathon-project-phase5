# Quickstart Guide: Backend API & Data Layer

**Feature**: Backend API & Data Layer
**Date**: 2026-01-20
**Status**: Complete

## Overview

This guide provides step-by-step instructions for setting up and running the FastAPI backend locally. Follow these instructions to get the development environment running.

## Prerequisites

Before starting, ensure you have the following installed:

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Git** - [Download](https://git-scm.com/downloads)
- **Neon PostgreSQL Account** - [Sign up](https://neon.tech/)
- **Code Editor** - VS Code, PyCharm, or similar

## Initial Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-name>
git checkout 001-backend-api-data
```

### 2. Set Up Python Virtual Environment

**Using venv (standard library)**:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

**Using uv (recommended for faster installs)**:
```bash
# Install uv if not already installed
pip install uv

# Create virtual environment with uv
uv venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
cd backend

# Using pip
pip install -r requirements.txt

# Or using uv (faster)
uv pip install -r requirements.txt
```

**Expected dependencies** (requirements.txt):
```
fastapi==0.109.0
sqlmodel==0.0.14
asyncpg==0.29.0
pydantic==2.5.0
uvicorn[standard]==0.27.0
python-dotenv==1.0.0
pytest==8.0.0
pytest-asyncio==0.23.0
httpx==0.26.0
```

### 4. Configure Neon PostgreSQL Database

#### Create Neon Database

1. Go to [Neon Console](https://console.neon.tech/)
2. Create a new project (or use existing)
3. Create a new database named `todo_app_dev`
4. Copy the connection string from the dashboard

#### Set Up Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# backend/.env
DATABASE_URL=postgresql+asyncpg://user:password@ep-cool-name-123456.us-east-2.aws.neon.tech/todo_app_dev?sslmode=require
ENVIRONMENT=development
```

**Important**:
- Replace the connection string with your actual Neon credentials
- Never commit `.env` file to version control (already in .gitignore)
- Use `.env.example` as a template for team members

**Example .env.example**:
```bash
# backend/.env.example
DATABASE_URL=postgresql+asyncpg://user:password@host/database?sslmode=require
ENVIRONMENT=development
```

### 5. Initialize Database Schema

Run the following command to create tables:

```bash
# From backend/ directory
python -c "
from database import engine
from models import SQLModel
import asyncio

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    print('Database initialized successfully')

asyncio.run(init_db())
"
```

**Alternative**: Create a `init_db.py` script:

```python
# backend/init_db.py
import asyncio
from database import engine
from models import SQLModel

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    print("Database tables created successfully")

if __name__ == "__main__":
    asyncio.run(init_db())
```

Then run:
```bash
python init_db.py
```

## Running the Application

### Start the Development Server

```bash
# From backend/ directory
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Options**:
- `--reload`: Auto-reload on code changes (development only)
- `--host 0.0.0.0`: Accept connections from any IP (use 127.0.0.1 for localhost only)
- `--port 8000`: Port number (default: 8000)

**Expected output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Verify the Server is Running

Open your browser or use curl:

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"2026-01-20T12:00:00Z"}
```

### Access API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Testing the API

### Using curl

**Create a task**:
```bash
curl -X POST http://localhost:8000/api/tasks/123e4567-e89b-12d3-a456-426614174000 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test task",
    "description": "This is a test task"
  }'
```

**List all tasks for a user**:
```bash
curl http://localhost:8000/api/tasks/123e4567-e89b-12d3-a456-426614174000
```

**Get a single task**:
```bash
curl http://localhost:8000/api/tasks/123e4567-e89b-12d3-a456-426614174000/987fcdeb-51a2-43f7-b123-456789abcdef
```

**Update a task**:
```bash
curl -X PUT http://localhost:8000/api/tasks/123e4567-e89b-12d3-a456-426614174000/987fcdeb-51a2-43f7-b123-456789abcdef \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated task title",
    "description": "Updated description"
  }'
```

**Toggle task completion**:
```bash
curl -X PATCH http://localhost:8000/api/tasks/123e4567-e89b-12d3-a456-426614174000/987fcdeb-51a2-43f7-b123-456789abcdef/complete
```

**Delete a task**:
```bash
curl -X DELETE http://localhost:8000/api/tasks/123e4567-e89b-12d3-a456-426614174000/987fcdeb-51a2-43f7-b123-456789abcdef
```

### Using Swagger UI

1. Navigate to http://localhost:8000/docs
2. Expand any endpoint
3. Click "Try it out"
4. Fill in parameters and request body
5. Click "Execute"
6. View the response

### Using Python requests

```python
import requests
import uuid

BASE_URL = "http://localhost:8000"
USER_ID = str(uuid.uuid4())

# Create a task
response = requests.post(
    f"{BASE_URL}/api/tasks/{USER_ID}",
    json={
        "title": "Test task",
        "description": "This is a test"
    }
)
task = response.json()
print(f"Created task: {task['id']}")

# List tasks
response = requests.get(f"{BASE_URL}/api/tasks/{USER_ID}")
tasks = response.json()
print(f"Found {len(tasks)} tasks")

# Update task
response = requests.put(
    f"{BASE_URL}/api/tasks/{USER_ID}/{task['id']}",
    json={"title": "Updated title"}
)
updated_task = response.json()
print(f"Updated task: {updated_task['title']}")

# Toggle completion
response = requests.patch(
    f"{BASE_URL}/api/tasks/{USER_ID}/{task['id']}/complete"
)
completed_task = response.json()
print(f"Task status: {completed_task['status']}")

# Delete task
response = requests.delete(f"{BASE_URL}/api/tasks/{USER_ID}/{task['id']}")
print(f"Deleted task: {response.status_code == 204}")
```

## Running Tests

### Run All Tests

```bash
# From backend/ directory
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=. --cov-report=html
```

### Run Specific Test Files

```bash
# Test models only
pytest tests/test_models.py

# Test API endpoints only
pytest tests/test_tasks.py

# Test database connection
pytest tests/test_database.py
```

### Run Tests with Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run async tests only
pytest -m asyncio
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Edit files in `backend/` directory following the project structure.

### 3. Run Tests

```bash
pytest
```

### 4. Check Code Quality

```bash
# Format code (if using black)
black .

# Lint code (if using ruff)
ruff check .

# Type check (if using mypy)
mypy .
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
```

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

## Troubleshooting

### Database Connection Issues

**Problem**: `asyncpg.exceptions.InvalidPasswordError`

**Solution**:
- Verify DATABASE_URL in `.env` is correct
- Check Neon dashboard for correct credentials
- Ensure SSL mode is set to `require`

**Problem**: `sqlalchemy.exc.OperationalError: could not connect to server`

**Solution**:
- Check internet connection
- Verify Neon database is running (check Neon console)
- Check firewall settings

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
# Ensure virtual environment is activated
# Then reinstall dependencies
pip install -r requirements.txt
```

### Port Already in Use

**Problem**: `OSError: [Errno 48] Address already in use`

**Solution**:
```bash
# Find process using port 8000
# On Windows:
netstat -ano | findstr :8000
taskkill /PID <process_id> /F

# On macOS/Linux:
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn main:app --reload --port 8001
```

### Test Failures

**Problem**: Tests fail with database errors

**Solution**:
- Ensure test database is configured in conftest.py
- Check that test fixtures are properly set up
- Verify test database is isolated from development database

## Environment Variables Reference

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| DATABASE_URL | PostgreSQL connection string | `postgresql+asyncpg://...` | Yes |
| ENVIRONMENT | Environment name | `development`, `test`, `production` | Yes |
| LOG_LEVEL | Logging level | `DEBUG`, `INFO`, `WARNING`, `ERROR` | No (default: INFO) |
| CORS_ORIGINS | Allowed CORS origins | `http://localhost:3000,http://localhost:3001` | No (default: *) |

## Next Steps

After completing the setup:

1. **Explore the API**: Use Swagger UI to test all endpoints
2. **Run the test suite**: Ensure all tests pass
3. **Review the code**: Familiarize yourself with the project structure
4. **Start development**: Follow the TDD workflow for new features

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Neon Documentation](https://neon.tech/docs/)
- [pytest Documentation](https://docs.pytest.org/)
- [OpenAPI Specification](https://swagger.io/specification/)

## Support

For issues or questions:
- Check the [troubleshooting section](#troubleshooting)
- Review the [data model documentation](./data-model.md)
- Consult the [API contracts](./contracts/openapi.yaml)
- Contact the development team
