# Oracle Cloud Infrastructure Deployment Guide

## Dual Configuration Approach

This document summarizes the dual configuration setup for the Event-Driven Todo App:

- **Local Development (Minikube)**: Uses Redpanda (Kafka-compatible)
- **Production Deployment (OKE)**: Uses Oracle Streaming Service (Kafka-compatible)

Both configurations use the same application code and Dapr architecture - only the Dapr Pub/Sub component configuration differs.

---

## 1. Message Broker: Dual Configuration

**Local Development (Minikube):** Redpanda
**Production Deployment (OKE):** Oracle Streaming Service (Kafka-compatible)

### Files Created:

#### `dapr-components/pubsub.kafka.minikube.yaml` (New)
- **Broker endpoint**: `localhost:19092` (or Redpanda Cloud endpoint)
- **SASL mechanism**: `SCRAM-SHA-256` (Redpanda standard)
- **Authentication**: Uses Redpanda credentials
- **Secret reference**: `redpanda-creds` secret

#### `dapr-components/pubsub.kafka.oke.yaml` (Renamed from pubsub.kafka.yaml)
- **Broker endpoint**: `cell-1.streaming.ap-mumbai-1.oci.oraclecloud.com:9092`
- **SASL mechanism**: `PLAIN` (Oracle Streaming requirement)
- **Authentication**: Uses OCI auth token
- **Secret reference**: `oci-streaming-creds` secret

#### `backend/.env`
Now includes both configurations:
```bash
# Redpanda (for Minikube local development)
REDPANDA_BOOTSTRAP_SERVERS=localhost:19092
REDPANDA_SASL_USERNAME=your-redpanda-username
REDPANDA_SASL_PASSWORD=your-redpanda-password

# Oracle Streaming Service (for OKE production)
ORACLE_STREAMING_ENDPOINT=cell-1.streaming.ap-mumbai-1.oci.oraclecloud.com:9092
ORACLE_STREAMING_USERNAME=your-tenancy/your-username/ocid1.streampool...
ORACLE_STREAMING_AUTH_TOKEN=your-auth-token
```

---

## 2. Kubernetes: Oracle Kubernetes Engine (OKE)

**Changed From:** Minikube (local), AKS/GKE (cloud)
**Changed To:** Oracle Kubernetes Engine (OKE)

### New Files Created:

#### `docs/ORACLE_CLOUD_SETUP.md`
Complete step-by-step guide with exact OCI CLI commands for:
- Creating VCN and subnets
- Creating Oracle Streaming Service (stream pool + 3 streams)
- Creating OKE cluster with node pool
- Configuring kubectl for OKE
- Installing Dapr on OKE
- Deploying services via Helm
- Configuring ingress with WebSocket support

---

## 3. Ingress: OCI Native Ingress Controller

**Changed From:** Generic Kubernetes ingress
**Changed To:** OCI Native Ingress Controller with Load Balancer

### New Files Created:

#### `helm/backend/templates/ingress.yaml`
- Uses `oci-native-ingress-controller` ingress class
- OCI Load Balancer annotations for health checks
- HTTP backend protocol
- Exposes backend API on port 8000

#### `helm/sync/templates/ingress.yaml`
- Uses `oci-native-ingress-controller` ingress class
- **WebSocket support** with connection upgrade headers
- Extended timeouts for long-lived WebSocket connections (3600s)
- Exposes WebSocket endpoint at `/ws/tasks`

### Files Modified:

#### `helm/backend/values.yaml`
- Added `ingress.enabled: true`
- Added `ingress.className: "oci-native-ingress-controller"`

#### `helm/sync/values.yaml`
- Added `ingress.enabled: true`
- Added `ingress.className: "oci-native-ingress-controller"`

---

## 4. Container Registry: Oracle Container Image Registry (OCIR)

**Changed From:** Docker Hub / Generic registry
**Changed To:** Oracle Container Image Registry (OCIR)

### Setup Commands:
```bash
# Login to OCIR
docker login ${OCI_REGION}.ocir.io -u ${TENANCY_NAME}/${OCI_USERNAME}

# Image naming format
${OCI_REGION}.ocir.io/${TENANCY_NAME}/${APP_NAME}/backend-api:latest
```

---

## 5. Secrets Management

**Changed From:** Generic Kubernetes secrets
**Changed To:** OCI-specific secrets with proper naming

### Kubernetes Secrets Created:

#### `redpanda-creds` (Minikube only)
- `sasl-username`: Redpanda username
- `sasl-password`: Redpanda password
- Used by `pubsub.kafka.minikube.yaml`

#### `oci-streaming-creds` (OKE only)
- `sasl-username`: Format `<tenancy>/<username>/<stream-pool-ocid>`
- `auth-token`: Generated via `oci iam auth-token create`
- Used by `pubsub.kafka.oke.yaml`

#### `app-secrets` (Both environments)
- `database-url`: Neon PostgreSQL connection string
- `better-auth-secret`: JWT secret key
- `sendgrid-api-key`: Email notification service
- `fcm-server-key`: Push notification service

---

## 6. Documentation Updates

### New Documentation:
- **`docs/ORACLE_CLOUD_SETUP.md`**: Complete OCI deployment guide (12 steps)

### Updated Documentation:
- **`README.md`**: Updated to mention Oracle Cloud as deployment option
- **`backend/.env`**: Updated with Oracle Streaming variables

---

## What Stayed the Same (No Changes)

✅ **Database**: Neon PostgreSQL for both Minikube and OKE
✅ **All microservices code**: No code changes required - same application code for both environments
✅ **Event schemas**: CloudEvents 1.0 specification unchanged
✅ **Dapr architecture**: Same Pub/Sub, State Store, Jobs API - only component configuration differs
✅ **Frontend code**: Next.js, WebSocket client unchanged
✅ **CI/CD workflows**: GitHub Actions unchanged (just update kubectl context for OKE)
✅ **Helm chart structure**: Same templates for both environments

---

## Deployment Checklists

### Minikube (Local Development) Checklist

- [ ] Install Minikube, Dapr CLI, Helm, kubectl
- [ ] Set up Redpanda (local or Redpanda Cloud)
- [ ] Update `backend/.env` with Redpanda credentials
- [ ] Run `./scripts/setup-minikube.sh` to set up cluster
- [ ] Verify `pubsub.kafka.minikube.yaml` is applied
- [ ] Verify `redpanda-creds` secret is created
- [ ] Run `./scripts/deploy-local.sh` to deploy services
- [ ] Test event publishing and consumption
- [ ] Test WebSocket connectivity

### OKE (Production Deployment) Checklist

- [ ] Create Oracle Streaming Service (stream pool + 3 streams)
- [ ] Generate OCI auth token
- [ ] Update `backend/.env` with Oracle Streaming credentials
- [ ] Create OKE cluster
- [ ] Configure kubectl for OKE
- [ ] Install Dapr on OKE
- [ ] Create `oci-streaming-creds` Kubernetes secret
- [ ] Apply `pubsub.kafka.oke.yaml` component
- [ ] Build and push images to OCIR
- [ ] Deploy Helm charts with updated image repositories
- [ ] Verify ingress and load balancer created
- [ ] Test WebSocket connectivity
- [ ] Test event publishing and consumption

---
---

## Cost Comparison

### Redpanda Cloud (Previous)
- Free tier: 10 MB/s ingress, 30 MB/s egress
- Paid tier: ~$0.50/GB transferred

### Oracle Streaming Service (Current)
- Free tier: 50 GB storage, 1 million PUT requests/month
- Paid tier: $0.025/GB storage, $0.04 per million PUT requests
- **Generally more cost-effective for high-volume workloads**

---

## Performance Considerations

### Oracle Streaming Service
- **Latency**: Typically 10-50ms (similar to Redpanda)
- **Throughput**: Up to 1 MB/s per partition (3 partitions = 3 MB/s)
- **Retention**: Configurable (24h-168h), we use 168h for task-events

### OKE
- **Node types**: VM.Standard.E4.Flex (2 OCPUs, 16GB RAM per node)
- **Scaling**: Horizontal Pod Autoscaler (HPA) supported
- **Networking**: VCN with private subnets for security

---

## Troubleshooting Oracle-Specific Issues

### Streaming Connection Errors
```bash
# Test connectivity from pod
kubectl run -it --rm debug --image=busybox --restart=Never -- sh
nc -zv cell-1.streaming.ap-mumbai-1.oci.oraclecloud.com 9092
```

### Auth Token Issues
- Auth tokens expire after 90 days by default
- Regenerate: `oci iam auth-token create --user-id <user-ocid>`
- Update Kubernetes secret: `kubectl create secret generic oci-streaming-creds --from-literal=auth-token=<new-token> --dry-run=client -o yaml | kubectl apply -f -`

### Ingress Not Getting External IP
- Check OCI Load Balancer creation: `oci lb load-balancer list --compartment-id <compartment-id>`
- Verify subnet has internet gateway attached
- Check security list allows ingress on ports 80, 443, 8003

---

## Next Steps

1. **Follow `docs/ORACLE_CLOUD_SETUP.md`** for complete deployment
2. **Test locally first** with Dapr sidecar before deploying to OKE
3. **Monitor costs** via OCI Cost Management dashboard
4. **Set up alerts** for streaming throughput and OKE resource usage
5. **Configure auto-scaling** for production workloads

---

## Support Resources

- **Oracle Streaming Service**: https://docs.oracle.com/en-us/iaas/Content/Streaming/home.htm
- **OKE Documentation**: https://docs.oracle.com/en-us/iaas/Content/ContEng/home.htm
- **Dapr on Kubernetes**: https://docs.dapr.io/operations/hosting/kubernetes/
- **OCI CLI Reference**: https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/
