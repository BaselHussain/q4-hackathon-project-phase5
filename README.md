# Todo App - Cloud-Native Event-Driven Architecture

A production-ready cloud-native todo application with event-driven microservices architecture using Kafka + Dapr, comprehensive monitoring with Prometheus + Grafana, centralized logging with Loki, and multi-cloud deployment support (OKE, AKS, GKE).

## Architecture Overview

This application implements:
- **Spec 8**: Kafka + Dapr Event-Driven Architecture
- **Spec 9**: Monitoring, Logging, and Multi-Cloud Deployment

### Services

1. **Backend API** (Port 8000) - Main FastAPI application
   - Task CRUD operations
   - User authentication (JWT)
   - Event publishing to Oracle Streaming Service via Dapr

2. **Recurring Task Service** (Port 8001)
   - Subscribes to `task-events` topic
   - Automatically creates next occurrence when recurring task completed
   - Supports daily, weekly, monthly, yearly patterns

3. **Notification Service** (Port 8002)
   - Subscribes to `reminders` topic
   - Schedules reminders via Dapr Jobs API
   - Sends email (SendGrid) and push (Firebase) notifications

4. **Real-Time Sync Service** (Port 8003)
   - Subscribes to `task-updates` topic
   - WebSocket server for real-time task synchronization
   - Broadcasts updates to connected clients

5. **Audit Service** (Port 8004)
   - Subscribes to `task-events` topic
   - Logs all task operations to `audit_logs` table
   - Provides query API with access control

### Event Flow

```
User Action → Backend API → Dapr Pub/Sub → Oracle Streaming Service
                                ↓
                    ┌───────────┴───────────┐
                    ↓           ↓           ↓
            Recurring Task  Notification  Audit
             Service         Service      Service
                    ↓
            Real-Time Sync Service → WebSocket → Frontend
```

### Topics

- **task-events** (3 partitions): Task lifecycle events (created, updated, completed, deleted)
- **reminders** (1 partition): Reminder scheduling and cancellation
- **task-updates** (3 partitions): Real-time sync events for WebSocket clients

## Technology Stack

- **Backend**: Python 3.11+, FastAPI 0.109+
- **Database**: Neon Serverless PostgreSQL (asyncpg)
- **Message Broker**:
  - **Local Dev (Minikube)**: Redpanda (Kafka-compatible)
  - **Production (OKE)**: Oracle Streaming Service (Kafka-compatible)
- **Service Mesh**: Dapr 1.12+ (Pub/Sub, State Store, Jobs API)
- **Frontend**: Next.js 16+, React 19, TypeScript
- **Deployment**:
  - **Local**: Minikube with Helm 3
  - **Production**: Oracle Kubernetes Engine (OKE) with Helm 3
- **CI/CD**: GitHub Actions

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop
- Minikube 1.32+
- Dapr CLI 1.12+
- Helm 3.x
- kubectl 1.28+

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-org/q4-hackathon-project-phase5.git
cd q4-hackathon-project-phase5
```

### 2. Set Up Environment Variables

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your credentials:
# - DATABASE_URL (Neon PostgreSQL)
#
# For Minikube (local development):
# - REDPANDA_BOOTSTRAP_SERVERS, REDPANDA_SASL_USERNAME, REDPANDA_SASL_PASSWORD
#
# For OKE (production deployment):
# - ORACLE_STREAMING_ENDPOINT, ORACLE_STREAMING_USERNAME, ORACLE_STREAMING_AUTH_TOKEN
#
# Common for both:
# - SENDGRID_API_KEY, FCM_SERVER_KEY
# - BETTER_AUTH_SECRET
```

**Note:** The application supports dual configuration:
- **Minikube**: Uses Redpanda (local or Redpanda Cloud) via `dapr-components/pubsub.kafka.minikube.yaml`
- **OKE**: Uses Oracle Streaming Service via `dapr-components/pubsub.kafka.oke.yaml`

### 3. Run Database Migration

```bash
cd backend
python migrate_event_architecture.py
```

This creates:
- `audit_logs` table for comprehensive audit trail
- `dapr_state` table for Dapr State Store

### 4. Set Up Minikube + Dapr + Kafka + Monitoring + Logging

```bash
# Full setup with monitoring and logging
./scripts/setup-minikube.sh --with-monitoring --with-logging

# Or minimal setup (no monitoring/logging)
./scripts/setup-minikube.sh
```

This script:
- Starts Minikube cluster (4 CPUs, 8GB RAM)
- Installs Dapr 1.12.0 on Kubernetes
- Applies Dapr components (Pub/Sub, State Store, Secrets)
- Creates Kubernetes secrets from `.env`
- **Optional**: Deploys Prometheus + Grafana (monitoring)
- **Optional**: Deploys Loki + Promtail (logging)

### 5. Deploy All Services

```bash
./scripts/deploy-local.sh
```

This script:
- Builds Docker images for all 5 services
- Loads images into Minikube
- Deploys Helm charts
- Waits for pods to be ready

### 6. Access Services

```bash
# Backend API
kubectl port-forward svc/backend 8000:8000

# Sync Service (WebSocket)
kubectl port-forward svc/sync-service 8003:8003

# Dapr Dashboard
dapr dashboard -k

# Grafana (if monitoring enabled)
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
# Open http://localhost:3000 (admin/admin)

# Loki (if logging enabled)
kubectl port-forward -n logging svc/loki-gateway 3100:80
```

### 7. Run End-to-End Tests

```bash
# Test complete deployment
./scripts/test-e2e-minikube.sh
```

This validates:
- All services are running
- Dapr runtime is operational
- Monitoring stack is collecting metrics
- Logging stack is aggregating logs
- Health checks pass

---

## Monitoring & Observability

### Quick Start

For detailed monitoring and logging setup, see: **[Monitoring & Logging Quick Start Guide](docs/monitoring-logging-quickstart.md)**

### Metrics (Prometheus + Grafana)

**Deploy Monitoring Stack**:
```bash
./scripts/deploy-monitoring.sh --environment minikube
```

**Access Grafana**:
```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
# Open http://localhost:3000
# Login: admin / admin
```

**Pre-Built Dashboards**:
1. **Service Overview**: HTTP metrics, error rates, response times
2. **Event Processing**: Kafka and Dapr pub/sub metrics
3. **WebSocket Metrics**: Active connections, message delivery
4. **Application Logs**: Centralized log viewer with Loki

**Key Metrics**:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency (p95, p99)
- `tasks_created_total` - Tasks created by user
- `websocket_connections_active` - Active WebSocket connections
- `database_query_duration_seconds` - Database query latency
- `dapr_component_pubsub_egress_count` - Events published to Kafka

### Logging (Loki + Promtail)

**Deploy Logging Stack**:
```bash
./scripts/deploy-logging.sh --environment minikube
```

**Query Logs in Grafana**:
1. Open Grafana (http://localhost:3000)
2. Go to **Explore** (compass icon)
3. Select **Loki** data source
4. Try these queries:

```logql
# All logs from backend service
{namespace="default", service="backend"}

# Error logs only
{namespace="default", level="ERROR"}

# Logs with specific text
{namespace="default"} |= "WebSocket"

# Logs from last 5 minutes
{namespace="default"} [5m]
```

**Structured Logging**:
All services emit structured JSON logs with:
- `timestamp` (RFC3339Nano)
- `level` (INFO, WARNING, ERROR)
- `logger` (module name)
- `message` (log message)
- `request_id` (unique per request)
- `user_id` (authenticated user)
- `trace_id` (distributed tracing)

### Alerting

**Pre-Configured Alerts**:
- High error rate (> 5%)
- Service down
- High memory usage (> 80%)
- Pod restarting frequently
- Database connection failures
- Kafka consumer lag

**Configure Notifications**:
Edit `helm/monitoring/templates/alertmanager-config.yaml` to add Slack/email webhooks.

---

## Multi-Cloud Deployment

The Todo App supports deployment to multiple cloud providers with comprehensive guides:

### Oracle Kubernetes Engine (OKE)

**Full Guide**: [OKE Deployment Guide](docs/deployment/oke-deployment.md)

**Quick Deploy**:
```bash
# 1. Create OKE cluster (via OCI Console or CLI)
# 2. Configure kubectl
oci ce cluster create-kubeconfig --cluster-id <cluster-ocid>

# 3. Deploy monitoring
./scripts/deploy-monitoring.sh --environment oke

# 4. Deploy logging
./scripts/deploy-logging.sh --environment oke

# 5. Deploy services
helm upgrade --install backend ./helm/backend --values ./helm/backend/values-oke.yaml

# 6. Run E2E tests
./scripts/test-e2e-oke.sh
```

**OKE-Specific Features**:
- OCI Block Volumes for persistent storage
- Oracle Streaming Service (Kafka-compatible)
- OCI Object Storage for Loki logs
- OCI Load Balancer for ingress

### Azure Kubernetes Service (AKS)

**Full Guide**: [AKS Deployment Guide](docs/deployment/aks-deployment.md)

**Quick Deploy**:
```bash
# 1. Create AKS cluster
az aks create --resource-group todoapp-rg --name todoapp-cluster

# 2. Get credentials
az aks get-credentials --resource-group todoapp-rg --name todoapp-cluster

# 3. Deploy monitoring
./scripts/deploy-monitoring.sh --environment aks

# 4. Deploy logging
./scripts/deploy-logging.sh --environment aks

# 5. Deploy services
helm upgrade --install backend ./helm/backend --values ./helm/backend/values-aks.yaml
```

**AKS-Specific Features**:
- Azure Disk for persistent storage
- Azure Event Hubs (Kafka-compatible)
- Azure Blob Storage for Loki logs
- Azure Load Balancer for ingress

### Google Kubernetes Engine (GKE)

**Full Guide**: [GKE Deployment Guide](docs/deployment/gke-deployment.md)

**Quick Deploy**:
```bash
# 1. Create GKE cluster
gcloud container clusters create todoapp-cluster --zone us-central1-a

# 2. Get credentials
gcloud container clusters get-credentials todoapp-cluster --zone us-central1-a

# 3. Deploy monitoring
./scripts/deploy-monitoring.sh --environment gke

# 4. Deploy logging
./scripts/deploy-logging.sh --environment gke

# 5. Deploy services
helm upgrade --install backend ./helm/backend --values ./helm/backend/values-gke.yaml
```

**GKE-Specific Features**:
- Google Persistent Disk for storage
- Self-hosted Kafka (Redpanda)
- Google Cloud Storage for Loki logs
- Google Cloud Load Balancer for ingress

---

## Production Readiness

Before deploying to production, review:

- **[Production Readiness Checklist](docs/production-readiness-checklist.md)** - 12-section comprehensive checklist
- **[Operational Runbooks](docs/runbooks.md)** - Step-by-step procedures for common operations
- **[SLI/SLO Definitions](docs/sli-slo-definitions.md)** - Service level objectives and error budgets
- **[Incident Response Template](docs/incident-response-template.md)** - Structured incident documentation
- **[Disaster Recovery Plan](docs/disaster-recovery-plan.md)** - Complete DR procedures (RTO: 4h, RPO: 1h)

**Key Production Requirements**:
- ✅ Resource limits and requests configured
- ✅ Horizontal Pod Autoscaling (HPA) enabled
- ✅ Pod Disruption Budgets (PDB) configured
- ✅ Monitoring and alerting operational
- ✅ Centralized logging with 30-day retention
- ✅ Automated backups configured
- ✅ TLS/HTTPS for all external traffic
- ✅ Secrets management (Kubernetes Secrets or cloud secret manager)
- ✅ Network policies for pod-to-pod communication
- ✅ Regular security scans and updates

---
# Backend API
kubectl port-forward svc/backend 8000:8000

# Real-Time Sync (WebSocket)
kubectl port-forward svc/sync-service 8003:8003

# Dapr Dashboard
dapr dashboard -k
```

## Deployment Options

This application supports **dual deployment configurations** for Phase 5:

### 📦 Local Development (Minikube + Redpanda)
Quick start guide above walks you through Minikube setup with Redpanda.

### ☁️ Production Deployment (OKE + Oracle Streaming)
For production deployment on Oracle Cloud Infrastructure (OKE), see the comprehensive setup guide:

**📘 [Oracle Cloud Setup Guide](docs/ORACLE_CLOUD_SETUP.md)**

This guide includes:
- Creating Oracle Streaming Service (Kafka-compatible message broker)
- Setting up Oracle Kubernetes Engine (OKE) cluster
- Configuring OCI Native Ingress Controller with WebSocket support
- Building and pushing images to Oracle Container Image Registry (OCIR)
- Deploying all services via Helm charts
- Complete OCI CLI commands for end-to-end setup

**Migration Summary:** See [Oracle Cloud Migration Summary](docs/ORACLE_CLOUD_MIGRATION.md) for details on changes from Redpanda to Oracle Streaming Service.

### 📖 Complete Deployment Guide
For a comprehensive comparison of both deployment options and detailed troubleshooting:

**📘 [Deployment Guide: Minikube vs OKE](docs/DEPLOYMENT_GUIDE.md)**

## Development

### Running Services Locally (Without Kubernetes)

Each service can run standalone with Dapr sidecar:

```bash
# Terminal 1: Backend API
cd backend
dapr run --app-id backend-api --app-port 8000 --dapr-http-port 3500 \
  --components-path ../dapr-components \
  -- uvicorn main:app --reload

# Terminal 2: Recurring Task Service
cd backend/services/recurring-task
dapr run --app-id recurring-task-service --app-port 8001 --dapr-http-port 3501 \
  --components-path ../../../dapr-components \
  -- uvicorn main:app --reload

# Terminal 3: Notification Service
cd backend/services/notification
dapr run --app-id notification-service --app-port 8002 --dapr-http-port 3502 \
  --components-path ../../../dapr-components \
  -- uvicorn main:app --reload

# Terminal 4: Sync Service
cd backend/services/sync
dapr run --app-id sync-service --app-port 8003 --dapr-http-port 3503 \
  --components-path ../../../dapr-components \
  -- uvicorn main:app --reload

# Terminal 5: Audit Service
cd backend/services/audit
dapr run --app-id audit-service --app-port 8004 --dapr-http-port 3504 \
  --components-path ../../../dapr-components \
  -- uvicorn main:app --reload
```

### Running Tests

```bash
cd backend

# Unit tests
pytest tests/unit/ -v

# Integration tests (requires Dapr)
pytest tests/integration/ -v -m integration

# Contract tests (event schema validation)
pytest tests/contract/ -v

# All tests with coverage
pytest --cov=. --cov-report=html
```

## Event Schemas

All events follow **CloudEvents 1.0** specification. See `specs/008-kafka-dapr/contracts/events/` for JSON schemas.

### Task Event Example

```json
{
  "specversion": "1.0",
  "type": "com.todo.task.created",
  "source": "backend-api",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "time": "2026-02-10T10:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "task_id": "uuid",
    "user_id": "uuid",
    "sequence": 1,
    "idempotency_key": "uuid",
    "payload": {
      "title": "Weekly team meeting",
      "status": "pending",
      "priority": "high",
      "recurring_pattern": "weekly"
    }
  }
}
```

## Monitoring

### Health Checks

All services expose `/health` endpoint:

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
```

### Logs

```bash
# Backend API logs
kubectl logs -l app.kubernetes.io/name=backend -c backend --tail=50 -f

# Dapr sidecar logs
kubectl logs -l app.kubernetes.io/name=backend -c daprd --tail=50 -f

# All services
kubectl logs -l dapr.io/enabled=true --all-containers --tail=50 -f
```

### Dapr Dashboard

```bash
dapr dashboard -k
# Opens http://localhost:8080
```

## CI/CD

GitHub Actions workflows:

- **build-test.yml**: Runs on push to `008-kafka-dapr` branch
  - Lints Python code
  - Runs unit, integration, and contract tests
  - Builds Docker images

- **deploy-staging.yml**: Runs on push to `main` branch
  - Deploys to staging environment
  - Runs smoke tests

- **deploy-production.yml**: Runs on release published
  - Requires manual approval
  - Deploys to production
  - Automatic rollback on failure

## Architecture Decisions

See `history/adr/` for Architecture Decision Records documenting key technical decisions:

- Message broker selection (Oracle Streaming Service vs Kafka vs Confluent)
- Event ordering strategy (sequence numbers vs partitions)
- Retry policy (exponential backoff with DLQ)
- State management (Dapr State Store vs Redis)

## Troubleshooting

### Events Not Publishing

1. Check Dapr sidecar is running:
   ```bash
   kubectl get pods -l dapr.io/enabled=true
   ```

2. Check Dapr components are applied:
   ```bash
   kubectl get components
   ```

3. Check Oracle Streaming Service connection:
   ```bash
   kubectl logs -l app.kubernetes.io/name=backend -c daprd | grep pubsub
   ```

### Reminders Not Sending

1. Check notification service logs:
   ```bash
   kubectl logs -l app.kubernetes.io/name=notification -c notification
   ```

2. Verify SendGrid/FCM credentials in secrets:
   ```bash
   kubectl get secret app-secrets -o yaml
   ```

3. Check Dapr Jobs API:
   ```bash
   kubectl logs -l app.kubernetes.io/name=notification -c daprd | grep jobs
   ```

### WebSocket Not Connecting

1. Verify sync service is running:
   ```bash
   kubectl get pods -l app.kubernetes.io/name=sync
   ```

2. Check JWT token is valid:
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8003/health
   ```

3. Test WebSocket connection:
   ```bash
   wscat -c "ws://localhost:8003/ws/tasks?token=<jwt-token>"
   ```

## Contributing

1. Create feature branch from `main`
2. Follow Spec-Driven Development workflow:
   - `/sp.specify` - Write specification
   - `/sp.clarify` - Resolve ambiguities
   - `/sp.plan` - Generate implementation plan
   - `/sp.tasks` - Break into tasks
   - `/sp.implement` - Execute tasks
3. Run tests and ensure all pass
4. Create PR with description following template
5. Wait for CI checks to pass
6. Request review

## License

MIT

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-org/q4-hackathon-project-phase5/issues
- Documentation: `specs/008-kafka-dapr/`
- Architecture: `specs/008-kafka-dapr/plan.md`
