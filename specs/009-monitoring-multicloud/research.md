# Research: Monitoring, Logging, and Multi-Cloud Deployment

**Feature**: 009-monitoring-multicloud
**Date**: 2026-02-10
**Purpose**: Resolve technical unknowns and make technology decisions for monitoring, logging, and multi-cloud deployment

## Research Questions

### 1. Monitoring Stack Selection

**Question**: Should we use kube-prometheus-stack or deploy Prometheus + Grafana separately?

**Options Considered**:
- **Option A**: kube-prometheus-stack Helm chart (recommended)
  - Pros: Complete monitoring solution, pre-configured dashboards, includes Alertmanager, widely adopted
  - Cons: Larger footprint, more components than needed
- **Option B**: Separate Prometheus + Grafana Helm charts
  - Pros: More control, smaller footprint
  - Cons: More configuration required, no pre-built integration

**Decision**: Use kube-prometheus-stack Helm chart
**Rationale**:
- Provides complete monitoring solution out-of-the-box
- Includes pre-configured Grafana dashboards for Kubernetes
- Widely adopted in production environments
- Easier to maintain and upgrade
- Includes Alertmanager for future alerting needs (out of scope for Spec 9, but valuable for future)

**Implementation Details**:
- Helm chart: `prometheus-community/kube-prometheus-stack`
- Version: Latest stable (51.x+)
- Configuration: Custom values.yaml for Minikube vs cloud environments
- Storage: Persistent volumes for Prometheus data (configurable retention)

---

### 2. Logging Stack Selection

**Question**: Should we use Loki + Promtail or ELK stack (Elasticsearch + Logstash + Kibana)?

**Options Considered**:
- **Option A**: Loki + Promtail (recommended)
  - Pros: Lightweight, integrates with Grafana, designed for Kubernetes, lower resource usage
  - Cons: Less mature than ELK, fewer advanced features
- **Option B**: ELK stack
  - Pros: More mature, powerful search capabilities, rich ecosystem
  - Cons: Heavy resource usage, complex setup, separate UI (Kibana)

**Decision**: Use Loki + Promtail
**Rationale**:
- Integrates seamlessly with Grafana (single UI for metrics + logs)
- Designed for cloud-native environments
- Lower resource footprint (critical for Minikube and free-tier cloud)
- Simpler architecture (no Logstash, no Elasticsearch cluster)
- Sufficient for our use case (log aggregation and search)

**Implementation Details**:
- Helm chart: `grafana/loki-stack` (includes Loki + Promtail + Grafana)
- Version: Latest stable (2.10.x+)
- Configuration: 7-day retention for dev, 30-day for prod
- Storage: Persistent volumes for Loki data

---

### 3. Dapr Metrics Exposure

**Question**: How do we expose Dapr metrics for Prometheus to scrape?

**Research Findings**:
- Dapr sidecars expose metrics on port 9090 by default
- Metrics endpoint: `http://localhost:9090/metrics`
- Prometheus ServiceMonitor CRD can auto-discover Dapr sidecars
- Dapr metrics include: HTTP request latency, gRPC calls, pub/sub operations, state store operations

**Decision**: Use Prometheus ServiceMonitor CRD for auto-discovery
**Rationale**:
- Automatic discovery of Dapr sidecars (no manual configuration per service)
- Standard Kubernetes pattern
- Works with kube-prometheus-stack out-of-the-box

**Implementation Details**:
- Create ServiceMonitor CRD for Dapr sidecars
- Label selector: `dapr.io/enabled: "true"`
- Scrape interval: 15 seconds
- Metrics port: 9090

---

### 4. Structured Logging Format

**Question**: What structured logging library should we use for Python services?

**Options Considered**:
- **Option A**: python-json-logger
  - Pros: Simple, lightweight, JSON output
  - Cons: Basic features only
- **Option B**: structlog (recommended)
  - Pros: Rich features, context binding, flexible output formats
  - Cons: Slightly more complex setup

**Decision**: Use structlog
**Rationale**:
- More powerful than python-json-logger
- Supports context binding (request ID, user ID, task ID)
- Flexible output formats (JSON for production, human-readable for dev)
- Better integration with FastAPI middleware

**Implementation Details**:
- Library: `structlog` (latest stable)
- Output format: JSON with timestamp, level, service, message, context fields
- Integration: FastAPI middleware to add request_id to all logs
- Configuration: Environment-based (JSON for prod, console for dev)

---

### 5. Multi-Cloud Kafka Configuration

**Question**: How do we handle Kafka differences across OKE, AKS, and GKE?

**Research Findings**:
- **OKE**: Oracle Streaming Service (Kafka-compatible) - primary
- **AKS**: Azure Event Hubs (Kafka-compatible) or self-hosted Redpanda
- **GKE**: Google Pub/Sub (NOT Kafka-compatible) or self-hosted Redpanda

**Decision**: Use Dapr Pub/Sub abstraction with cloud-specific components
**Rationale**:
- Dapr abstracts messaging differences
- Application code remains unchanged
- Only Dapr component YAML changes per cloud

**Implementation Details**:
- **OKE**: Dapr Pub/Sub component for Oracle Streaming Service
- **AKS**: Dapr Pub/Sub component for Azure Event Hubs (Kafka protocol)
- **GKE**: Dapr Pub/Sub component for self-hosted Redpanda (Google Pub/Sub not Kafka-compatible)
- Helm chart parameterization: `values-oke.yaml`, `values-aks.yaml`, `values-gke.yaml`

---

### 6. Grafana Dashboard Access

**Question**: How should users access Grafana dashboard on Minikube vs cloud?

**Options Considered**:
- **Minikube**: Port-forward (recommended for simplicity)
- **Cloud**: Ingress with TLS (recommended for production)

**Decision**: Port-forward for Minikube, Ingress for cloud
**Rationale**:
- Port-forward is simplest for local development
- Ingress with TLS is production-ready for cloud
- Avoids complexity of setting up ingress on Minikube

**Implementation Details**:
- **Minikube**: `kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80`
- **Cloud**: Kubernetes Ingress with TLS certificate (cert-manager)
- Documentation: Clear instructions for both approaches

---

### 7. E2E Testing Framework

**Question**: What framework should we use for E2E testing?

**Options Considered**:
- **Option A**: Python + pytest + requests (recommended)
  - Pros: Simple, familiar, easy to maintain
  - Cons: Basic features only
- **Option B**: Specialized E2E framework (Playwright, Cypress)
  - Pros: Rich features, browser automation
  - Cons: Overkill for API testing, complex setup

**Decision**: Python + pytest + requests
**Rationale**:
- Simple and maintainable
- Team already familiar with pytest
- Sufficient for API and event-driven testing
- Can add WebSocket testing with `websockets` library

**Implementation Details**:
- Framework: pytest with requests library
- Test structure: `backend/tests/e2e/test_event_flows.py`
- Fixtures: Setup test environment, create test users, cleanup
- Assertions: Verify API responses, Kafka events, WebSocket messages, audit logs

---

### 8. Production Readiness - Resource Limits

**Question**: What resource limits should we set for each service?

**Research Findings**:
- FastAPI services: Typically 100-250m CPU, 128-512Mi memory
- Kafka consumers: Typically 100-250m CPU, 256-512Mi memory
- Dapr sidecars: 50-100m CPU, 64-128Mi memory

**Decision**: Conservative limits with room for scaling
**Rationale**:
- Start conservative, adjust based on monitoring
- Ensure services can run on free-tier cloud (OKE Always Free: 2 VMs with 1 OCPU each)
- Leave headroom for HPA scaling

**Implementation Details**:
- **Backend API**: requests: 100m CPU, 128Mi memory; limits: 250m CPU, 256Mi memory
- **Recurring Task Engine**: requests: 100m CPU, 128Mi memory; limits: 250m CPU, 256Mi memory
- **Notification Service**: requests: 100m CPU, 128Mi memory; limits: 250m CPU, 256Mi memory
- **Sync Service**: requests: 100m CPU, 256Mi memory; limits: 250m CPU, 512Mi memory (WebSocket connections)
- **Audit Service**: requests: 100m CPU, 128Mi memory; limits: 250m CPU, 256Mi memory
- **Dapr Sidecars**: requests: 50m CPU, 64Mi memory; limits: 100m CPU, 128Mi memory

---

### 9. Horizontal Pod Autoscaler (HPA) Configuration

**Question**: Which services need HPA and what metrics should trigger scaling?

**Decision**: HPA for backend and sync services only
**Rationale**:
- Backend API: User-facing, variable load
- Sync Service: WebSocket connections, variable load
- Other services: Kafka consumers with predictable load (no HPA needed)

**Implementation Details**:
- **Backend API HPA**: Scale 1-5 replicas based on CPU (70% threshold)
- **Sync Service HPA**: Scale 1-3 replicas based on CPU (70% threshold)
- Min replicas: 1 (cost optimization)
- Max replicas: Conservative to fit free-tier resources

---

### 10. Cloud Deployment Differences

**Question**: What are the key differences between OKE, AKS, and GKE that need documentation?

**Research Findings**:

| Aspect | OKE | AKS | GKE |
|--------|-----|-----|-----|
| **Ingress Controller** | OCI Load Balancer | Azure Load Balancer | GCP Load Balancer |
| **Storage Class** | oci-bv (block volume) | azure-disk | standard-rwo |
| **Kafka** | Oracle Streaming Service | Azure Event Hubs | Self-hosted Redpanda |
| **Secrets** | OCI Vault (optional) | Azure Key Vault (optional) | GCP Secret Manager (optional) |
| **CLI** | oci | az | gcloud |
| **Free Tier** | Always Free (2 VMs) | $200 credits | $300 credits |

**Decision**: Document differences in deployment guide with cloud-specific values files
**Rationale**:
- Clear documentation prevents deployment errors
- Cloud-specific values files make deployment straightforward
- Helm chart parameterization handles differences

**Implementation Details**:
- Create `docs/deployment/oke-deployment.md`
- Create `docs/deployment/aks-deployment.md`
- Create `docs/deployment/gke-deployment.md`
- Create `helm/values-oke.yaml`, `helm/values-aks.yaml`, `helm/values-gke.yaml`

---

## Summary of Decisions

| Decision Area | Choice | Rationale |
|--------------|--------|-----------|
| Monitoring | kube-prometheus-stack | Complete solution, pre-configured dashboards |
| Logging | Loki + Promtail | Lightweight, Grafana integration, cloud-native |
| Dapr Metrics | ServiceMonitor CRD | Auto-discovery, standard pattern |
| Structured Logging | structlog | Rich features, context binding |
| Multi-Cloud Kafka | Dapr Pub/Sub abstraction | Cloud-agnostic application code |
| Grafana Access | Port-forward (Minikube), Ingress (cloud) | Simple for dev, production-ready for cloud |
| E2E Testing | pytest + requests | Simple, maintainable, sufficient |
| Resource Limits | Conservative with headroom | Fit free-tier, allow scaling |
| HPA | Backend + Sync only | Variable load services |
| Cloud Differences | Documented with values files | Clear guidance, parameterized deployment |

---

## Technical Unknowns Resolved

All technical unknowns have been resolved. The implementation can proceed with:
1. Deploying kube-prometheus-stack for monitoring
2. Deploying Loki + Promtail for logging
3. Configuring Dapr metrics exposure via ServiceMonitor
4. Adding structlog to all Python services
5. Creating cloud-specific Dapr Pub/Sub components
6. Writing deployment guides for OKE, AKS, GKE
7. Creating E2E test suite with pytest
8. Defining resource limits and HPA configuration
9. Creating production readiness checklist

No further research required. Ready to proceed to Phase 1 (Design & Contracts).
