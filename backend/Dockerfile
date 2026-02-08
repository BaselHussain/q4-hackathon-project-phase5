# Backend Dockerfile — FastAPI (8002) + MCP Server (8001)
# Uses multi-process supervisor pattern via shell script

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY main.py mcp_server.py database.py models.py schemas.py dependencies.py ./
COPY src/ ./src/
COPY routers/ ./routers/
COPY tools/ ./tools/
COPY app/ ./app/

# Copy .env if present (for local builds; override with env vars in production)
COPY .env* ./

# Create startup script that runs both processes
RUN printf '#!/bin/sh\n\
\n\
cleanup() {\n\
  kill $MCP_PID $API_PID 2>/dev/null\n\
  exit 0\n\
}\n\
\n\
trap cleanup TERM INT\n\
\n\
echo "Starting MCP Server on port 8001..."\n\
python mcp_server.py &\n\
MCP_PID=$!\n\
sleep 2\n\
echo "Starting FastAPI on port ${API_PORT:-8002}..."\n\
python -m uvicorn main:app --host 0.0.0.0 --port ${API_PORT:-8002} &\n\
API_PID=$!\n\
\n\
# Wait for both processes\n\
wait $MCP_PID $API_PID\n' > /app/start.sh && chmod +x /app/start.sh

# Expose both ports
EXPOSE 8001 8002

# Health check against FastAPI
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${API_PORT:-8002}/health || exit 1

# Run both servers
CMD ["/app/start.sh"]
