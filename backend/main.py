"""
FastAPI application for Task Management API.

This module initializes the FastAPI app, configures middleware, and implements error handling.
"""
import logging
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

# Load environment variables BEFORE importing local modules
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from routers import tasks
from schemas import ProblemDetail
from src.api import auth_router
from src.middleware.logging import log_security_event

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# T037: Configure slowapi rate limiter (5 requests per minute per IP)
limiter = Limiter(key_func=get_remote_address)

# Load environment variables from .env file
# Already loaded above before imports

# Initialize FastAPI application
app = FastAPI(
    title="Task Management API",
    description="RESTful API for managing user tasks with Neon PostgreSQL backend",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "authentication",
            "description": "User registration and login endpoints. Login endpoint is rate-limited to 5 requests per minute per IP address."
        },
        {
            "name": "tasks",
            "description": "Task management operations. All endpoints require JWT authentication via Bearer token."
        },
        {
            "name": "health",
            "description": "Health check and monitoring endpoints"
        }
    ],
    # T067: Add security scheme for JWT Bearer authentication
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# T067: Define security scheme for OpenAPI documentation
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Task Management API",
        version="1.0.0",
        description="""
## Authentication

This API uses JWT (JSON Web Token) Bearer authentication. To access protected endpoints:

1. **Register** a new account at `POST /api/auth/register`
2. **Login** with your credentials at `POST /api/auth/login` to receive a JWT token
3. **Include the token** in the `Authorization` header for all protected requests:
   ```
   Authorization: Bearer <your-jwt-token>
   ```

### Example Authentication Flow

```bash
# 1. Register a new user
curl -X POST http://localhost:8000/api/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{"email": "user@example.com", "password": "SecurePass123!"}'

# 2. Login to get JWT token
curl -X POST http://localhost:8000/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"email": "user@example.com", "password": "SecurePass123!"}'

# Response includes access_token:
# {"access_token": "eyJhbGc...", "token_type": "bearer", ...}

# 3. Use token to access protected endpoints
curl -X GET http://localhost:8000/api/{user_id}/tasks \\
  -H "Authorization: Bearer eyJhbGc..."
```

### Token Details

- **Algorithm**: HS256 (HMAC with SHA-256)
- **Expiration**: 24 hours
- **Format**: `Authorization: Bearer <token>`

### Security Features

- **Password Hashing**: Bcrypt with automatic salt generation
- **Rate Limiting**: Login endpoint limited to 5 requests/minute per IP
- **User Isolation**: Users can only access their own tasks
- **Security Logging**: All authentication failures are logged

### Error Responses

All errors follow RFC 7807 Problem Details format:

```json
{
  "type": "invalid-credentials",
  "title": "Invalid Credentials",
  "status": 401,
  "detail": "Invalid email or password",
  "instance": "/api/auth/login"
}
```
        """,
        routes=app.routes,
    )

    # Add security scheme definition
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token obtained from the /api/auth/login endpoint"
        }
    }

    # Apply security to all task endpoints (paths starting with /api/{user_id})
    for path, path_item in openapi_schema["paths"].items():
        if path.startswith("/api/") and "{user_id}" in path:
            for method in path_item.values():
                if isinstance(method, dict) and "operationId" in method:
                    method["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Add rate limiter to app state
app.state.limiter = limiter

# T039: Custom RFC 7807 error handler for rate limit exceeded
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Exception handler for RateLimitExceeded that formats responses as RFC 7807 Problem Details.

    Args:
        request: The incoming request
        exc: The RateLimitExceeded exception

    Returns:
        JSONResponse: RFC 7807 formatted error response with Retry-After header
    """
    # T065: Log rate limit trigger
    log_security_event(
        event_type="rate_limit_exceeded",
        user_id=None,  # Rate limit is per IP, not per user
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details={
            "endpoint": str(request.url.path),
            "limit": "5/minute"
        }
    )

    return JSONResponse(
        status_code=429,
        content={
            "type": "rate-limit-exceeded",
            "title": "Rate Limit Exceeded",
            "status": 429,
            "detail": "Too many requests. Please try again later.",
            "instance": str(request.url.path)
        },
        headers={
            "Content-Type": "application/problem+json",
            "Retry-After": "60"  # Rate limit window is 1 minute
        }
    )

# Configure CORS middleware for development (allow all origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# T068: Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log all incoming requests and responses.

    Logs request method, path, client IP, and response time.

    Args:
        request: The incoming request
        call_next: The next middleware or route handler

    Returns:
        Response: The response from the next handler
    """
    start_time = time.time()

    # Log incoming request
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )

    # Process request
    response = await call_next(request)

    # Calculate response time
    process_time = time.time() - start_time

    # Log response
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"status={response.status_code} duration={process_time:.3f}s"
    )

    # Add response time header
    response.headers["X-Process-Time"] = str(process_time)

    return response


# Include routers
app.include_router(auth_router)
app.include_router(tasks.router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Exception handler for HTTPException that formats responses as RFC 7807 Problem Details.

    Maps HTTP status codes to appropriate type and title values.

    Args:
        request: The incoming request
        exc: The HTTPException that was raised

    Returns:
        JSONResponse: RFC 7807 formatted error response
    """
    # If detail is already a dict (from our custom exceptions), use it
    if isinstance(exc.detail, dict):
        problem_detail = exc.detail
    else:
        # Map status codes to appropriate types and titles
        status_code = exc.status_code
        type_mapping = {
            400: "bad-request",
            401: "unauthorized",
            403: "forbidden",
            404: "not-found",
            405: "method-not-allowed",
            409: "conflict",
            422: "unprocessable-entity",
            500: "internal-server-error"
        }

        title_mapping = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            409: "Conflict",
            422: "Unprocessable Entity",
            500: "Internal Server Error"
        }

        problem_detail = {
            "type": type_mapping.get(status_code, "error"),
            "title": title_mapping.get(status_code, "Error"),
            "detail": str(exc.detail),
            "status": status_code,
            "instance": str(request.url.path)
        }

    return JSONResponse(
        status_code=exc.status_code,
        content=problem_detail,
        headers={"Content-Type": "application/problem+json"}
    )


@app.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint.

    Returns the current health status of the API and current UTC timestamp.

    Returns:
        dict: Health status and timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
