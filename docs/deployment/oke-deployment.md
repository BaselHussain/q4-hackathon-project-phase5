# Oracle Kubernetes Engine (OKE) Deployment Guide

This guide walks you through deploying the Todo App to Oracle Kubernetes Engine (OKE) with full monitoring and logging capabilities.

## Prerequisites

- Oracle Cloud Infrastructure (OCI) account
- OCI CLI installed and configured
- kubectl installed
- Helm 3 installed
- Docker installed (for building images)
- Oracle Container Registry (OCIR) access

## Step 1: Create OKE Cluster

### Using OCI Console

1. Navigate to **Developer Services** > **Kubernetes Clusters (OKE)**
2. Click **Create Cluster**
3. Choose **Quick Create** for a standard configuration
4. Configure cluster:
   - **Name**: `todoapp-cluster`
   - **Kubernetes Version**: 1.28 or later
   - **Node Pool Shape**: VM.Standard.E4.Flex (2 OCPUs, 16GB RAM)
   - **Number of Nodes**: 3
   - **Kubernetes API Endpoint**: Public
5. Click **Create Cluster** and wait for provisioning (10-15 minutes)

### Using OCI CLI

```bash
# Create VCN and subnets (if not exists)
oci ce cluster create \
  --compartment-id <compartment-ocid> \
  --name todoapp-cluster \
  --kubernetes-version v1.28.2 \
  --vcn-id <vcn-ocid> \
  --service-lb-subnet-ids '["<lb-subnet-ocid>"]'

# Create node pool
oci ce node-pool create \
  --cluster-id <cluster-ocid> \
  --compartment-id <compartment-ocid> \
  --name todoapp-nodes \
  --node-shape VM.Standard.E4.Flex \
  --node-shape-config '{"ocpus":2,"memoryInGBs":16}' \
  --size 3 \
  --kubernetes-version v1.28.2
```

## Step 2: Configure kubectl

```bash
# Get kubeconfig
oci ce cluster create-kubeconfig \
  --cluster-id <cluster-ocid> \
  --file $HOME/.kube/config \
  --region us-ashburn-1 \
  --token-version 2.0.0

# Verify connection
kubectl cluster-info
kubectl get nodes
```

## Step 3: Set Up Oracle Container Registry (OCIR)

```bash
# Login to OCIR
docker login <region-key>.ocir.io \
  -u '<tenancy-namespace>/<username>' \
  -p '<auth-token>'

# Example for Ashburn region
docker login iad.ocir.io \
  -u 'mytenancy/oracleidentitycloudservice/user@example.com' \
  -p '<auth-token>'
```

## Step 4: Build and Push Docker Images

```bash
# Set environment variables
export REGION_KEY=iad  # or your region
export TENANCY_NAMESPACE=<your-tenancy-namespace>
export OCIR_REPO=${REGION_KEY}.ocir.io/${TENANCY_NAMESPACE}/todoapp

# Build and push backend
docker build -t ${OCIR_REPO}/backend:latest ./backend
docker push ${OCIR_REPO}/backend:latest

# Build and push microservices
docker build -t ${OCIR_REPO}/recurring-task:latest ./backend/services/recurring-task
docker push ${OCIR_REPO}/recurring-task:latest

docker build -t ${OCIR_REPO}/notification:latest ./backend/services/notification
docker push ${OCIR_REPO}/notification:latest

docker build -t ${OCIR_REPO}/sync:latest ./backend/services/sync
docker push ${OCIR_REPO}/sync:latest

docker build -t ${OCIR_REPO}/audit:latest ./backend/services/audit
docker push ${OCIR_REPO}/audit:latest
```

## Step 5: Create Kubernetes Secrets

```bash
# Create namespace
kubectl create namespace default

# Create image pull secret for OCIR
kubectl create secret docker-registry ocir-secret \
  --docker-server=${REGION_KEY}.ocir.io \
  --docker-username='<tenancy-namespace>/<username>' \
  --docker-password='<auth-token>' \
  --docker-email='<email>'

# Create application secrets
kubectl create secret generic app-secrets \
  --from-literal=database-url="<neon-postgres-url>" \
  --from-literal=better-auth-secret="<auth-secret>" \
  --from-literal=sendgrid-api-key="<sendgrid-key>" \
  --from-literal=fcm-server-key="<fcm-key>"

# Create Kafka credentials (if using OCI Streaming)
kubectl create secret generic kafka-creds \
  --from-literal=sasl-username="<oci-streaming-username>" \
  --from-literal=sasl-password="<oci-streaming-password>"
```

## Step 6: Install Dapr

```bash
# Install Dapr CLI (if not installed)
wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash

# Initialize Dapr on Kubernetes
dapr init -k --runtime-version 1.12.0 --wait

# Verify Dapr installation
kubectl get pods -n dapr-system
```

## Step 7: Deploy Dapr Components

```bash
# Apply OKE-specific Dapr components
kubectl apply -f dapr-components/pubsub.kafka.oke.yaml
kubectl apply -f dapr-components/statestore.postgresql.yaml
kubectl apply -f dapr-components/secretstores.kubernetes.yaml
```

## Step 8: Deploy Monitoring Stack

```bash
# Deploy Prometheus + Grafana
./scripts/deploy-monitoring.sh --environment oke

# Wait for deployment
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n monitoring --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana -n monitoring --timeout=300s

# Get Grafana admin password
kubectl get secret -n monitoring kube-prometheus-stack-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode
```

## Step 9: Deploy Logging Stack

```bash
# Create OCI Object Storage bucket for Loki
oci os bucket create \
  --compartment-id <compartment-ocid> \
  --name loki-chunks

# Deploy Loki + Promtail
./scripts/deploy-logging.sh --environment oke

# Wait for deployment
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=loki -n logging --timeout=300s
```

## Step 10: Deploy Application Services

```bash
# Update Helm values with OCIR image paths
# Edit helm/*/values-oke.yaml files to set:
# image.repository: iad.ocir.io/<tenancy-namespace>/todoapp/<service>

# Deploy backend
helm upgrade --install backend ./helm/backend \
  --values ./helm/backend/values-oke.yaml \
  --set image.repository=${OCIR_REPO}/backend \
  --set image.tag=latest

# Deploy microservices
helm upgrade --install recurring-task ./helm/recurring-task \
  --values ./helm/recurring-task/values-oke.yaml \
  --set image.repository=${OCIR_REPO}/recurring-task

helm upgrade --install notification ./helm/notification \
  --values ./helm/notification/values-oke.yaml \
  --set image.repository=${OCIR_REPO}/notification

helm upgrade --install sync ./helm/sync \
  --values ./helm/sync/values-oke.yaml \
  --set image.repository=${OCIR_REPO}/sync

helm upgrade --install audit ./helm/audit \
  --values ./helm/audit/values-oke.yaml \
  --set image.repository=${OCIR_REPO}/audit
```

## Step 11: Configure Ingress (Optional)

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Wait for Load Balancer IP
kubectl get svc -n ingress-nginx ingress-nginx-controller

# Configure DNS
# Point todoapp.example.com to the Load Balancer IP

# Apply ingress resources
kubectl apply -f k8s/ingress-oke.yaml
```

## Step 12: Verify Deployment

```bash
# Check all pods are running
kubectl get pods --all-namespaces

# Check services
kubectl get svc

# Test backend API
kubectl port-forward svc/backend 8000:8000
curl http://localhost:8000/health

# Access Grafana
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
# Open http://localhost:3000

# Access Loki
kubectl port-forward -n logging svc/loki-gateway 3100:80
# Query logs: http://localhost:3100/loki/api/v1/query
```

## Monitoring and Observability

### Grafana Dashboards

1. **Service Overview**: Real-time metrics for all services
2. **Event Processing**: Kafka and Dapr pub/sub metrics
3. **WebSocket Metrics**: Active connections and message delivery
4. **Application Logs**: Centralized log aggregation with Loki

### Accessing Dashboards

```bash
# Port-forward Grafana
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80

# Login credentials
# Username: admin
# Password: (retrieved in Step 8)
```

### Querying Logs

```bash
# Port-forward Loki
kubectl port-forward -n logging svc/loki-gateway 3100:80

# Example LogQL queries
# All logs from backend: {namespace="default", service="backend"}
# Error logs: {level="ERROR"}
# Logs with trace IDs: {namespace="default"} |= "trace_id"
```

## Scaling

### Horizontal Pod Autoscaling

```bash
# Enable metrics-server (if not installed)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Create HPA for backend
kubectl autoscale deployment backend --cpu-percent=70 --min=2 --max=10

# Check HPA status
kubectl get hpa
```

### Node Pool Scaling

```bash
# Scale node pool via OCI CLI
oci ce node-pool update \
  --node-pool-id <node-pool-ocid> \
  --size 5
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>

# Check Dapr sidecar logs
kubectl logs <pod-name> -c daprd
```

### Image Pull Errors

```bash
# Verify OCIR secret
kubectl get secret ocir-secret -o yaml

# Test image pull manually
docker pull ${OCIR_REPO}/backend:latest
```

### Networking Issues

```bash
# Check service endpoints
kubectl get endpoints

# Test service connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- sh
# Inside pod: wget -O- http://backend:8000/health
```

## Cost Optimization

1. **Use Preemptible Nodes**: For non-production workloads
2. **Right-size Node Shapes**: Start with smaller shapes and scale up
3. **Enable Cluster Autoscaler**: Automatically scale nodes based on demand
4. **Use OCI Free Tier**: 2 VMs with 1 OCPU each (always free)
5. **Monitor Resource Usage**: Use Grafana to identify over-provisioned resources

## Security Best Practices

1. **Enable Network Policies**: Restrict pod-to-pod communication
2. **Use OCI Vault**: Store secrets in OCI Vault instead of Kubernetes secrets
3. **Enable Pod Security Policies**: Enforce security standards
4. **Regular Updates**: Keep Kubernetes and Dapr versions up to date
5. **Audit Logging**: Enable OKE audit logging for compliance

## Cleanup

```bash
# Delete Helm releases
helm uninstall backend recurring-task notification sync audit
helm uninstall kube-prometheus-stack -n monitoring
helm uninstall loki -n logging

# Delete Dapr
dapr uninstall -k

# Delete OKE cluster (via OCI Console or CLI)
oci ce cluster delete --cluster-id <cluster-ocid>
```

## Additional Resources

- [OKE Documentation](https://docs.oracle.com/en-us/iaas/Content/ContEng/home.htm)
- [OCIR Documentation](https://docs.oracle.com/en-us/iaas/Content/Registry/home.htm)
- [Dapr on Kubernetes](https://docs.dapr.io/operations/hosting/kubernetes/)
- [Prometheus Operator](https://prometheus-operator.dev/)
- [Grafana Loki](https://grafana.com/docs/loki/latest/)
