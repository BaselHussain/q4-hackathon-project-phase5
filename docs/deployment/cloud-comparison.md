# Multi-Cloud Deployment Comparison

This document compares the deployment configurations across Oracle OKE, Azure AKS, and Google GKE.

## Infrastructure Comparison

| Feature | Oracle OKE | Azure AKS | Google GKE |
|---------|-----------|-----------|-----------|
| **CLI Tool** | `oci` | `az` | `gcloud` |
| **Cluster Create** | `oci ce cluster create` | `az aks create` | `gcloud container clusters create` |
| **Kubeconfig** | `oci ce cluster create-kubeconfig` | `az aks get-credentials` | `gcloud container clusters get-credentials` |
| **Container Registry** | OCI Container Registry (OCIR) | Azure Container Registry (ACR) | Google Container Registry (GCR) / Artifact Registry |
| **Min Nodes** | 2 (recommended) | 2 (recommended) | 2 (recommended) |
| **Node Shape/Size** | VM.Standard.E4.Flex | Standard_D2s_v3 | e2-standard-2 |

## Storage Classes

| Feature | Oracle OKE | Azure AKS | Google GKE |
|---------|-----------|-----------|-----------|
| **Block Storage** | `oci-bv` (Block Volume) | `azure-disk` (Managed Disk) | `standard-rwo` (Persistent Disk) |
| **File Storage** | `oci-fss` (File Storage) | `azure-file` (Azure Files) | `standard` (Filestore) |
| **Default Class** | `oci-bv` | `managed-premium` | `standard-rwo` |

## Networking

| Feature | Oracle OKE | Azure AKS | Google GKE |
|---------|-----------|-----------|-----------|
| **Load Balancer** | OCI Load Balancer | Azure Load Balancer | GCP Load Balancer |
| **Ingress Controller** | OCI Native Ingress | NGINX / App Gateway | GKE Ingress / NGINX |
| **TLS/Certificates** | OCI Certificates | Azure Key Vault / cert-manager | Google-managed / cert-manager |
| **DNS** | OCI DNS | Azure DNS | Cloud DNS |

## Kafka-Compatible Messaging

| Feature | Oracle OKE | Azure AKS | Google GKE |
|---------|-----------|-----------|-----------|
| **Service** | Oracle Streaming Service | Azure Event Hubs | Self-hosted Redpanda |
| **Protocol** | Kafka-compatible | Kafka-compatible | Native Kafka |
| **SASL Mechanism** | PLAIN | PLAIN ($ConnectionString) | SCRAM-SHA-256 |
| **TLS** | Required | Required | Required |
| **Dapr Component** | `pubsub.kafka.oke.yaml` | `pubsub.kafka.aks.yaml` | `pubsub.kafka.gke.yaml` |
| **K8s Secret** | `oci-streaming-creds` | `azure-eventhubs-creds` | `redpanda-creds` |
| **Managed** | Yes (fully managed) | Yes (fully managed) | No (self-hosted) |

## Monitoring & Logging Storage

| Feature | Oracle OKE | Azure AKS | Google GKE |
|---------|-----------|-----------|-----------|
| **Prometheus Storage** | `oci-bv` (40Gi) | `azure-disk` (40Gi) | `standard-rwo` (40Gi) |
| **Grafana Storage** | `oci-bv` (10Gi) | `azure-disk` (10Gi) | `standard-rwo` (10Gi) |
| **Loki Backend** | OCI Object Storage | Azure Blob Storage | Google Cloud Storage |
| **Log Retention** | 30 days | 30 days | 30 days |
| **Metrics Retention** | 30 days | 30 days | 30 days |

## Secrets Management

| Feature | Oracle OKE | Azure AKS | Google GKE |
|---------|-----------|-----------|-----------|
| **Native Solution** | OCI Vault | Azure Key Vault | GCP Secret Manager |
| **K8s Integration** | Kubernetes Secrets | Azure Key Vault CSI | GCP Secret Manager CSI |
| **Dapr Component** | `secretstores.kubernetes` | `secretstores.kubernetes` | `secretstores.kubernetes` |

## Cost Considerations

| Resource | Oracle OKE | Azure AKS | Google GKE |
|----------|-----------|-----------|-----------|
| **Control Plane** | Free | Free | Free (Standard) / $73/mo (Autopilot) |
| **Node Pool (2x)** | ~$140/mo (E4.Flex) | ~$140/mo (D2s_v3) | ~$130/mo (e2-standard-2) |
| **Messaging** | ~$50/mo (Streaming) | ~$40/mo (Event Hubs Basic) | ~$0 (self-hosted Redpanda) |
| **Load Balancer** | ~$12/mo | ~$18/mo | ~$18/mo |
| **Estimated Total** | ~$200/mo | ~$200/mo | ~$150/mo |

*Prices are approximate and vary by region.*

## Deployment Commands Quick Reference

### Oracle OKE
```bash
./scripts/deploy-monitoring.sh --environment oke
./scripts/deploy-logging.sh --environment oke
helm upgrade --install backend helm/backend/ -f helm/backend/values-oke.yaml
```

### Azure AKS
```bash
./scripts/deploy-monitoring.sh --environment aks
./scripts/deploy-logging.sh --environment aks
helm upgrade --install backend helm/backend/ -f helm/backend/values-aks.yaml
```

### Google GKE
```bash
./scripts/deploy-monitoring.sh --environment gke
./scripts/deploy-logging.sh --environment gke
helm upgrade --install backend helm/backend/ -f helm/backend/values-gke.yaml
```

## Architecture Abstraction

All three clouds use the same application code and Helm charts. The Dapr abstraction layer
handles the differences:

```
Application Code (identical)
        |
    Dapr Sidecar (identical)
        |
    Dapr Component (cloud-specific)
        |
  +-----------+-----------+-----------+
  |           |           |           |
  OKE        AKS         GKE         Minikube
  (Oracle     (Azure      (Redpanda   (Redpanda
  Streaming)  Event Hubs) on GKE)     local)
```

This means switching clouds requires only:
1. Updating the Dapr component YAML
2. Using the cloud-specific Helm values file
3. Configuring the cloud-specific Kubernetes secrets
