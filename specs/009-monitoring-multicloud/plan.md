# Implementation Plan: Monitoring, Logging, and Multi-Cloud Deployment

**Branch**: `009-monitoring-multicloud` | **Date**: 2026-02-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-monitoring-multicloud/spec.md`

## Summary

Add production-grade observability (monitoring + logging) and multi-cloud deployment guides to the existing Minikube + OKE deployment from Spec 8. This feature enables DevOps engineers to monitor system health in real-time, debug issues efficiently through centralized logging, and deploy to multiple cloud providers (OKE, AKS, GKE) as fallback options.

**Technical Approach**:
- Deploy kube-prometheus-stack (Prometheus + Grafana + Alertmanager) for metrics collection and visualization
- Deploy Loki + Promtail for centralized log aggregation
- Configure Dapr metrics exposure via Prometheus ServiceMonitor CRD for auto-discovery
- Add structlog to all Python services for structured JSON logging
- Create cloud-specific Helm values files for OKE, AKS, and GKE deployments
- Write comprehensive deployment guides for each cloud provider
- Implement E2E test suite with pytest to verify complete event-driven workflows
- Define production readiness checklist with resource limits, HPA, PDB, network policies

## Technical Context

**Language/Version**: Python 3.11+ (backend services), Bash (setup scripts)
**Primary Dependencies**:
- Monitoring: kube-prometheus-stack Helm chart (Prometheus + Grafana)
- Logging: Loki + Promtail (grafana/loki-stack Helm chart)
- Structured Logging: structlog (Python library)
- Testing: pytest + requests + websockets
- Existing: FastAPI, Dapr, Kafka/Redpanda, Kubernetes, Helm 3

**Storage**:
- Prometheus: Persistent volumes for metrics (15-day retention, configurable)
- Loki: Persistent volumes for logs (7-day dev, 30-day prod retention)
- PostgreSQL: Existing Neon database (no changes)

**Testing**:
- E2E tests: pytest with requests library for API testing
- WebSocket tests: websockets library for real-time sync testing
- Event verification: Kafka consumer to verify event publishing
- Minikube integration tests in CI/CD pipeline

**Target Platform**:
- Local: Minikube (Docker driver, 4 CPU, 8GB RAM)
- Cloud: Oracle OKE (primary, Always Free tier), Azure AKS (fallback, $200 credits), Google GKE (fallback, $300 credits)

**Project Type**: Cloud-native microservices with observability infrastructure

**Performance Goals**:
- Metrics available within 30 seconds of collection
- Log search results within 2 seconds
- Dashboard refresh rate: 30 seconds
- Prometheus scrape interval: 15 seconds

**Constraints**:
- Must work on Minikube AND all cloud providers without code changes
- Must fit within free-tier resources (OKE: 2 VMs with 1 OCPU each)
- Monitoring/logging must not significantly impact application performance
- No vendor lock-in (use Dapr abstractions for cloud-specific services)

**Scale/Scope**:
- 5 microservices to monitor (backend, recurring-task, notification, sync, audit)
- 10+ Dapr sidecars (metrics endpoints)
- 3 cloud providers (OKE, AKS, GKE)
- 10,000+ log entries per minute (estimated)
- 3 deployment guides (OKE, AKS, GKE)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Educational Clarity ✅ PASS

- **Documentation**: Comprehensive deployment guides for OKE, AKS, GKE with exact CLI commands
- **Quickstart**: Step-by-step guide for local setup and cloud deployment
- **Contracts**: Metrics specification, log format, dashboard configurations documented
- **Rationale**: Clear documentation enables learning and reproducibility

### II. Engineering Accuracy ✅ PASS

- **Cloud-Native Best Practices**:
  - Using kube-prometheus-stack (industry standard)
  - Loki for cloud-native logging
  - ServiceMonitor CRD for auto-discovery
  - Structured JSON logging with correlation IDs

- **Monitoring & Logging Requirements**:
  - Prometheus + Grafana for metrics ✅
  - Loki + Promtail for logs ✅
  - Dapr metrics exposure ✅
  - Pre-configured dashboards ✅
  - Log retention policies ✅

### III. Practical Applicability ✅ PASS

- **Local Development**: Works on Minikube with port-forward access
- **Cloud Deployment**: Parameterized Helm charts for OKE/AKS/GKE
- **Real-Time Features**: WebSocket monitoring, Kafka consumer lag tracking
- **Rationale**: Practical for both development and production environments

### IV. Spec-Driven Development ✅ PASS

- **Spec 9 Focus**: Monitoring, logging, multi-cloud deployment (NEW items only)
- **Builds on Spec 8**: Extends existing Kafka + Dapr architecture
- **No Overlap**: Does not recreate Spec 8 work
- **Rationale**: Clear separation of concerns, incremental development

### V. Ethical Responsibility ✅ PASS

- **Security**:
  - Grafana admin password stored in Kubernetes Secret
  - No credentials in logs or version control
  - TLS/SSL for cloud ingress (documented)

- **Privacy**:
  - Logs respect user privacy (no sensitive data logged)
  - Metrics aggregated (no individual user tracking)

- **Data Protection**:
  - Log retention policies (7 days dev, 30 days prod)
  - Persistent volumes for metrics and logs
  - Backup procedures documented

### VI. Reproducibility & Open Knowledge ✅ PASS

- **Reproducibility**:
  - Exact Helm chart versions documented
  - Setup scripts for Minikube
  - Cloud deployment guides with exact CLI commands

- **Open Source**:
  - All tools are open-source (Prometheus, Grafana, Loki)
  - No proprietary dependencies

- **Documentation**:
  - README updates with monitoring/logging setup
  - Architecture diagrams (to be created)
  - Troubleshooting guide in quickstart.md

### VII. Zero Broken State ✅ PASS

- **Quality**:
  - E2E tests verify complete workflows
  - Minikube deployment test in CI pipeline
  - Health check endpoints for all services

- **Stability**:
  - Monitoring does not impact application stability
  - Graceful degradation if monitoring fails
  - No data loss on service restart

**Constitution Check Result**: ✅ ALL GATES PASSED

## Project Structure

### Documentation (this feature)

```text
specs/009-monitoring-multicloud/
├── spec.md                          # Feature specification (completed)
├── plan.md                          # This file (implementation plan)
├── research.md                      # Phase 0: Technical decisions (completed)
├── data-model.md                    # Phase 1: Data model (N/A - infrastructure)
├── quickstart.md                    # Phase 1: Setup guide (completed)
├── contracts/                       # Phase 1: API contracts (completed)
│   ├── log-format.json             # Structured log format specification
│   ├── metrics-specification.md    # Prometheus metrics specification
│   └── dashboards/                 # Grafana dashboard configurations
│       └── service-overview.json   # Main service overview dashboard
├── checklists/
│   └── requirements.md             # Specification quality checklist
└── tasks.md                        # Phase 2: Implementation tasks (NOT created yet)
```

### Source Code (repository root)

```text
# Monitoring & Logging Infrastructure
helm/
├── monitoring/
│   ├── Chart.yaml                  # kube-prometheus-stack wrapper chart
│   ├── values.yaml                 # Default values (Minikube)
│   ├── values-oke.yaml             # OKE-specific values
│   ├── values-aks.yaml             # AKS-specific values
│   ├── values-gke.yaml             # GKE-specific values
│   └── templates/
│       ├── servicemonitor-dapr.yaml    # Dapr metrics scraping
│       └── dashboards/                 # Dashboard ConfigMaps
│           └── service-overview.yaml
├── logging/
│   ├── Chart.yaml                  # Loki stack wrapper chart
│   ├── values.yaml                 # Default values (Minikube)
│   ├── values-oke.yaml             # OKE-specific values
│   ├── values-aks.yaml             # AKS-specific values
│   └── values-gke.yaml             # GKE-specific values

# Updated Service Helm Charts (add resource limits, HPA, PDB)
helm/backend/
├── values.yaml                     # Add resource limits, HPA config
├── templates/
│   ├── hpa.yaml                    # Horizontal Pod Autoscaler (NEW)
│   └── pdb.yaml                    # Pod Disruption Budget (NEW)

helm/recurring-task/
├── values.yaml                     # Add resource limits
└── templates/
    └── pdb.yaml                    # Pod Disruption Budget (NEW)

helm/notification/
├── values.yaml                     # Add resource limits
└── templates/
    └── pdb.yaml                    # Pod Disruption Budget (NEW)

helm/sync/
├── values.yaml                     # Add resource limits, HPA config
└── templates/
    ├── hpa.yaml                    # Horizontal Pod Autoscaler (NEW)
    └── pdb.yaml                    # Pod Disruption Budget (NEW)

helm/audit/
├── values.yaml                     # Add resource limits
└── templates/
    └── pdb.yaml                    # Pod Disruption Budget (NEW)

# Backend Services (add structured logging)
backend/
├── requirements.txt                # Add structlog dependency
├── logging_config.py               # Structlog configuration (NEW)
├── main.py                         # Update to use structlog
├── routers/
│   └── tasks.py                    # Add structured logging to all routes
└── tests/
    └── e2e/
        └── test_event_flows.py     # E2E test suite (NEW)

backend/services/recurring-task/
├── requirements.txt                # Add structlog dependency
├── logging_config.py               # Structlog configuration (NEW)
└── main.py                         # Update to use structlog

backend/services/notification/
├── requirements.txt                # Add structlog dependency
├── logging_config.py               # Structlog configuration (NEW)
└── main.py                         # Update to use structlog

backend/services/sync/
├── requirements.txt                # Add structlog dependency
├── logging_config.py               # Structlog configuration (NEW)
└── main.py                         # Update to use structlog

backend/services/audit/
├── requirements.txt                # Add structlog dependency
├── logging_config.py               # Structlog configuration (NEW)
└── main.py                         # Update to use structlog

# Deployment Guides
docs/
└── deployment/
    ├── oke-deployment.md           # Oracle OKE deployment guide (NEW)
    ├── aks-deployment.md           # Azure AKS deployment guide (NEW)
    └── gke-deployment.md           # Google GKE deployment guide (NEW)

# Setup Scripts (update for monitoring/logging)
scripts/
├── setup-minikube.sh               # Update to install monitoring/logging
└── deploy-monitoring.sh            # Deploy monitoring stack (NEW)

# CI/CD (update for E2E tests)
.github/
└── workflows/
    ├── test.yml                    # Add E2E tests to CI pipeline
    └── deploy.yml                  # Update deployment workflow

# Production Readiness
docs/
└── production-readiness-checklist.md   # Production checklist (NEW)
```

**Structure Decision**: This is a cloud-native infrastructure feature that extends the existing microservices architecture from Spec 8. The structure follows Kubernetes best practices with Helm charts for monitoring/logging infrastructure, updated service charts with production-ready configurations (resource limits, HPA, PDB), and comprehensive deployment guides for multi-cloud support.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. All constitution gates passed. No complexity justification needed.

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Grafana Dashboard (UI)                       │
│  - Service Overview Dashboard                                    │
│  - Event Processing Dashboard                                    │
│  - WebSocket Dashboard                                           │
└────────────┬────────────────────────────────┬───────────────────┘
             │                                │
             │ Queries                        │ Queries
             ▼                                ▼
┌─────────────────────────┐      ┌─────────────────────────┐
│   Prometheus (Metrics)   │      │    Loki (Logs)          │
│  - Scrapes every 15s     │      │  - Aggregates logs      │
│  - 15-day retention      │      │  - 7/30-day retention   │
└────────────┬─────────────┘      └────────────┬────────────┘
             │                                  │
             │ Scrapes                          │ Collects
             ▼                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Backend    │  │ Recurring    │  │ Notification │          │
│  │   Service    │  │ Task Engine  │  │   Service    │          │
│  │ + Dapr       │  │ + Dapr       │  │ + Dapr       │          │
│  │ + Promtail   │  │ + Promtail   │  │ + Promtail   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │    Sync      │  │    Audit     │                            │
│  │   Service    │  │   Service    │                            │
│  │ + Dapr       │  │ + Dapr       │                            │
│  │ + Promtail   │  │ + Promtail   │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘

Metrics Flow:
1. Services expose /metrics endpoint (FastAPI)
2. Dapr sidecars expose /metrics on port 9090
3. Prometheus scrapes all endpoints every 15s
4. Grafana queries Prometheus for visualization

Logs Flow:
1. Services output structured JSON logs to stdout
2. Promtail collects logs from all pods
3. Promtail forwards logs to Loki
4. Grafana queries Loki for log search/visualization
```

### Multi-Cloud Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Application Code (Unchanged)                  │
│  - Backend API, Recurring Task, Notification, Sync, Audit        │
└────────────┬────────────────────────────────┬───────────────────┘
             │                                │
             │ Uses Dapr Abstractions         │
             ▼                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Dapr Components (Cloud-Specific)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │     OKE      │  │     AKS      │  │     GKE      │          │
│  │ Oracle       │  │ Azure Event  │  │ Redpanda     │          │
│  │ Streaming    │  │ Hubs (Kafka) │  │ (self-hosted)│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘

Key Insight: Application code remains unchanged across clouds.
Only Dapr component YAML files change per cloud provider.
```

---

## Implementation Phases

### Phase 1: Monitoring Stack (P1 - MVP)

**Goal**: Deploy Prometheus + Grafana for real-time metrics

**Tasks**:
1. Create Helm chart wrapper for kube-prometheus-stack
2. Create ServiceMonitor CRD for Dapr metrics scraping
3. Create Grafana dashboard ConfigMaps (service overview, event processing, WebSocket)
4. Add prometheus-client to all Python services
5. Expose /metrics endpoint on all services
6. Test on Minikube: verify metrics collection and dashboard display
7. Create cloud-specific values files (values-oke.yaml, values-aks.yaml, values-gke.yaml)

**Acceptance Criteria**:
- Prometheus scrapes metrics from all 5 services + Dapr sidecars
- Grafana displays real-time metrics with <30s delay
- Dashboards show: HTTP request rate, latency p95, Kafka consumer lag, WebSocket connections
- Works identically on Minikube and cloud

### Phase 2: Logging Stack (P2)

**Goal**: Deploy Loki + Promtail for centralized log aggregation

**Tasks**:
1. Create Helm chart wrapper for Loki stack
2. Add structlog to all Python services (requirements.txt)
3. Create logging_config.py for structured JSON logging
4. Update all services to use structlog with context binding (request_id, user_id, task_id)
5. Configure log retention (7 days dev, 30 days prod)
6. Test on Minikube: verify log collection and search
7. Create pre-defined log queries for common debugging scenarios

**Acceptance Criteria**:
- Loki collects logs from all pods
- Logs are structured JSON with timestamp, level, service, message, context
- Log search returns results within 2 seconds
- Log retention policies enforced
- Works identically on Minikube and cloud

### Phase 3: Multi-Cloud Deployment Guides (P3, P4)

**Goal**: Document deployment to OKE, AKS, GKE

**Tasks**:
1. Write OKE deployment guide (docs/deployment/oke-deployment.md)
   - Exact oci CLI commands for cluster creation
   - Oracle Streaming Service configuration
   - Helm deployment with values-oke.yaml
2. Write AKS deployment guide (docs/deployment/aks-deployment.md)
   - Exact az CLI commands for cluster creation
   - Azure Event Hubs configuration
   - Helm deployment with values-aks.yaml
3. Write GKE deployment guide (docs/deployment/gke-deployment.md)
   - Exact gcloud CLI commands for cluster creation
   - Redpanda self-hosted configuration
   - Helm deployment with values-gke.yaml
4. Document differences (networking, ingress, storage, Kafka)
5. Test deployment on at least one cloud provider (OKE preferred)

**Acceptance Criteria**:
- Deployment guides are complete with exact CLI commands
- Differences between clouds are clearly documented
- Deployment completes in <30 minutes following guide
- All features work on cloud (verified via E2E tests)

### Phase 4: E2E Testing Automation (P5)

**Goal**: Automated E2E tests for complete event-driven workflows

**Tasks**:
1. Create backend/tests/e2e/test_event_flows.py
2. Implement test fixtures (setup environment, create test users, cleanup)
3. Write E2E tests:
   - test_task_creation_flow: API → Kafka event → audit log
   - test_recurring_task_flow: Cron → new task instance → event
   - test_reminder_flow: Task due date → reminder scheduled → notification
   - test_websocket_sync_flow: Task update → WebSocket message
   - test_audit_log_flow: All operations logged
4. Integrate E2E tests into GitHub Actions CI/CD pipeline
5. Configure tests to run on Minikube in CI

**Acceptance Criteria**:
- All E2E tests pass locally and in CI
- Tests complete within 5 minutes
- Tests verify complete workflows across all services
- CI blocks deployment if tests fail

### Phase 5: Production Readiness (P6)

**Goal**: Production-ready configurations for all services

**Tasks**:
1. Add resource limits to all Helm charts (CPU, memory)
2. Create HPA for backend and sync services
3. Create PDB for all services (ensure minimum replicas during updates)
4. Document network policies (future work, out of scope for implementation)
5. Document secrets management best practices
6. Document backup and disaster recovery procedures
7. Create production readiness checklist (docs/production-readiness-checklist.md)
8. Review and validate all items in checklist

**Acceptance Criteria**:
- All services have resource limits defined
- HPA configured for backend and sync services
- PDB configured for all services
- Production readiness checklist 100% complete
- Documentation covers all production requirements

---

## Key Design Decisions

### 1. Monitoring: kube-prometheus-stack vs Separate Charts

**Decision**: Use kube-prometheus-stack Helm chart

**Rationale**:
- Complete monitoring solution out-of-the-box
- Pre-configured Grafana dashboards for Kubernetes
- Includes Alertmanager for future alerting
- Widely adopted in production environments
- Easier to maintain and upgrade

**Trade-offs**:
- Larger footprint than separate charts
- More components than strictly needed
- Accepted because: Completeness and ease of use outweigh footprint concerns

### 2. Logging: Loki vs ELK Stack

**Decision**: Use Loki + Promtail

**Rationale**:
- Integrates seamlessly with Grafana (single UI)
- Designed for cloud-native environments
- Lower resource footprint (critical for free-tier cloud)
- Simpler architecture (no Elasticsearch cluster)
- Sufficient for our use case

**Trade-offs**:
- Less mature than ELK
- Fewer advanced features
- Accepted because: Simplicity and resource efficiency are priorities

### 3. Dapr Metrics: Manual vs Auto-Discovery

**Decision**: Use Prometheus ServiceMonitor CRD for auto-discovery

**Rationale**:
- Automatic discovery of Dapr sidecars
- No manual configuration per service
- Standard Kubernetes pattern
- Works with kube-prometheus-stack out-of-the-box

**Trade-offs**:
- Requires ServiceMonitor CRD (kube-prometheus-stack provides this)
- Accepted because: Auto-discovery is more maintainable

### 4. Structured Logging: python-json-logger vs structlog

**Decision**: Use structlog

**Rationale**:
- More powerful than python-json-logger
- Supports context binding (request_id, user_id, task_id)
- Flexible output formats (JSON for prod, console for dev)
- Better integration with FastAPI middleware

**Trade-offs**:
- Slightly more complex setup
- Accepted because: Rich features justify complexity

### 5. Multi-Cloud Kafka: Cloud-Managed vs Self-Hosted

**Decision**: Use Dapr Pub/Sub abstraction with cloud-specific components

**Rationale**:
- Application code remains unchanged
- Only Dapr component YAML changes per cloud
- Leverages cloud-managed services where available (Oracle Streaming, Azure Event Hubs)
- Falls back to self-hosted Redpanda for GKE (Google Pub/Sub not Kafka-compatible)

**Trade-offs**:
- Requires maintaining multiple Dapr component files
- Accepted because: Cloud-agnostic code is more valuable

### 6. Grafana Access: Port-Forward vs Ingress

**Decision**: Port-forward for Minikube, Ingress for cloud

**Rationale**:
- Port-forward is simplest for local development
- Ingress with TLS is production-ready for cloud
- Avoids complexity of setting up ingress on Minikube

**Trade-offs**:
- Different access methods for local vs cloud
- Accepted because: Simplicity for local dev is priority

### 7. E2E Testing: pytest vs Specialized Framework

**Decision**: Use pytest + requests

**Rationale**:
- Simple and maintainable
- Team already familiar with pytest
- Sufficient for API and event-driven testing
- Can add WebSocket testing with websockets library

**Trade-offs**:
- Basic features only (no browser automation)
- Accepted because: API testing is sufficient for our use case

### 8. Resource Limits: Aggressive vs Conservative

**Decision**: Conservative limits with room for scaling

**Rationale**:
- Start conservative, adjust based on monitoring
- Ensure services fit on free-tier cloud (OKE: 2 VMs with 1 OCPU each)
- Leave headroom for HPA scaling

**Trade-offs**:
- May under-utilize resources initially
- Accepted because: Free-tier constraints are priority

### 9. HPA: All Services vs Selective

**Decision**: HPA for backend and sync services only

**Rationale**:
- Backend API: User-facing, variable load
- Sync Service: WebSocket connections, variable load
- Other services: Kafka consumers with predictable load (no HPA needed)

**Trade-offs**:
- Manual scaling for other services if needed
- Accepted because: Variable load services benefit most from HPA

### 10. Cloud Deployment: Single Guide vs Per-Cloud Guides

**Decision**: Separate deployment guide per cloud provider

**Rationale**:
- Clear, focused instructions per cloud
- Exact CLI commands for each provider
- Easier to follow than a single guide with conditionals

**Trade-offs**:
- More documentation to maintain
- Accepted because: Clarity is more important than brevity

---

## Risk Analysis

### Risk 1: Prometheus Storage Fills Up

**Likelihood**: Medium
**Impact**: High (metrics collection stops)

**Mitigation**:
- Configure metric retention period (15 days default)
- Set storage limits in Helm values
- Monitor Prometheus storage usage
- Document storage cleanup procedures

### Risk 2: Loki Storage Fills Up

**Likelihood**: High (with high log volume)
**Impact**: High (log collection stops)

**Mitigation**:
- Configure log retention (7 days dev, 30 days prod)
- Set storage limits in Helm values
- Monitor Loki storage usage
- Document log volume reduction strategies

### Risk 3: Cloud Provider Differences Break Deployment

**Likelihood**: Medium
**Impact**: High (deployment fails)

**Mitigation**:
- Use Dapr abstractions to minimize cloud-specific code
- Test deployment on at least one cloud provider (OKE)
- Document differences clearly in deployment guides
- Provide cloud-specific Helm values files

### Risk 4: E2E Tests Are Flaky

**Likelihood**: Medium
**Impact**: Medium (CI pipeline unreliable)

**Mitigation**:
- Add appropriate wait times in tests
- Implement retry logic for transient failures
- Use fixtures for proper setup/cleanup
- Run tests multiple times in CI to detect flakiness

### Risk 5: Monitoring Impacts Application Performance

**Likelihood**: Low
**Impact**: High (application slowdown)

**Mitigation**:
- Use efficient metrics libraries (prometheus-client)
- Limit metric cardinality (avoid high-cardinality labels like user_id in metric names)
- Configure appropriate scrape intervals (15s default)
- Monitor application performance after adding metrics

### Risk 6: Free-Tier Resources Insufficient

**Likelihood**: Medium
**Impact**: High (deployment fails or services crash)

**Mitigation**:
- Conservative resource limits
- Test on Minikube first (similar resource constraints)
- Document minimum resource requirements
- Provide guidance on scaling up if needed

### Risk 7: Structured Logging Breaks Existing Logs

**Likelihood**: Low
**Impact**: Medium (log parsing issues)

**Mitigation**:
- Test structured logging locally first
- Gradual rollout (one service at a time)
- Keep existing log format during transition
- Document log format changes

---

## Success Metrics

### Monitoring Success Metrics

- ✅ Prometheus scrapes metrics from all 5 services + Dapr sidecars
- ✅ Grafana displays metrics with <30s delay
- ✅ Dashboards show: HTTP request rate, latency p95, Kafka consumer lag, WebSocket connections
- ✅ Monitoring works identically on Minikube and cloud

### Logging Success Metrics

- ✅ Loki collects logs from all pods
- ✅ Log search returns results within 2 seconds
- ✅ Logs are structured JSON with required fields
- ✅ Log retention policies enforced

### Multi-Cloud Success Metrics

- ✅ Deployment to OKE completes in <30 minutes
- ✅ Deployment to AKS completes in <30 minutes (if tested)
- ✅ Deployment to GKE completes in <30 minutes (if tested)
- ✅ All features work on cloud (verified via E2E tests)

### E2E Testing Success Metrics

- ✅ All E2E tests pass locally and in CI
- ✅ Tests complete within 5 minutes
- ✅ Tests verify complete workflows across all services
- ✅ CI blocks deployment if tests fail

### Production Readiness Success Metrics

- ✅ All services have resource limits defined
- ✅ HPA configured for backend and sync services
- ✅ PDB configured for all services
- ✅ Production readiness checklist 100% complete

---

## References

- **Research**: [research.md](./research.md) - Technical decisions and alternatives considered
- **Data Model**: [data-model.md](./data-model.md) - N/A for infrastructure feature
- **Contracts**: [contracts/](./contracts/) - Log format, metrics specification, dashboards
- **Quickstart**: [quickstart.md](./quickstart.md) - Setup guide for local and cloud
- **Specification**: [spec.md](./spec.md) - Feature requirements and user stories
- **Constitution**: [.specify/memory/constitution.md](../../.specify/memory/constitution.md) - Project principles

---

## Next Steps

1. Run `/sp.tasks` to generate implementation tasks from this plan
2. Review and approve tasks.md
3. Run `/sp.implement` to execute tasks
4. Create PR and merge to main after all tests pass
5. Deploy to OKE and verify monitoring/logging in production

---

**Plan Status**: ✅ COMPLETE - Ready for task generation
**Constitution Check**: ✅ ALL GATES PASSED
**Phase 0 (Research)**: ✅ COMPLETE
**Phase 1 (Design & Contracts)**: ✅ COMPLETE
