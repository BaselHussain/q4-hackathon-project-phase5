<!--
  Sync Impact Report
  ==================
  Version change: 2.0.0 → 3.0.0

  Modified principles:
    - I. Spec-Driven Development → I. Educational Clarity (reordered and expanded)
    - II. AI-First Stateless Architecture → II. Engineering Accuracy (replaced with cloud-native focus)
    - III. Secure Authentication & Authorization → V. Ethical Responsibility (expanded scope)
    - IV. Persistent Data & Conversation State → (removed - superseded by event-driven architecture)
    - V. OpenAI Agents SDK Integration → (removed - Phase 3 specific)
    - VI. Stateless Tool Design → (removed - Phase 3 specific)
    - VII. Conversational UI Experience → (removed - Phase 3 specific)
    - VIII. MCP Server Protocol → (removed - Phase 3 specific)

  Added sections:
    - I. Educational Clarity (NEW - comprehensive documentation requirements)
    - II. Engineering Accuracy (NEW - cloud-native architecture requirements)
    - III. Practical Applicability (NEW - deployment and usability requirements)
    - IV. Spec-Driven Development (EXPANDED - three-spec approach for Phase 5)
    - VI. Reproducibility & Open Knowledge (NEW - open source requirements)
    - VII. Zero Broken State (NEW - quality and stability requirements)
    - Phase 5 Technology Stack Requirements (NEW)
    - Advanced Todo Features (NEW)
    - Event-Driven Architecture Requirements (NEW)
    - Dapr Integration Requirements (NEW)
    - Kubernetes Deployment Requirements (NEW)
    - CI/CD Requirements (NEW)
    - Monitoring & Logging Requirements (NEW)

  Removed sections:
    - Phase 3 AI-specific principles (MCP, OpenAI Agents SDK, ChatKit)
    - Conversational UI requirements
    - Stateless tool design

  Templates requiring updates:
    - .specify/templates/plan-template.md: ✅ No changes needed (generic)
    - .specify/templates/spec-template.md: ✅ No changes needed (generic)
    - .specify/templates/tasks-template.md: ✅ No changes needed (generic)

  Follow-up TODOs:
    - None - all placeholders filled
-->

# Todo AI Chatbot Constitution (Phase 5 - Advanced Cloud Deployment)

## Core Purpose

Transform the Todo AI Chatbot into an advanced, event-driven, Kubernetes-deployed microservices application demonstrating cloud-native, scalable architecture with distributed runtime (Dapr), message streaming (Kafka), and production deployment capabilities. All implementation MUST be via Claude Code only - no manual coding allowed.

## Core Principles

### I. Educational Clarity (NON-NEGOTIABLE)

All specifications, plans, and tasks MUST be clearly documented with exact commands and step-by-step instructions. Documentation MUST enable any developer to reproduce the entire system from scratch.

**Documentation requirements:**
- README.md MUST contain complete Minikube setup instructions with exact commands
- README.md MUST contain cloud deployment instructions for Azure AKS, Google GKE, and Oracle OKE
- CLAUDE.md MUST document the complete agentic workflow for all three specs
- All environment variables MUST be documented in `.env.example` files
- Helm chart values MUST be documented with comments explaining each configuration option
- CI/CD pipeline steps MUST be documented with clear explanations
- Architecture diagrams MUST be included showing event flow and service interactions

**Rationale**: Educational clarity ensures knowledge transfer, reproducibility, and enables the project to serve as a reference implementation for cloud-native patterns.

### II. Engineering Accuracy (NON-NEGOTIABLE)

All technical implementations MUST follow cloud-native best practices and production-grade patterns. No shortcuts or toy implementations allowed.

**Advanced Todo Features (MUST implement all):**
- Recurring tasks with cron-like scheduling (daily, weekly, monthly, custom)
- Due dates and reminders with configurable notification timing
- Priority levels (high, medium, low) with sorting and filtering
- Tags for categorization with multi-tag support
- Search functionality across task title, description, and tags
- Filter by status, priority, tags, due date range
- Sort by created date, due date, priority, completion status

**Event-Driven Architecture (MUST implement):**
- Kafka or Redpanda for message streaming
- Event topics: task.created, task.updated, task.completed, task.deleted, reminder.due, task.recurring
- Audit log topic for all state changes
- Real-time sync topic for WebSocket updates to connected clients
- Event sourcing pattern for task state changes
- Consumer groups for scalable event processing

**Dapr Integration (MUST use all components):**
- Pub/Sub component for Kafka integration
- State Store component for PostgreSQL state management
- Cron Binding for recurring task engine
- Secrets component for secure credential management
- Service Invocation for inter-service communication
- No direct Kafka or database client code - all via Dapr APIs

**Kubernetes Deployment (MUST support both):**
- Local development on Minikube with exact setup commands
- Production deployment to Azure AKS, Google GKE, or Oracle OKE
- Helm charts for all services (frontend, backend, recurring-engine, reminder-service)
- Proper resource limits and requests
- Health checks (liveness and readiness probes)
- ConfigMaps and Secrets for configuration
- Horizontal Pod Autoscaling (HPA) configuration

**CI/CD Pipeline (MUST implement):**
- GitHub Actions workflows for automated testing and deployment
- Build Docker images for all services
- Run tests in CI pipeline
- Deploy to Minikube for integration testing
- Deploy to cloud environments with approval gates
- Automated Helm chart validation

**Monitoring & Logging (MUST implement):**
- Prometheus metrics collection or equivalent
- Structured logging with correlation IDs
- Service health endpoints
- Basic dashboards for key metrics (task operations, event processing, API latency)

**Rationale**: Engineering accuracy ensures the project demonstrates real-world production patterns, not toy implementations. This makes it valuable as a learning resource and portfolio piece.

### III. Practical Applicability (NON-NEGOTIABLE)

The system MUST be runnable locally and deployable to cloud with clear, exact commands. No "figure it out yourself" steps allowed.

**Local Development (MUST work):**
- Runnable on Minikube with documented setup script
- All dependencies installable via standard tools (UV, npm/pnpm, Helm, kubectl, Dapr CLI)
- `.env.example` files with all required variables
- Single command to start entire stack locally
- Clear instructions for accessing services (URLs, ports)

**Cloud Deployment (MUST work):**
- Deployable to Azure AKS using free $200 credits
- Deployable to Google GKE using free $300 credits
- Deployable to Oracle OKE using Always Free tier
- Helm charts parameterized for different environments
- Clear instructions for cloud provider setup
- No vendor lock-in - Dapr abstracts infrastructure

**Real-Time Features (MUST work without polling):**
- Task sync across clients via Kafka + WebSocket
- Reminders triggered by events, not polling
- Recurring tasks created by cron binding, not polling
- Event-driven architecture eliminates polling overhead

**Rationale**: Practical applicability ensures the project is actually usable, not just theoretical. Developers should be able to run it locally and deploy to cloud following exact instructions.

### IV. Spec-Driven Development (NON-NEGOTIABLE)

All development MUST follow Spec-Driven Development (SDD) methodology. Features MUST be fully specified before implementation. No manual coding allowed - all implementation MUST be agent-driven using Claude Code tools.

**Phase 5 requires three separate specs in this exact order:**

1. **Spec 1: Advanced Todo Features**
   - Recurring tasks with cron scheduling
   - Due dates and reminders
   - Priorities (high, medium, low)
   - Tags for categorization
   - Search, filter, and sort functionality
   - Database schema updates
   - API endpoint changes

2. **Spec 2: Kafka + Dapr Event-Driven Architecture**
   - Kafka/Redpanda topic design
   - Dapr Pub/Sub component configuration
   - Event producers and consumers
   - Recurring task engine (Dapr Cron Binding)
   - Reminder service (event-driven)
   - Audit log service
   - Real-time sync service (WebSocket)
   - Dapr State Store for PostgreSQL
   - Dapr Secrets management

3. **Spec 3: Local (Minikube) + Cloud (AKS/GKE/OKE) Deployment**
   - Helm charts for all services
   - Kubernetes manifests (Deployments, Services, ConfigMaps, Secrets)
   - Minikube setup script with Dapr and Kafka installation
   - GitHub Actions CI/CD workflows
   - Cloud provider setup instructions (AKS, GKE, OKE)
   - Monitoring and logging setup (Prometheus or equivalent)
   - Health checks and autoscaling

**Spec execution order (MUST follow):**
- Each spec MUST be completed before starting the next
- Each spec MUST have its own plan.md and tasks.md
- Each spec MUST be independently testable
- Every feature MUST be traceable to a spec

**Rationale**: Spec-Driven Development ensures systematic, traceable implementation. The three-spec approach breaks down the complex Phase 5 work into manageable, sequential pieces.

### V. Ethical Responsibility (NON-NEGOTIABLE)

Security, privacy, and data protection MUST be built-in from the start, not added later.

**Security requirements:**
- Existing Better Auth with JWT tokens MUST be preserved from Phase 2
- All API endpoints MUST have JWT verification middleware
- User isolation MUST be strictly enforced - users can only access their own data
- Secrets MUST be managed via Dapr Secrets component, never hardcoded
- Kubernetes Secrets MUST be used for sensitive configuration
- No credentials in code, logs, or version control

**Privacy requirements:**
- Reminders and notifications MUST be private per user
- Event data MUST include user_id for isolation
- Audit logs MUST respect user privacy
- No unnecessary data collection
- Clear data retention policies

**Data protection:**
- Database backups MUST be configured
- State Store (Dapr) MUST use PostgreSQL with proper persistence
- Event data MUST be durable (Kafka retention policies)
- No data loss on service restart

**Rationale**: Ethical responsibility ensures the system is secure, respects user privacy, and protects data. This is non-negotiable for any production system.

### VI. Reproducibility & Open Knowledge (NON-NEGOTIABLE)

The project MUST be fully reproducible by any developer with access to the repository and documented tools.

**Open Source requirements:**
- Public GitHub repository
- All code version-controlled
- No proprietary dependencies
- Clear licensing (if applicable)

**Reproducibility requirements:**
- `.env.example` files for all services
- Exact tool versions documented (Python, Node.js, Helm, kubectl, Dapr CLI)
- Dependency lock files committed (requirements.txt, package-lock.json)
- Minikube setup script that works on fresh installation
- Cloud deployment scripts that work with new accounts
- No "works on my machine" issues

**Documentation requirements:**
- README.md with complete setup instructions
- Architecture documentation with diagrams
- API documentation (OpenAPI/Swagger)
- Helm chart documentation
- Troubleshooting guide

**Rationale**: Reproducibility ensures the project serves as a valuable learning resource and reference implementation. Open knowledge sharing benefits the entire developer community.

### VII. Zero Broken State (NON-NEGOTIABLE)

The main branch MUST always be in a working state. No broken commits, no "fix later" TODOs in main branch.

**Quality requirements:**
- All PRs MUST pass CI/CD pipeline before merge
- All PRs MUST be tested on Minikube before merge
- No crashes on normal usage paths
- Graceful error handling for all edge cases
- Clear error messages for users

**Testing requirements:**
- Integration tests for critical paths (chat → create task → reminder → real-time sync)
- Minikube deployment test in CI pipeline
- Health check endpoints for all services
- Smoke tests for basic functionality

**Stability requirements:**
- Services MUST restart cleanly after failure
- State MUST be preserved across restarts (via Dapr State Store)
- Events MUST be processed reliably (Kafka consumer groups)
- No data loss on service restart

**Development workflow:**
- Feature branches for all work
- PRs reviewed before merge
- Main branch protected
- Rollback plan for failed deployments

**Rationale**: Zero broken state ensures the project is always demonstrable and usable. This is critical for hackathon presentations and portfolio showcases.

## Technology Stack Requirements

### Phase 5 Stack (Additions to Phase 1-4)

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Message Streaming** | Kafka or Redpanda | Event-driven architecture, pub/sub messaging |
| **Distributed Runtime** | Dapr | Pub/Sub, State Store, Cron Binding, Secrets, Service Invocation |
| **Container Orchestration** | Kubernetes (Minikube local, AKS/GKE/OKE cloud) | Service deployment, scaling, management |
| **Package Manager** | Helm 3 | Kubernetes application packaging and deployment |
| **CI/CD** | GitHub Actions | Automated testing, building, deployment |
| **Monitoring** | Prometheus or equivalent | Metrics collection and monitoring |
| **Logging** | Structured logging with correlation IDs | Distributed tracing and debugging |
| **Database** | Neon PostgreSQL (existing) | Primary data store + Dapr State Store |
| **Backend** | FastAPI (existing) | REST API + event producers |
| **Frontend** | Next.js (existing) | UI + WebSocket client |
| **Auth** | Better Auth + JWT (existing) | User authentication |

### New Services (Phase 5)

1. **Backend API Service** (existing, enhanced)
   - REST API endpoints for advanced todo features
   - Event producers (publish to Kafka via Dapr)
   - WebSocket server for real-time sync
   - JWT authentication middleware

2. **Recurring Task Engine** (NEW)
   - Dapr Cron Binding for scheduled execution
   - Reads recurring task definitions from database
   - Creates new task instances based on schedule
   - Publishes task.created events

3. **Reminder Service** (NEW)
   - Subscribes to task.created and task.updated events
   - Schedules reminders based on due dates
   - Publishes reminder.due events
   - Sends notifications (WebSocket or other channels)

4. **Audit Log Service** (NEW)
   - Subscribes to all task events
   - Writes audit trail to database
   - Provides audit query API

5. **Real-Time Sync Service** (NEW)
   - Subscribes to all task events
   - Pushes updates to connected WebSocket clients
   - Maintains client connection state

### New Dependencies (Phase 5)

**Backend (Python):**
- `dapr` - Dapr Python SDK
- `kafka-python` or `confluent-kafka` (optional, if not using Dapr)
- `websockets` or `fastapi-websocket` - WebSocket support
- `croniter` - Cron expression parsing for recurring tasks

**Infrastructure:**
- Helm 3.x - Kubernetes package manager
- kubectl 1.28+ - Kubernetes CLI
- Dapr CLI 1.12+ - Dapr runtime management
- Minikube 1.32+ - Local Kubernetes cluster
- Docker 24+ - Container runtime

**Cloud CLIs (for deployment):**
- Azure CLI (for AKS)
- gcloud CLI (for GKE)
- oci CLI (for OKE)

### Existing Stack (Preserved from Phase 1-4)

- Python 3.11+ with FastAPI 0.109+
- SQLModel 0.0.14+ for ORM
- asyncpg 0.29+ for async PostgreSQL
- Next.js 16+ with App Router
- Better Auth for authentication
- Neon Serverless PostgreSQL

## Development Workflow

### Code Quality Standards

- All code MUST follow consistent style guidelines
- Meaningful commit messages following conventional commits
- All implementation via Claude Code only
- No direct pushes to main branch
- All PRs MUST pass CI/CD pipeline

### Documentation Standards

- README.md MUST contain complete setup instructions (local + cloud)
- CLAUDE.md MUST have complete agentic workflow for all three specs
- All environment variables MUST be documented in `.env.example`
- API documentation MUST be up-to-date (OpenAPI/Swagger)
- Helm charts MUST have documented values with comments
- Architecture diagrams MUST be included

### Three-Spec Development Approach

Phase 5 development MUST follow this spec order:

1. **Spec 1: Advanced Todo Features**
   - Add recurring tasks, due dates, reminders, priorities, tags
   - Implement search, filter, sort functionality
   - Update database schema
   - Update API endpoints
   - Test locally without Kubernetes

2. **Spec 2: Kafka + Dapr Event-Driven Architecture**
   - Design Kafka topics and event schemas
   - Implement Dapr components (Pub/Sub, State, Cron, Secrets)
   - Build recurring task engine service
   - Build reminder service
   - Build audit log service
   - Build real-time sync service
   - Test locally with Docker Compose or Minikube

3. **Spec 3: Local (Minikube) + Cloud (AKS/GKE/OKE) Deployment**
   - Create Helm charts for all services
   - Write Minikube setup script
   - Configure GitHub Actions CI/CD
   - Document cloud deployment (AKS, GKE, OKE)
   - Setup monitoring and logging
   - Test full deployment pipeline

## Deployment Requirements

### Local Development (Minikube)

**MUST be runnable with these exact steps:**
1. Install prerequisites (Docker, Minikube, Helm, kubectl, Dapr CLI)
2. Run Minikube setup script (installs Dapr, Kafka, PostgreSQL)
3. Deploy services via Helm charts
4. Access frontend at documented URL
5. All features working locally

**Setup script MUST:**
- Start Minikube with appropriate resources
- Install Dapr runtime
- Install Kafka/Redpanda via Helm (Strimzi operator or Redpanda chart)
- Install PostgreSQL via Helm (if not using external Neon)
- Configure Dapr components
- Verify all components healthy

### Cloud Deployment

**Azure AKS:**
- Use free $200 credits for new accounts
- Document exact `az` CLI commands
- Helm chart deployment with AKS-specific values
- Configure Azure-specific networking and storage

**Google GKE:**
- Use free $300 credits for new accounts
- Document exact `gcloud` CLI commands
- Helm chart deployment with GKE-specific values
- Configure GCP-specific networking and storage

**Oracle OKE:**
- Use Always Free tier (2 VMs, 1 load balancer)
- Document exact `oci` CLI commands
- Helm chart deployment with OKE-specific values
- Configure OCI-specific networking and storage

**Cloud deployment MUST:**
- Use same Helm charts as Minikube (parameterized)
- Support external Neon PostgreSQL database
- Configure cloud-managed Kafka (or self-hosted)
- Setup ingress/load balancer for frontend
- Configure TLS/SSL certificates
- Setup monitoring and logging

### CI/CD Pipeline (GitHub Actions)

**MUST implement these workflows:**

1. **Build & Test Workflow** (on PR)
   - Checkout code
   - Build Docker images for all services
   - Run unit tests
   - Run integration tests
   - Deploy to Minikube for smoke tests
   - Report test results

2. **Deploy to Staging Workflow** (on merge to main)
   - Build and push Docker images to registry
   - Deploy to staging environment (Minikube or cloud)
   - Run smoke tests
   - Notify on success/failure

3. **Deploy to Production Workflow** (manual trigger)
   - Require approval
   - Deploy to production cloud environment
   - Run health checks
   - Rollback on failure

## Governance

The constitution supersedes all other development practices. Amendments require:
- Documentation of the change and rationale
- Version update following semantic versioning
- Migration plan for existing code if needed

All development MUST verify compliance with this constitution. Use CLAUDE.md for runtime development guidance and tool usage.

**Version**: 3.0.0 | **Ratified**: 2026-01-19 | **Last Amended**: 2026-02-09
