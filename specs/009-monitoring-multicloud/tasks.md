# Tasks: Monitoring, Logging, and Multi-Cloud Deployment

**Input**: Design documents from `/specs/009-monitoring-multicloud/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the specification, so test tasks are excluded. Focus is on infrastructure deployment and documentation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/`, `helm/`, `docs/`, `scripts/`
- Paths follow the structure defined in plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure for monitoring, logging, and deployment guides

- [x] T001 Create helm/monitoring/ directory structure for kube-prometheus-stack wrapper chart
- [x] T002 [P] Create helm/logging/ directory structure for Loki stack wrapper chart
- [x] T003 [P] Create docs/deployment/ directory for cloud deployment guides
- [x] T004 [P] Create backend/tests/e2e/ directory for end-to-end tests

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: This feature builds on Spec 8 (Kafka + Dapr Event-Driven Architecture). All foundational work is already complete. No blocking prerequisites needed.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Production Monitoring Dashboard (Priority: P1) 🎯 MVP

**Goal**: Deploy Prometheus + Grafana for real-time visibility into microservices health and performance

**Independent Test**: Deploy Prometheus and Grafana to Minikube, verify metrics are being scraped from all 5 services (backend, recurring-task, notification, sync, audit), and confirm that pre-configured dashboards display real-time data for event processing latency, Kafka lag, WebSocket connections, and API response times.

### Monitoring Helm Chart

- [x] T005 [P] [US1] Create helm/monitoring/Chart.yaml for kube-prometheus-stack wrapper chart
- [x] T006 [P] [US1] Create helm/monitoring/values.yaml with default values for Minikube (Prometheus retention, Grafana admin password, storage config)
- [x] T007 [P] [US1] Create helm/monitoring/values-oke.yaml with OKE-specific values (storage class: oci-bv, ingress config)
- [x] T008 [P] [US1] Create helm/monitoring/values-aks.yaml with AKS-specific values (storage class: azure-disk, ingress config)
- [x] T009 [P] [US1] Create helm/monitoring/values-gke.yaml with GKE-specific values (storage class: standard-rwo, ingress config)

### Dapr Metrics Scraping

- [x] T010 [US1] Create helm/monitoring/templates/servicemonitor-dapr.yaml for Prometheus ServiceMonitor CRD to auto-discover Dapr sidecars (label selector: dapr.io/enabled=true, port: metrics, interval: 15s)

### Grafana Dashboards

- [x] T011 [P] [US1] Create helm/monitoring/templates/dashboards/service-overview.yaml ConfigMap from specs/009-monitoring-multicloud/contracts/dashboards/service-overview.json
- [x] T012 [P] [US1] Create helm/monitoring/templates/dashboards/event-processing.yaml ConfigMap for event processing dashboard (Kafka metrics, Dapr pub/sub metrics)
- [x] T013 [P] [US1] Create helm/monitoring/templates/dashboards/websocket.yaml ConfigMap for WebSocket dashboard (active connections, message delivery latency)

### Service Metrics Instrumentation

- [x] T014 [P] [US1] Add prometheus-client to backend/requirements.txt
- [x] T015 [P] [US1] Add prometheus-client to backend/services/recurring-task/requirements.txt
- [x] T016 [P] [US1] Add prometheus-client to backend/services/notification/requirements.txt
- [x] T017 [P] [US1] Add prometheus-client to backend/services/sync/requirements.txt
- [x] T018 [P] [US1] Add prometheus-client to backend/services/audit/requirements.txt

- [x] T019 [US1] Implement /metrics endpoint in backend/main.py using prometheus-fastapi-instrumentator (HTTP request metrics, custom task metrics)
- [x] T020 [P] [US1] Implement /metrics endpoint in backend/services/recurring-task/main.py (recurring task processing metrics)
- [x] T021 [P] [US1] Implement /metrics endpoint in backend/services/notification/main.py (reminder metrics)
- [x] T022 [P] [US1] Implement /metrics endpoint in backend/services/sync/main.py (WebSocket connection metrics)
- [x] T023 [P] [US1] Implement /metrics endpoint in backend/services/audit/main.py (audit log metrics)

### Deployment and Verification

- [x] T024 [US1] Update scripts/setup-minikube.sh to optionally deploy monitoring stack (helm install kube-prometheus-stack)
- [x] T025 [US1] Create scripts/deploy-monitoring.sh to deploy monitoring stack to any cluster (Minikube or cloud)
- [ ] T026 [US1] Test monitoring deployment on Minikube: verify Prometheus scrapes all services, Grafana dashboards display metrics, metrics update within 30 seconds

**Checkpoint**: At this point, User Story 1 should be fully functional - Prometheus + Grafana deployed, all services exposing metrics, dashboards displaying real-time data

---

## Phase 4: User Story 2 - Centralized Log Aggregation (Priority: P2)

**Goal**: Deploy Loki + Promtail for centralized log aggregation and enable structured JSON logging in all services

**Independent Test**: Deploy Loki and Promtail to Minikube, verify logs from all pods are aggregated, search for a specific error message across all services, and confirm results are returned within 2 seconds.

### Logging Helm Chart

- [x] T027 [P] [US2] Create helm/logging/Chart.yaml for Loki stack wrapper chart
- [x] T028 [P] [US2] Create helm/logging/values.yaml with default values for Minikube (Loki retention: 7 days, storage config, Promtail config)
- [x] T029 [P] [US2] Create helm/logging/values-oke.yaml with OKE-specific values (storage class: oci-bv, retention: 30 days for prod)
- [x] T030 [P] [US2] Create helm/logging/values-aks.yaml with AKS-specific values (storage class: azure-disk, retention: 30 days for prod)
- [x] T031 [P] [US2] Create helm/logging/values-gke.yaml with GKE-specific values (storage class: standard-rwo, retention: 30 days for prod)

### Structured Logging Implementation

- [x] T032 [P] [US2] Add structlog to backend/requirements.txt (Created structured_logger.py utility)
- [x] T033 [P] [US2] Add structlog to backend/services/recurring-task/requirements.txt
- [x] T034 [P] [US2] Add structlog to backend/services/notification/requirements.txt
- [x] T035 [P] [US2] Add structlog to backend/services/sync/requirements.txt
- [x] T036 [P] [US2] Add structlog to backend/services/audit/requirements.txt

- [x] T037 [P] [US2] Create backend/logging_config.py with structlog configuration (Created utils/structured_logger.py)
- [x] T038 [P] [US2] Create backend/services/recurring-task/logging_config.py with structlog configuration
- [x] T039 [P] [US2] Create backend/services/notification/logging_config.py with structlog configuration
- [x] T040 [P] [US2] Create backend/services/sync/logging_config.py with structlog configuration
- [x] T041 [P] [US2] Create backend/services/audit/logging_config.py with structlog configuration

- [x] T042 [US2] Update backend/main.py to use structlog with context binding (Added LoggingMiddleware)
- [x] T043 [P] [US2] Update backend/services/recurring-task/main.py to use structlog
- [x] T044 [P] [US2] Update backend/services/notification/main.py to use structlog
- [x] T045 [P] [US2] Update backend/services/sync/main.py to use structlog
- [x] T046 [P] [US2] Update backend/services/audit/main.py to use structlog

- [x] T047 [US2] Add structured logging to all routes in backend/routers/tasks.py (log task creation, updates, deletions with context)
- [x] T048 [P] [US2] Add structured logging to backend/src/api/auth.py (log authentication events)
- [x] T049 [P] [US2] N/A — no backend/routers/users.py exists; user operations handled via auth.py

### Log Queries and Documentation

- [x] T050 [US2] Create helm/logging/templates/log-queries.yaml ConfigMap with pre-defined log queries for common debugging scenarios (task creation failed, event publishing failed, WebSocket connection lost)

### Deployment and Verification

- [x] T051 [US2] Update scripts/setup-minikube.sh to optionally deploy logging stack (Added --with-logging flag)
- [x] T052 [US2] Create scripts/deploy-logging.sh for standalone logging deployment
- [ ] T053 [US2] Test logging deployment on Minikube: verify Loki collects logs from all pods, search returns results within 2 seconds, logs are structured JSON (Manual verification)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - Monitoring + Logging fully operational

---

## Phase 5: User Story 3 - Azure AKS Deployment (Priority: P3)

**Goal**: Document step-by-step deployment to Azure AKS with exact CLI commands

**Independent Test**: Follow the AKS deployment guide from scratch, deploy all services to a new AKS cluster, and verify the application is fully functional within 30 minutes.

### AKS Deployment Guide

- [x] T054 [US3] Create docs/deployment/aks-deployment.md with complete AKS deployment guide including:
  - Prerequisites (Azure CLI, kubectl, Helm, Dapr CLI)
  - Exact az CLI commands for cluster creation (resource group, AKS cluster with 2 nodes)
  - Kubeconfig setup (az aks get-credentials)
  - Dapr installation on AKS
  - Azure Event Hubs configuration for Kafka-compatible messaging
  - Helm deployment commands with values-aks.yaml for all services
  - Monitoring and logging deployment
  - Ingress configuration with TLS
  - Verification steps (health checks, E2E tests)
  - Troubleshooting section

### AKS-Specific Dapr Components

- [x] T055 [P] [US3] Create dapr-components/pubsub.kafka.aks.yaml for Azure Event Hubs Pub/Sub component (Kafka protocol, SASL authentication)
- [x] T056 [P] [US3] Update dapr-components/statestore.postgresql.yaml to work with AKS (if needed) — statestore is cloud-agnostic, no changes needed
- [x] T057 [P] [US3] Update dapr-components/secretstores.kubernetes.yaml to work with AKS (Azure Key Vault integration optional) — secretstore is cloud-agnostic, no changes needed

### Documentation

- [x] T058 [US3] Document differences between OKE and AKS in docs/deployment/cloud-comparison.md (unified comparison of networking, storage, Kafka across all clouds)

**Checkpoint**: AKS deployment guide complete and tested (if Azure account available)

---

## Phase 6: User Story 4 - Google GKE Deployment (Priority: P4)

**Goal**: Document step-by-step deployment to Google GKE with exact CLI commands

**Independent Test**: Follow the GKE deployment guide from scratch, deploy all services to a new GKE cluster, and verify the application is fully functional within 30 minutes.

### GKE Deployment Guide

- [x] T059 [US4] Create docs/deployment/gke-deployment.md with complete GKE deployment guide including:
  - Prerequisites (gcloud CLI, kubectl, Helm, Dapr CLI)
  - Exact gcloud CLI commands for cluster creation (project setup, GKE cluster with 2 nodes)
  - Kubeconfig setup (gcloud container clusters get-credentials)
  - Dapr installation on GKE
  - Self-hosted Redpanda configuration (Google Pub/Sub not Kafka-compatible)
  - Helm deployment commands with values-gke.yaml for all services
  - Monitoring and logging deployment
  - Ingress configuration with TLS
  - Verification steps (health checks, E2E tests)
  - Troubleshooting section

### GKE-Specific Dapr Components

- [x] T060 [P] [US4] Create dapr-components/pubsub.kafka.gke.yaml for self-hosted Redpanda Pub/Sub component (Kafka protocol)
- [x] T061 [P] [US4] Update dapr-components/statestore.postgresql.yaml to work with GKE (if needed) — statestore is cloud-agnostic, no changes needed
- [x] T062 [P] [US4] Update dapr-components/secretstores.kubernetes.yaml to work with GKE (GCP Secret Manager integration optional) — secretstore is cloud-agnostic, no changes needed

### Documentation

- [x] T063 [US4] Document differences between OKE/AKS/GKE in docs/deployment/cloud-comparison.md (unified comparison covering all three clouds)

**Checkpoint**: GKE deployment guide complete and tested (if GCP account available)

---

## Phase 7: User Story 5 - End-to-End Testing Automation (Priority: P5)

**Goal**: Automated E2E tests that verify complete event-driven workflows across all microservices

**Independent Test**: Run the automated E2E test script against a deployed environment, verify it tests the complete workflow (create task → recurring task → reminder → WebSocket sync → audit log), and confirm all tests pass within 5 minutes.

### E2E Test Suite

- [x] T064 [P] [US5] Create scripts/test-e2e-minikube.sh for automated E2E testing on Minikube
- [x] T065 [P] [US5] Create scripts/test-e2e-oke.sh for automated E2E testing on OKE
- [x] T066 [P] [US5] Create backend/tests/e2e/test_task_creation_flow.py to test: API → Kafka event → audit log
- [x] T067 [P] [US5] Create backend/tests/e2e/test_recurring_task_flow.py to test: Cron → new task instance → event
- [x] T068 [P] [US5] Create backend/tests/e2e/test_reminder_flow.py to test: Task due date → reminder scheduled → notification
- [x] T069 [P] [US5] Create backend/tests/e2e/test_websocket_sync_flow.py to test: Task update → WebSocket message
- [x] T070 [P] [US5] Create backend/tests/e2e/test_audit_log_flow.py to test: All operations logged with correct timestamp, user ID, event type

### CI/CD Integration

- [x] T071 [US5] Create .github/workflows/e2e-tests.yml to run E2E tests on Minikube in CI (setup Minikube, deploy services, run pytest backend/tests/e2e/, report results)
- [x] T072 [US5] Configure CI to block deployment if E2E tests fail (required status check via e2e-tests.yml)

**Checkpoint**: E2E tests complete and running in CI pipeline

---

## Phase 8: User Story 6 - Production Readiness Checklist (Priority: P6)

**Goal**: Production-ready configurations for all services (resource limits, HPA, PDB, documentation)

**Independent Test**: Review the production readiness checklist, verify all items are addressed in the Helm charts and deployment guides, and confirm that a production deployment meets all criteria.

### Resource Limits

- [x] T073 [P] [US6] Update helm/backend/values.yaml to add resource limits (requests: 250m CPU, 256Mi memory; limits: 500m CPU, 512Mi memory)
- [x] T074 [P] [US6] Update helm/recurring-task/values.yaml to add resource limits (requests: 100m CPU, 128Mi memory; limits: 250m CPU, 256Mi memory)
- [x] T075 [P] [US6] Update helm/notification/values.yaml to add resource limits (requests: 100m CPU, 128Mi memory; limits: 250m CPU, 256Mi memory)
- [x] T076 [P] [US6] Update helm/sync/values.yaml to add resource limits (requests: 100m CPU, 128Mi memory; limits: 250m CPU, 256Mi memory)
- [x] T077 [P] [US6] Update helm/audit/values.yaml to add resource limits (requests: 100m CPU, 128Mi memory; limits: 250m CPU, 256Mi memory)

### Horizontal Pod Autoscaler (HPA)

- [x] T078 [P] [US6] Create helm/backend/templates/hpa.yaml for backend service (scale 1-5 replicas based on CPU 70% threshold)
- [x] T079 [P] [US6] Create helm/sync/templates/hpa.yaml for sync service (scale 1-3 replicas based on CPU 70% threshold)
- [x] T080 [US6] Update helm/backend/values.yaml to enable HPA configuration (hpa.enabled, hpa.minReplicas, hpa.maxReplicas, hpa.targetCPUUtilizationPercentage)
- [x] T081 [US6] Update helm/sync/values.yaml to enable HPA configuration

### Pod Disruption Budgets (PDB)

- [x] T082 [P] [US6] Create helm/backend/templates/pdb.yaml for backend service (minAvailable: 1)
- [x] T083 [P] [US6] Create helm/recurring-task/templates/pdb.yaml for recurring-task service (minAvailable: 1)
- [x] T084 [P] [US6] Create helm/notification/templates/pdb.yaml for notification service (minAvailable: 1)
- [x] T085 [P] [US6] Create helm/sync/templates/pdb.yaml for sync service (minAvailable: 1)
- [x] T086 [P] [US6] Create helm/audit/templates/pdb.yaml for audit service (minAvailable: 1)

### Production Readiness Documentation

- [x] T087 [US6] Create docs/production-readiness-checklist.md with comprehensive checklist:
  - Resource limits and requests for all services ✓
  - HPA configuration for backend and sync services ✓
  - PDB configuration for all services ✓
  - Network policies (documented, implementation optional)
  - Secrets management best practices (Kubernetes Secrets, no ConfigMaps for sensitive data)
  - Database backup and disaster recovery procedures
  - Monitoring and logging operational
  - E2E tests passing
  - Health check endpoints working
  - TLS/SSL for cloud ingress
  - Log retention policies configured

**Checkpoint**: All services production-ready with resource limits, HPA, PDB, and comprehensive documentation

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements and documentation updates

- [x] T088 [P] Update README.md with monitoring and logging setup instructions (link to quickstart.md, deployment guides)
- [x] T089 [P] Update README.md with multi-cloud deployment section (OKE, AKS, GKE guides)
- [x] T090 [P] Create architecture diagram showing monitoring/logging flow (docs/architecture-monitoring-logging.md) - ASCII diagrams with full flow
- [x] T091 [P] Create architecture diagram showing multi-cloud deployment (docs/architecture-multicloud.md) - ASCII diagrams with Dapr abstraction
- [x] T092 [P] Update CLAUDE.md with monitoring/logging context and cloud deployment information
- [ ] T093 Run quickstart.md validation: follow all steps on Minikube, verify monitoring and logging work end-to-end (Manual verification required)
- [ ] T094 Review all Helm charts for consistency and best practices (Ongoing)
- [ ] T095 Review all deployment guides for clarity and completeness (Ongoing)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: No blocking prerequisites (builds on Spec 8)
- **User Stories (Phase 3-8)**: Can proceed in parallel or sequentially in priority order
  - US1 (Monitoring) - Independent
  - US2 (Logging) - Independent (but integrates with Grafana from US1)
  - US3 (AKS) - Independent (documentation only)
  - US4 (GKE) - Independent (documentation only)
  - US5 (E2E Tests) - Depends on US1 and US2 being deployed for full testing
  - US6 (Production Readiness) - Independent (updates existing Helm charts)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1 - MVP)**: Can start immediately - No dependencies
- **User Story 2 (P2)**: Can start immediately - Independent (integrates with Grafana from US1 for unified UI)
- **User Story 3 (P3)**: Can start immediately - Independent (documentation)
- **User Story 4 (P4)**: Can start immediately - Independent (documentation)
- **User Story 5 (P5)**: Should start after US1 and US2 are deployed (tests need monitoring/logging infrastructure)
- **User Story 6 (P6)**: Can start immediately - Independent (updates existing charts)

### Within Each User Story

- **US1 (Monitoring)**:
  - Helm charts before deployment scripts
  - ServiceMonitor before testing
  - Metrics instrumentation can be parallel
  - Dashboards can be parallel

- **US2 (Logging)**:
  - Helm charts before deployment
  - Structlog dependencies before configuration
  - Logging configuration before service updates
  - Service updates can be parallel

- **US3/US4 (Multi-Cloud)**:
  - Deployment guide before Dapr components
  - All tasks within story can be parallel

- **US5 (E2E Tests)**:
  - Test fixtures before test files
  - Test files can be parallel
  - CI integration after tests are written

- **US6 (Production Readiness)**:
  - Resource limits can be parallel
  - HPA templates can be parallel
  - PDB templates can be parallel
  - Documentation after all configurations

### Parallel Opportunities

- **Setup (Phase 1)**: All 4 tasks can run in parallel (different directories)
- **US1 (Monitoring)**:
  - T005-T009 (Helm charts) can run in parallel
  - T011-T013 (Dashboards) can run in parallel
  - T014-T018 (Dependencies) can run in parallel
  - T020-T023 (Metrics endpoints) can run in parallel
- **US2 (Logging)**:
  - T027-T031 (Helm charts) can run in parallel
  - T032-T036 (Dependencies) can run in parallel
  - T037-T041 (Logging config) can run in parallel
  - T043-T046 (Service updates) can run in parallel
  - T048-T049 (Router logging) can run in parallel
- **US3 (AKS)**: T055-T057 (Dapr components) can run in parallel
- **US4 (GKE)**: T060-T062 (Dapr components) can run in parallel
- **US5 (E2E Tests)**: T066-T070 (Test files) can run in parallel
- **US6 (Production Readiness)**:
  - T073-T077 (Resource limits) can run in parallel
  - T078-T079 (HPA) can run in parallel
  - T082-T086 (PDB) can run in parallel
- **Polish (Phase 9)**: T088-T092 (Documentation) can run in parallel

---

## Parallel Example: User Story 1 (Monitoring)

```bash
# Launch all Helm chart values files together:
Task: "Create helm/monitoring/values.yaml"
Task: "Create helm/monitoring/values-oke.yaml"
Task: "Create helm/monitoring/values-aks.yaml"
Task: "Create helm/monitoring/values-gke.yaml"

# Launch all Grafana dashboards together:
Task: "Create helm/monitoring/templates/dashboards/service-overview.yaml"
Task: "Create helm/monitoring/templates/dashboards/event-processing.yaml"
Task: "Create helm/monitoring/templates/dashboards/websocket.yaml"

# Launch all metrics endpoint implementations together:
Task: "Implement /metrics endpoint in backend/services/recurring-task/main.py"
Task: "Implement /metrics endpoint in backend/services/notification/main.py"
Task: "Implement /metrics endpoint in backend/services/sync/main.py"
Task: "Implement /metrics endpoint in backend/services/audit/main.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 3: User Story 1 (Monitoring)
3. **STOP and VALIDATE**: Test monitoring on Minikube independently
4. Deploy/demo if ready

**MVP Deliverable**: Production monitoring dashboard with Prometheus + Grafana showing real-time metrics for all microservices.

### Incremental Delivery

1. Complete Setup → Foundation ready
2. Add User Story 1 (Monitoring) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (Logging) → Test independently → Deploy/Demo
4. Add User Story 3 (AKS Guide) → Review and validate → Publish
5. Add User Story 4 (GKE Guide) → Review and validate → Publish
6. Add User Story 5 (E2E Tests) → Test independently → Integrate into CI
7. Add User Story 6 (Production Readiness) → Review all charts → Deploy to production
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup together (Phase 1)
2. Once Setup is done:
   - Developer A: User Story 1 (Monitoring)
   - Developer B: User Story 2 (Logging)
   - Developer C: User Story 3 (AKS Guide)
   - Developer D: User Story 4 (GKE Guide)
   - Developer E: User Story 6 (Production Readiness)
3. After US1 and US2 complete:
   - Developer F: User Story 5 (E2E Tests)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests are NOT included (not explicitly requested in specification)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- MVP = User Story 1 (Monitoring) - provides immediate value for production operations
- User Stories 3 and 4 are documentation-only (no code changes)
- User Story 5 depends on US1 and US2 for full testing capability
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Task Summary

- **Total Tasks**: 95
- **Setup Tasks**: 4
- **US1 (Monitoring)**: 22 tasks
- **US2 (Logging)**: 27 tasks
- **US3 (AKS)**: 5 tasks
- **US4 (GKE)**: 5 tasks
- **US5 (E2E Tests)**: 9 tasks
- **US6 (Production Readiness)**: 16 tasks
- **Polish**: 7 tasks

**Parallel Opportunities**: 60+ tasks can run in parallel (marked with [P])

**MVP Scope**: Phase 1 (Setup) + Phase 3 (US1 - Monitoring) = 26 tasks

**Estimated Completion**:
- MVP (US1): ~26 tasks
- MVP + Logging (US1 + US2): ~57 tasks
- Full Feature (All 6 user stories): ~95 tasks
