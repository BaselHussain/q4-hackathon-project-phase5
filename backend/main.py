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

from routers import tasks
from schemas import ProblemDetail

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
# Already loaded above before imports

# Initialize FastAPI application
app = FastAPI(
    title="Task Management API",
    description="RESTful API for managing user tasks with Neon PostgreSQL backend",
    version="1.0.0"
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
            "status": status_code
        }

    return JSONResponse(
        status_code=exc.status_code,
        content=problem_detail
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
