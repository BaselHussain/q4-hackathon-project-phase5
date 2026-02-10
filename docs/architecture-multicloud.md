# Architecture: Multi-Cloud Deployment

## Overview

The application uses Dapr as an abstraction layer to enable deployment across multiple
Kubernetes providers without application code changes. Only infrastructure configuration
(Dapr components and Helm values) differs between clouds.

## Multi-Cloud Architecture

```
                    +----------------------------------+
                    |        Application Layer          |
                    |                                  |
                    |  Backend API    Recurring Task   |
                    |  Notification   Sync Service     |
                    |  Audit Service                   |
                    |                                  |
                    |  (Identical code on all clouds)  |
                    +----------------+-----------------+
                                     |
                    +----------------+-----------------+
                    |         Dapr Sidecar Layer        |
                    |                                  |
                    |  Pub/Sub    State Store  Secrets  |
                    |  (Kafka)   (PostgreSQL) (K8s)    |
                    |                                  |
                    |  (Identical behavior, different  |
                    |   backend implementations)       |
                    +----------------+-----------------+
                                     |
              +----------------------+----------------------+
              |                      |                      |
    +---------+----------+ +---------+----------+ +---------+----------+
    |    Oracle OKE      | |    Azure AKS       | |    Google GKE      |
    |                    | |                    | |                    |
    | Messaging:         | | Messaging:         | | Messaging:         |
    |  Oracle Streaming  | |  Azure Event Hubs  | |  Redpanda          |
    |  (Kafka protocol)  | |  (Kafka protocol)  | |  (self-hosted)     |
    |                    | |                    | |                    |
    | Storage:           | | Storage:           | | Storage:           |
    |  OCI Block Volume  | |  Azure Managed     | |  Persistent Disk   |
    |  (oci-bv)          | |  Disk (azure-disk)  | |  (standard-rwo)    |
    |                    | |                    | |                    |
    | Logs:              | | Logs:              | | Logs:              |
    |  OCI Object Store  | |  Azure Blob Store  | |  Google Cloud      |
    |                    | |                    | |  Storage           |
    |                    | |                    | |                    |
    | Ingress:           | | Ingress:           | | Ingress:           |
    |  OCI Native LB     | |  Azure Load        | |  GCP Load          |
    |                    | |  Balancer          | |  Balancer          |
    +--------------------+ +--------------------+ +--------------------+
```

## Dapr Component Abstraction

```
dapr-components/
├── pubsub.kafka.minikube.yaml   # Local Redpanda (dev)
├── pubsub.kafka.oke.yaml        # Oracle Streaming Service
├── pubsub.kafka.aks.yaml        # Azure Event Hubs
├── pubsub.kafka.gke.yaml        # Self-hosted Redpanda on GKE
├── statestore.postgresql.yaml   # Neon PostgreSQL (cloud-agnostic)
└── secretstores.kubernetes.yaml # Kubernetes Secrets (cloud-agnostic)
```

### Switching Clouds

To deploy to a different cloud, only three things change:

```
1. Dapr Pub/Sub Component    -> pubsub.kafka.<cloud>.yaml
2. Helm Values Override      -> values-<cloud>.yaml
3. Kubernetes Secrets        -> Cloud-specific credentials
```

Application code remains **100% identical** across all environments.

## Helm Values Strategy

```
helm/<service>/
├── values.yaml              # Defaults (Minikube)
├── values-oke.yaml          # Oracle OKE overrides
├── values-aks.yaml          # Azure AKS overrides
└── values-gke.yaml          # Google GKE overrides

Overrides include:
- Storage class names
- Ingress controller type
- Resource limits (production)
- Replica counts
- TLS configuration
- Cloud-specific annotations
```

## Deployment Flow

```
                              Developer
                                 |
                    +------------+------------+
                    |                         |
              Local Dev                  Production
                    |                         |
              Minikube                   Choose Cloud
              + Redpanda                      |
              + Dapr                    +-----+-----+
                                        |     |     |
                                       OKE  AKS   GKE
                                        |     |     |
                                        v     v     v

Step 1: Configure Secrets
        kubectl create secret generic <cloud>-creds ...

Step 2: Apply Dapr Components
        kubectl apply -f dapr-components/pubsub.kafka.<cloud>.yaml
        kubectl apply -f dapr-components/statestore.postgresql.yaml

Step 3: Deploy Services
        helm upgrade --install <service> helm/<service>/ \
          -f helm/<service>/values-<cloud>.yaml

Step 4: Deploy Monitoring
        ./scripts/deploy-monitoring.sh --environment <cloud>

Step 5: Deploy Logging
        ./scripts/deploy-logging.sh --environment <cloud>

Step 6: Verify
        ./scripts/test-e2e-<cloud>.sh
```

## CI/CD Multi-Cloud Pipeline

```
Code Push
    |
    v
+---+---+
| Build |  (build-test.yml)
| & Test|  - Lint, unit tests, contract tests
+---+---+  - Build Docker images
    |
    v
+---+--------+
| Deploy     |  (deploy-staging.yml)
| Staging    |  - Deploy to staging namespace
|            |  - Run E2E tests
+---+--------+
    |
    v
+---+--------+
| E2E Tests  |  (e2e-tests.yml)
|            |  - Minikube-based integration tests
|            |  - Full workflow validation
+---+--------+
    |
    v (manual approval)
+---+--------+
| Deploy     |  (deploy-production.yml)
| Production |  - Deploy to chosen cloud
|            |  - Environment-specific values
+------------+
```

## Service Topology (All Clouds)

```
                         Internet
                            |
                      +-----+-----+
                      |  Ingress  |
                      | Controller|
                      +-----+-----+
                            |
              +-------------+-------------+
              |                           |
        +-----+-----+              +-----+-----+
        | Backend   |              |   Sync    |
        | API       |              |  Service  |
        | (2 pods)  |              | (2 pods)  |
        +-----+-----+              +-----+-----+
              |                           |
              | Dapr Pub/Sub              | WebSocket
              |                           |
    +---------+---------+---------+       |
    |         |         |         |       |
+---+---+ +--+----+ +--+----+ +--+----+  |
|Recur- | |Notif- | |Audit  | |Kafka/ |  |
|ring   | |ication| |Service| |Event  |<-+
|Task   | |Service| |(1 pod)| |Broker |
|(1 pod)| |(1 pod)|  +-------+ +-------+
+-------+ +-------+
              |
        +-----+-----+
        | PostgreSQL |
        | (Neon)     |
        +------------+
```
