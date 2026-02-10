# Google Kubernetes Engine (GKE) Deployment Guide

This guide walks you through deploying the Todo App to Google Kubernetes Engine (GKE) with full monitoring and logging capabilities.

## Prerequisites

- Google Cloud Platform (GCP) account with billing enabled
- gcloud CLI installed and configured
- kubectl installed
- Helm 3 installed
- Docker installed (for building images)
- Google Container Registry (GCR) or Artifact Registry access

## Step 1: Set Up GCP Project

```bash
# Set environment variables
export PROJECT_ID=todoapp-project
export REGION=us-central1
export ZONE=us-central1-a
export CLUSTER_NAME=todoapp-cluster

# Create new project (or use existing)
gcloud projects create $PROJECT_ID --name="Todo App"

# Set current project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable storage-api.googleapis.com
```

## Step 2: Create GKE Cluster

```bash
# Create GKE cluster with autoscaling
gcloud container clusters create $CLUSTER_NAME \
  --zone $ZONE \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --enable-autoscaling \
  --min-nodes 3 \
  --max-nodes 10 \
  --enable-autorepair \
  --enable-autoupgrade \
  --enable-stackdriver-kubernetes

# Get credentials
gcloud container clusters get-credentials $CLUSTER_NAME --zone $ZONE

# Verify connection
kubectl cluster-info
kubectl get nodes
```

## Step 3: Set Up Google Container Registry (GCR)

```bash
# Configure Docker to use gcloud as credential helper
gcloud auth configure-docker

# Set GCR hostname
export GCR_HOSTNAME=gcr.io
export GCR_PROJECT=${GCR_HOSTNAME}/${PROJECT_ID}
```

## Step 4: Build and Push Docker Images

```bash
# Build and push backend
docker build -t ${GCR_PROJECT}/backend:latest ./backend
docker push ${GCR_PROJECT}/backend:latest

# Build and push microservices
docker build -t ${GCR_PROJECT}/recurring-task:latest ./backend/services/recurring-task
docker push ${GCR_PROJECT}/recurring-task:latest

docker build -t ${GCR_PROJECT}/notification:latest ./backend/services/notification
docker push ${GCR_PROJECT}/notification:latest

docker build -t ${GCR_PROJECT}/sync:latest ./backend/services/sync
docker push ${GCR_PROJECT}/sync:latest

docker build -t ${GCR_PROJECT}/audit:latest ./backend/services/audit
docker push ${GCR_PROJECT}/audit:latest
```

## Step 5: Create Google Cloud Storage Bucket for Loki

```bash
# Create GCS bucket for Loki chunks
export BUCKET_NAME=${PROJECT_ID}-loki-chunks

gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://${BUCKET_NAME}/

# Create service account for Loki
gcloud iam service-accounts create loki-storage \
  --display-name "Loki Storage Service Account"

# Grant storage permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member "serviceAccount:loki-storage@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role "roles/storage.objectAdmin"

# Create and download key
gcloud iam service-accounts keys create loki-sa-key.json \
  --iam-account loki-storage@${PROJECT_ID}.iam.gserviceaccount.com
```

## Step 6: Create Kubernetes Secrets

```bash
# Create namespace
kubectl create namespace default

# Create application secrets
kubectl create secret generic app-secrets \
  --from-literal=database-url="<neon-postgres-url>" \
  --from-literal=better-auth-secret="<auth-secret>" \
  --from-literal=sendgrid-api-key="<sendgrid-key>" \
  --from-literal=fcm-server-key="<fcm-key>"

# Create GCS credentials for Loki
kubectl create secret generic gcs-credentials \
  --from-file=key.json=loki-sa-key.json \
  -n logging

# Create Kafka credentials (if using Confluent Cloud or self-hosted)
kubectl create secret generic kafka-creds \
  --from-literal=sasl-username="<kafka-username>" \
  --from-literal=sasl-password="<kafka-password>"
```

## Step 7: Install Dapr

```bash
# Install Dapr CLI (if not installed)
wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash

# Initialize Dapr on Kubernetes
dapr init -k --runtime-version 1.12.0 --wait

# Verify Dapr installation
kubectl get pods -n dapr-system
```

## Step 8: Deploy Dapr Components

```bash
# Apply GKE-specific Dapr components
kubectl apply -f dapr-components/pubsub.kafka.gke.yaml
kubectl apply -f dapr-components/statestore.postgresql.yaml
kubectl apply -f dapr-components/secretstores.kubernetes.yaml
```

## Step 9: Deploy Monitoring Stack

```bash
# Deploy Prometheus + Grafana
./scripts/deploy-monitoring.sh --environment gke

# Wait for deployment
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n monitoring --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana -n monitoring --timeout=300s

# Get Grafana admin password
kubectl get secret -n monitoring kube-prometheus-stack-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode
```

## Step 10: Deploy Logging Stack

```bash
# Deploy Loki + Promtail with GCS backend
./scripts/deploy-logging.sh --environment gke

# Wait for deployment
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=loki -n logging --timeout=300s
```

## Step 11: Deploy Application Services

```bash
# Deploy backend
helm upgrade --install backend ./helm/backend \
  --values ./helm/backend/values-gke.yaml \
  --set image.repository=${GCR_PROJECT}/backend \
  --set image.tag=latest

# Deploy microservices
helm upgrade --install recurring-task ./helm/recurring-task \
  --values ./helm/recurring-task/values-gke.yaml \
  --set image.repository=${GCR_PROJECT}/recurring-task

helm upgrade --install notification ./helm/notification \
  --values ./helm/notification/values-gke.yaml \
  --set image.repository=${GCR_PROJECT}/notification

helm upgrade --install sync ./helm/sync \
  --values ./helm/sync/values-gke.yaml \
  --set image.repository=${GCR_PROJECT}/sync

helm upgrade --install audit ./helm/audit \
  --values ./helm/audit/values-gke.yaml \
  --set image.repository=${GCR_PROJECT}/audit
```

## Step 12: Configure Ingress

```bash
# GKE automatically provisions a Google Cloud Load Balancer
# when you create an Ingress resource

# Apply ingress resources
kubectl apply -f k8s/ingress-gke.yaml

# Wait for Load Balancer IP
kubectl get ingress

# Get external IP
export EXTERNAL_IP=$(kubectl get ingress todoapp-ingress \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "External IP: $EXTERNAL_IP"

# Configure DNS
# Create A record: todoapp.example.com -> $EXTERNAL_IP
```

## Step 13: Configure TLS with Google-Managed Certificates

```bash
# Create ManagedCertificate resource
cat <<EOF | kubectl apply -f -
apiVersion: networking.gke.io/v1
kind: ManagedCertificate
metadata:
  name: todoapp-cert
spec:
  domains:
    - todoapp.example.com
    - api.todoapp.example.com
EOF

# Update ingress to use managed certificate
# Add annotation: networking.gke.io/managed-certificates: todoapp-cert

# Check certificate status (takes 10-15 minutes)
kubectl describe managedcertificate todoapp-cert
```

## Step 14: Verify Deployment

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

### Google Cloud Monitoring Integration

GKE integrates with Google Cloud Monitoring (formerly Stackdriver). You can view:

1. **GKE Dashboard**: Cluster health, resource usage
2. **Logs Explorer**: Centralized logging
3. **Metrics Explorer**: Custom metrics and dashboards
4. **Trace**: Distributed tracing

Access via GCP Console: **Operations** > **Monitoring**

### Grafana Dashboards

```bash
# Port-forward Grafana
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80

# Login credentials
# Username: admin
# Password: (retrieved in Step 9)
```

### Querying Logs with Loki

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
# Create HPA for backend
kubectl autoscale deployment backend --cpu-percent=70 --min=2 --max=10

# Check HPA status
kubectl get hpa
```

### Cluster Autoscaling

GKE cluster autoscaling is already enabled (from Step 2). It will automatically:
- Add nodes when pods can't be scheduled
- Remove nodes when utilization is low

```bash
# Check autoscaler status
gcloud container clusters describe $CLUSTER_NAME --zone $ZONE \
  --format="value(autoscaling)"
```

### Vertical Pod Autoscaling (VPA)

```bash
# Enable VPA
gcloud container clusters update $CLUSTER_NAME --zone $ZONE \
  --enable-vertical-pod-autoscaling

# Create VPA for backend
cat <<EOF | kubectl apply -f -
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: backend-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  updatePolicy:
    updateMode: "Auto"
EOF
```

## Backup and Disaster Recovery

### Velero with GCS Backend

```bash
# Create GCS bucket for backups
gsutil mb -p $PROJECT_ID -l $REGION gs://${PROJECT_ID}-velero-backups/

# Install Velero
velero install \
  --provider gcp \
  --plugins velero/velero-plugin-for-gcp:v1.8.0 \
  --bucket ${PROJECT_ID}-velero-backups \
  --secret-file ./loki-sa-key.json

# Create backup
velero backup create todoapp-backup --include-namespaces default,monitoring,logging

# Restore from backup
velero restore create --from-backup todoapp-backup
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

### GCR Authentication Issues

```bash
# Verify GCR access
gcloud auth configure-docker

# Test image pull
docker pull ${GCR_PROJECT}/backend:latest

# Check GKE service account permissions
kubectl get serviceaccount default -o yaml
```

### Networking Issues

```bash
# Check service endpoints
kubectl get endpoints

# Test service connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- sh
# Inside pod: wget -O- http://backend:8000/health
```

### Load Balancer Issues

```bash
# Check ingress status
kubectl describe ingress todoapp-ingress

# Check backend services
kubectl get backendconfig

# View load balancer in GCP Console
# Compute Engine > Network services > Load balancing
```

## Cost Optimization

1. **Use Preemptible Nodes**: Save up to 80% on compute costs
   ```bash
   gcloud container node-pools create preemptible-pool \
     --cluster $CLUSTER_NAME \
     --zone $ZONE \
     --preemptible \
     --num-nodes 2
   ```

2. **Enable Cluster Autoscaler**: Scale down during off-peak hours

3. **Use Committed Use Discounts**: Save up to 57% with 1-3 year commitments

4. **Right-size Node Machines**: Start with n1-standard-2 and adjust

5. **Use GCP Free Tier**: $300 credit for new accounts

6. **Monitor with Cloud Billing**: Set budgets and alerts

## Security Best Practices

1. **Enable Workload Identity**: Use GCP IAM instead of service account keys
   ```bash
   gcloud container clusters update $CLUSTER_NAME --zone $ZONE \
     --workload-pool=${PROJECT_ID}.svc.id.goog
   ```

2. **Enable Binary Authorization**: Ensure only trusted images are deployed

3. **Use Private GKE Clusters**: Restrict API server access

4. **Enable Network Policies**: Restrict pod-to-pod communication

5. **Use Secret Manager**: Store secrets in GCP Secret Manager

6. **Enable GKE Security Posture**: Automated security scanning

## Cleanup

```bash
# Delete Helm releases
helm uninstall backend recurring-task notification sync audit
helm uninstall kube-prometheus-stack -n monitoring
helm uninstall loki -n logging

# Delete Dapr
dapr uninstall -k

# Delete GKE cluster
gcloud container clusters delete $CLUSTER_NAME --zone $ZONE

# Delete GCS buckets
gsutil rm -r gs://${BUCKET_NAME}/
gsutil rm -r gs://${PROJECT_ID}-velero-backups/

# Delete service account
gcloud iam service-accounts delete loki-storage@${PROJECT_ID}.iam.gserviceaccount.com

# Delete project (optional - deletes all resources)
gcloud projects delete $PROJECT_ID
```

## Additional Resources

- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Google Container Registry](https://cloud.google.com/container-registry/docs)
- [Google Cloud Monitoring](https://cloud.google.com/monitoring/docs)
- [Dapr on GKE](https://docs.dapr.io/operations/hosting/kubernetes/cluster/setup-gke/)
- [GKE Ingress](https://cloud.google.com/kubernetes-engine/docs/concepts/ingress)
