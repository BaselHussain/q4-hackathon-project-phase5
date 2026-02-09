# Quick Start: Kafka + Dapr Event-Driven Architecture

**Feature**: 008-kafka-dapr
**Date**: 2026-02-09
**Audience**: Developers implementing event-driven architecture

## Overview

This guide provides step-by-step instructions to implement event-driven architecture using Redpanda Cloud and Dapr. Follow these steps in order to add automatic recurring tasks, timely reminders, real-time sync, and audit logging to the Todo application.

## Prerequisites

Before starting, ensure you have:

- ✅ Completed Spec 7 (Advanced Todo Features) - recurring tasks, priorities, tags, due dates
- ✅ Python 3.11+ installed
- ✅ Node.js 20+ installed (for frontend)
- ✅ Docker Desktop running (for local Dapr)
- ✅ Dapr CLI 1.12+ installed (`dapr --version`)
- ✅ kubectl 1.28+ installed (for Kubernetes deployment)
- ✅ Helm 3.x installed (for Kubernetes deployment)
- ✅ Redpanda Cloud account (free tier)
- ✅ Neon PostgreSQL database (existing from Phase 2)

## Step 1: Set Up Redpanda Cloud (5 minutes)

### 1.1 Create Redpanda Cloud Account

```bash
# Visit https://redpanda.com/try-redpanda
# Sign up for free serverless tier
# Create a new cluster (serverless)
```

### 1.2 Create Topics

In Redpanda Console:
- Create topic: `task-events` (3 partitions, 7-day retention)
- Create topic: `reminders` (1 partition, 1-day retention)
- Create topic: `task-updates` (3 partitions, 1-day retention)

### 1.3 Get Connection Credentials

```bash
# In Redpanda Console, go to Security > Users
# Create a new user with read/write permissions
# Copy bootstrap servers, username, and password
```

### 1.4 Store Credentials

```bash
# Create .env file in backend/
cat > backend/.env << EOF
REDPANDA_BOOTSTRAP_SERVERS=bootstrap.redpanda.cloud:9092
REDPANDA_SASL_USERNAME=your-username
REDPANDA_SASL_PASSWORD=your-password
EOF
```

## Step 2: Install Dapr Locally (5 minutes)

### 2.1 Initialize Dapr

```bash
# Initialize Dapr in self-hosted mode
dapr init

# Verify installation
dapr --version
# Expected: CLI version: 1.12.x, Runtime version: 1.12.x
```

### 2.2 Verify Dapr Components

```bash
# Check Dapr is running
docker ps | grep dapr

# Expected output:
# dapr_placement
# dapr_redis
# dapr_zipkin
```

## Step 3: Configure Dapr Components (10 minutes)

### 3.1 Create Dapr Components Directory

```bash
mkdir -p ~/.dapr/components
```

### 3.2 Create Pub/Sub Component

```bash
cat > ~/.dapr/components/pubsub.yaml << 'EOF'
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
spec:
  type: pubsub.kafka
  version: v1
  metadata:
  - name: brokers
    value: "bootstrap.redpanda.cloud:9092"
  - name: authType
    value: "password"
  - name: saslMechanism
    value: "SCRAM-SHA-256"
  - name: saslUsername
    value: "your-username"  # Replace with actual username
  - name: saslPassword
    value: "your-password"  # Replace with actual password
  - name: consumerGroup
    value: "{APP_ID}"
EOF
```

### 3.3 Create State Store Component

```bash
cat > ~/.dapr/components/statestore.yaml << 'EOF'
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
spec:
  type: state.postgresql
  version: v1
  metadata:
  - name: connectionString
    value: "postgresql://user:password@host:5432/dbname?sslmode=require"  # Replace with Neon connection string
  - name: tableName
    value: "dapr_state"
EOF
```

## Step 4: Database Migration (5 minutes)

### 4.1 Run Migration Script

```bash
cd backend

# Create migration script
cat > migrate_event_architecture.py << 'EOF'
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def migrate():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))

    # Create audit_logs table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            event_id UUID NOT NULL UNIQUE,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            user_id UUID NOT NULL REFERENCES users(id),
            event_type VARCHAR(50) NOT NULL,
            task_id UUID REFERENCES tasks(id),
            payload JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_task_id ON audit_logs(task_id);
    """)

    # Create dapr_state table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS dapr_state (
            key TEXT PRIMARY KEY,
            value JSONB NOT NULL,
            isbinary BOOLEAN NOT NULL,
            insertdate TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updatedate TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            eTag TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_dapr_state_updatedate ON dapr_state(updatedate);
    """)

    await conn.close()
    print("✅ Migration complete")

if __name__ == "__main__":
    asyncio.run(migrate())
EOF

# Run migration
python migrate_event_architecture.py
```

## Step 5: Implement Event Publishing (30 minutes)

### 5.1 Install Dependencies

```bash
cd backend

# Add to requirements.txt
cat >> requirements.txt << EOF
dapr==1.12.0
httpx==0.26.0
EOF

# Install
pip install -r requirements.txt
```

### 5.2 Create Event Publisher

```bash
mkdir -p backend/events

cat > backend/events/publisher.py << 'EOF'
import httpx
import uuid
from datetime import datetime
from typing import Dict, Any

DAPR_HTTP_PORT = 3500
PUBSUB_NAME = "pubsub"

async def publish_event(topic: str, event_type: str, data: Dict[str, Any]):
    """Publish CloudEvents-compliant event to Dapr Pub/Sub"""
    event = {
        "specversion": "1.0",
        "type": event_type,
        "source": "backend-api",
        "id": str(uuid.uuid4()),
        "time": datetime.utcnow().isoformat() + "Z",
        "datacontenttype": "application/json",
        "data": data
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:{DAPR_HTTP_PORT}/v1.0/publish/{PUBSUB_NAME}/{topic}",
            json=event,
            headers={"Content-Type": "application/cloudevents+json"}
        )
        response.raise_for_status()

    return event["id"]
EOF
```

### 5.3 Extend Task Router

```python
# In backend/routers/tasks.py, add event publishing

from backend.events.publisher import publish_event

@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate, current_user: User = Depends(get_current_user)):
    # ... existing task creation code ...

    # Publish task.created event
    await publish_event(
        topic="task-events",
        event_type="com.todo.task.created",
        data={
            "task_id": str(new_task.id),
            "user_id": str(current_user.id),
            "sequence": 1,
            "idempotency_key": str(uuid.uuid4()),
            "payload": {
                "title": new_task.title,
                "description": new_task.description,
                "status": new_task.status,
                "priority": new_task.priority,
                "tags": new_task.tags,
                "due_date": new_task.due_date.isoformat() if new_task.due_date else None,
                "recurring_pattern": new_task.recurring_pattern
            }
        }
    )

    return new_task
```

## Step 6: Build Recurring Task Service (45 minutes)

### 6.1 Create Service Structure

```bash
mkdir -p backend/services/recurring-task
cd backend/services/recurring-task

cat > main.py << 'EOF'
from fastapi import FastAPI
from dapr.ext.fastapi import DaprApp
import httpx
from datetime import datetime, timedelta

app = FastAPI()
dapr_app = DaprApp(app)

@dapr_app.subscribe(pubsub="pubsub", topic="task-events")
async def handle_task_event(event: dict):
    """Handle task completion events and create next occurrence if recurring"""
    event_type = event.get("type")
    data = event.get("data", {})

    if event_type == "com.todo.task.completed":
        payload = data.get("payload", {})
        recurring_pattern = payload.get("recurring_pattern")

        if recurring_pattern:
            # Calculate next due date
            next_due_date = calculate_next_due_date(
                payload.get("due_date"),
                recurring_pattern,
                payload.get("recurring_interval", 1)
            )

            # Create next task occurrence via backend API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/api/tasks",
                    json={
                        "title": payload["title"],
                        "description": payload["description"],
                        "priority": payload["priority"],
                        "tags": payload["tags"],
                        "due_date": next_due_date.isoformat(),
                        "recurring_pattern": recurring_pattern,
                        "recurring_interval": payload.get("recurring_interval", 1)
                    },
                    headers={"Authorization": f"Bearer {get_service_token()}"}
                )
                response.raise_for_status()

    return {"success": True}

def calculate_next_due_date(current_due_date: str, pattern: str, interval: int) -> datetime:
    """Calculate next due date based on recurrence pattern"""
    current = datetime.fromisoformat(current_due_date.replace("Z", "+00:00"))

    if pattern == "daily":
        return current + timedelta(days=interval)
    elif pattern == "weekly":
        return current + timedelta(weeks=interval)
    elif pattern == "monthly":
        return current + timedelta(days=30 * interval)  # Simplified

    return current

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
EOF
```

### 6.2 Run Recurring Task Service

```bash
# Terminal 1: Run with Dapr
dapr run --app-id recurring-task-service --app-port 8001 --dapr-http-port 3501 -- python main.py
```

## Step 7: Test Event Flow (15 minutes)

### 7.1 Start Backend with Dapr

```bash
# Terminal 2: Run backend with Dapr
cd backend
dapr run --app-id backend-api --app-port 8000 --dapr-http-port 3500 -- uvicorn app.main:app --reload
```

### 7.2 Create Recurring Task

```bash
# Terminal 3: Test task creation
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "title": "Daily standup",
    "description": "Team sync meeting",
    "priority": "high",
    "tags": ["work", "meeting"],
    "due_date": "2026-02-10T10:00:00Z",
    "recurring_pattern": "daily",
    "recurring_interval": 1
  }'
```

### 7.3 Complete Task and Verify Next Occurrence

```bash
# Mark task as completed
curl -X PUT http://localhost:8000/api/tasks/{task_id}/complete \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Verify next occurrence created
curl http://localhost:8000/api/tasks \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Expected: New task with due_date = 2026-02-11T10:00:00Z
```

### 7.4 Check Dapr Logs

```bash
# Check event publishing logs
dapr logs --app-id backend-api

# Check event consumption logs
dapr logs --app-id recurring-task-service
```

## Step 8: Build Notification Service (Optional - 45 minutes)

Follow similar pattern as Recurring Task Service:
1. Create `backend/services/notification/main.py`
2. Subscribe to `reminders` topic
3. Use Dapr Jobs API to schedule reminders
4. Send email via SendGrid and push via Firebase Cloud Messaging

## Step 9: Deploy to Kubernetes (60 minutes)

### 9.1 Install Minikube

```bash
# Install Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Start Minikube
minikube start --cpus=4 --memory=8192
```

### 9.2 Install Dapr on Kubernetes

```bash
# Install Dapr CLI
dapr init --kubernetes

# Verify Dapr installation
kubectl get pods -n dapr-system
```

### 9.3 Deploy Dapr Components

```bash
# Apply Dapr components
kubectl apply -f specs/008-kafka-dapr/contracts/dapr-components/
```

### 9.4 Deploy Services with Helm

```bash
# Create Helm charts (see helm/ directory)
helm install backend ./helm/backend
helm install recurring-task ./helm/recurring-task
```

## Troubleshooting

### Issue: Events not being published

**Solution**:
```bash
# Check Dapr sidecar is running
curl http://localhost:3500/v1.0/healthz

# Check Pub/Sub component
dapr components -k
```

### Issue: Consumer not receiving events

**Solution**:
```bash
# Check subscription endpoint
curl http://localhost:8001/dapr/subscribe

# Check Dapr logs
dapr logs --app-id recurring-task-service
```

### Issue: State store connection failed

**Solution**:
```bash
# Verify PostgreSQL connection string
psql "postgresql://user:password@host:5432/dbname?sslmode=require"

# Check dapr_state table exists
SELECT * FROM dapr_state LIMIT 1;
```

## Next Steps

1. ✅ Implement Notification Service (reminders)
2. ✅ Implement Audit Service (logging)
3. ✅ Implement Real-Time Sync Service (WebSocket)
4. ✅ Add frontend WebSocket client
5. ✅ Deploy to cloud (Azure AKS, Google GKE, or Oracle OKE)
6. ✅ Set up CI/CD pipeline (GitHub Actions)

## Resources

- [Dapr Documentation](https://docs.dapr.io/)
- [Redpanda Cloud Documentation](https://docs.redpanda.com/current/get-started/cloud/)
- [CloudEvents Specification](https://cloudevents.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Helm Documentation](https://helm.sh/docs/)

## Support

For issues or questions:
- Check `specs/008-kafka-dapr/plan.md` for detailed architecture
- Check `specs/008-kafka-dapr/data-model.md` for event schemas
- Check `specs/008-kafka-dapr/research.md` for technical decisions
