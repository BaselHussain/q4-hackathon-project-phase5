# Deployment Guide: Minikube vs OKE

## Overview

This application supports **dual deployment configurations** to meet Phase 5 requirements:

1. **Local Development (Minikube)**: Uses Redpanda for Kafka-compatible messaging
2. **Production Deployment (OKE)**: Uses Oracle Streaming Service for Kafka-compatible messaging

Both configurations use the **same application code** and **same Dapr architecture** - only the Dapr Pub/Sub component configuration differs.

---

## Configuration Comparison

| Aspect | Minikube (Local Dev) | OKE (Production) |
|--------|---------------------|------------------|
| **Kubernetes** | Minikube | Oracle Kubernetes Engine (OKE) |
| **Message Broker** | Redpanda | Oracle Streaming Service |
| **Dapr Component** | `pubsub.kafka.minikube.yaml` | `pubsub.kafka.oke.yaml` |
| **SASL Mechanism** | SCRAM-SHA-256 | PLAIN |
| **Kubernetes Secret** | `redpanda-creds` | `oci-streaming-creds` |
| **Container Registry** | Local Docker | Oracle Container Image Registry (OCIR) |
| **Ingress** | Port-forward | OCI Native Ingress Controller |
| **Setup Script** | `./scripts/setup-minikube.sh` | Follow `docs/ORACLE_CLOUD_SETUP.md` |

---

## When to Use Each Configuration

### Use Minikube When:
- Developing locally on your laptop
- Testing changes before pushing to production
- Running integration tests in CI/CD
- Learning the application architecture
- No cloud resources required

### Use OKE When:
- Deploying to production
- Need high availability and scalability
- Require enterprise-grade message broker (Oracle Streaming)
- Want OCI-native integrations (Load Balancer, Monitoring)
- Deploying for end users

---

## Quick Start: Minikube (Local Development)

### Prerequisites
- Minikube 1.32+
- Dapr CLI 1.12+
- Docker Desktop
- kubectl 1.28+
- Helm 3.x

### Setup Steps

1. **Configure Redpanda credentials in `.env`:**
   ```bash
   REDPANDA_BOOTSTRAP_SERVERS=localhost:19092
   REDPANDA_SASL_USERNAME=your-username
   REDPANDA_SASL_PASSWORD=your-password
   ```

2. **Run setup script:**
   ```bash
   ./scripts/setup-minikube.sh
   ```
   This will:
   - Start Minikube cluster
   - Install Dapr 1.12.0
   - Apply `pubsub.kafka.minikube.yaml` (Redpanda)
   - Create `redpanda-creds` secret
   - Apply State Store and Secret Store components

3. **Deploy services:**
   ```bash
   ./scripts/deploy-local.sh
   ```

4. **Access services:**
   ```bash
   kubectl port-forward svc/backend 8000:8000
   kubectl port-forward svc/sync-service 8003:8003
   ```

---

## Quick Start: OKE (Production Deployment)

### Prerequisites
- OCI CLI configured
- kubectl 1.28+
- Helm 3.x
- Docker (for building images)

### Setup Steps

Follow the comprehensive guide: **[docs/ORACLE_CLOUD_SETUP.md](ORACLE_CLOUD_SETUP.md)**

Key steps:
1. Create Oracle Streaming Service (3 streams)
2. Create OKE cluster
3. Configure Oracle Streaming credentials in `.env`
4. Create `oci-streaming-creds` Kubernetes secret
5. Apply `pubsub.kafka.oke.yaml` component
6. Build and push images to OCIR
7. Deploy via Helm charts
8. Configure OCI Native Ingress with WebSocket support

---

## Environment Variables

Your `backend/.env` should include **both** configurations:

```bash
# Database (shared by both environments)
DATABASE_URL=postgresql+asyncpg://...

# Redpanda (for Minikube)
REDPANDA_BOOTSTRAP_SERVERS=localhost:19092
REDPANDA_SASL_USERNAME=your-redpanda-username
REDPANDA_SASL_PASSWORD=your-redpanda-password

# Oracle Streaming Service (for OKE)
ORACLE_STREAMING_ENDPOINT=cell-1.streaming.ap-mumbai-1.oci.oraclecloud.com:9092
ORACLE_STREAMING_USERNAME=your-tenancy/your-username/ocid1.streampool...
ORACLE_STREAMING_AUTH_TOKEN=your-auth-token

# Notification services (shared)
SENDGRID_API_KEY=your-sendgrid-key
FCM_SERVER_KEY=your-fcm-key

# Authentication (shared)
BETTER_AUTH_SECRET=your-secret-key

# Dapr (shared)
DAPR_HTTP_PORT=3500
```

---

## Switching Between Environments

### From Minikube to OKE:
1. Build and push images to OCIR
2. Update Helm values with OCIR image paths
3. Apply `pubsub.kafka.oke.yaml` instead of `pubsub.kafka.minikube.yaml`
4. Create `oci-streaming-creds` secret
5. Deploy via Helm

### From OKE to Minikube:
1. Switch kubectl context to Minikube
2. Apply `pubsub.kafka.minikube.yaml`
3. Create `redpanda-creds` secret
4. Deploy via `./scripts/deploy-local.sh`

---

## Troubleshooting

### Minikube Issues

**Events not publishing:**
```bash
# Check Dapr sidecar logs
kubectl logs -l app.kubernetes.io/name=backend -c daprd | grep pubsub

# Verify Redpanda connection
kubectl get components
kubectl describe component pubsub
```

**Secret not found:**
```bash
# Verify redpanda-creds secret exists
kubectl get secret redpanda-creds

# Recreate if needed
kubectl create secret generic redpanda-creds \
  --from-literal=sasl-username="$REDPANDA_SASL_USERNAME" \
  --from-literal=sasl-password="$REDPANDA_SASL_PASSWORD"
```

### OKE Issues

**Oracle Streaming connection errors:**
```bash
# Test connectivity from pod
kubectl run -it --rm debug --image=busybox --restart=Never -- sh
nc -zv cell-1.streaming.ap-mumbai-1.oci.oraclecloud.com 9092
```

**Auth token expired:**
```bash
# Regenerate auth token
oci iam auth-token create --user-id <user-ocid>

# Update secret
kubectl create secret generic oci-streaming-creds \
  --from-literal=auth-token=<new-token> \
  --dry-run=client -o yaml | kubectl apply -f -
```

---

## Phase 5 Compliance

✅ **Kafka-compatible message broker**: Redpanda (Minikube) and Oracle Streaming (OKE)
✅ **Kubernetes deployment**: Minikube (local) and OKE (production)
✅ **Dapr service mesh**: Pub/Sub, State Store, Jobs API
✅ **Event-driven architecture**: 4 microservices (recurring-task, notification, sync, audit)
✅ **Helm charts**: All services packaged with Helm 3
✅ **CI/CD**: GitHub Actions pipelines
✅ **Local development**: Minikube setup script
✅ **Cloud deployment**: OKE with Oracle Streaming Service

---

## Next Steps

1. **For Local Development**: Run `./scripts/setup-minikube.sh` and start coding
2. **For Production Deployment**: Follow `docs/ORACLE_CLOUD_SETUP.md` step-by-step
3. **For CI/CD**: Configure GitHub Actions with OKE credentials

---

## Support Resources

- **Minikube**: https://minikube.sigs.k8s.io/docs/
- **Redpanda**: https://docs.redpanda.com/
- **Oracle Streaming**: https://docs.oracle.com/en-us/iaas/Content/Streaming/home.htm
- **OKE**: https://docs.oracle.com/en-us/iaas/Content/ContEng/home.htm
- **Dapr**: https://docs.dapr.io/
