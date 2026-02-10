# Azure Kubernetes Service (AKS) Deployment Guide

This guide walks you through deploying the Todo App to Azure Kubernetes Service (AKS) with full monitoring and logging capabilities.

## Prerequisites

- Azure account with active subscription
- Azure CLI installed and configured
- kubectl installed
- Helm 3 installed
- Docker installed (for building images)
- Azure Container Registry (ACR) access

## Step 1: Create Resource Group

```bash
# Set environment variables
export RESOURCE_GROUP=todoapp-rg
export LOCATION=eastus
export CLUSTER_NAME=todoapp-cluster
export ACR_NAME=todoappacr

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION
```

## Step 2: Create Azure Container Registry (ACR)

```bash
# Create ACR
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Standard

# Login to ACR
az acr login --name $ACR_NAME

# Get ACR login server
export ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)
```

## Step 3: Create AKS Cluster

```bash
# Create AKS cluster with managed identity
az aks create \
  --resource-group $RESOURCE_GROUP \
  --name $CLUSTER_NAME \
  --node-count 3 \
  --node-vm-size Standard_D2s_v3 \
  --enable-managed-identity \
  --generate-ssh-keys \
  --attach-acr $ACR_NAME \
  --enable-addons monitoring

# Get credentials
az aks get-credentials \
  --resource-group $RESOURCE_GROUP \
  --name $CLUSTER_NAME

# Verify connection
kubectl cluster-info
kubectl get nodes
```

## Step 4: Build and Push Docker Images

```bash
# Build and push backend
docker build -t ${ACR_LOGIN_SERVER}/backend:latest ./backend
docker push ${ACR_LOGIN_SERVER}/backend:latest

# Build and push microservices
docker build -t ${ACR_LOGIN_SERVER}/recurring-task:latest ./backend/services/recurring-task
docker push ${ACR_LOGIN_SERVER}/recurring-task:latest

docker build -t ${ACR_LOGIN_SERVER}/notification:latest ./backend/services/notification
docker push ${ACR_LOGIN_SERVER}/notification:latest

docker build -t ${ACR_LOGIN_SERVER}/sync:latest ./backend/services/sync
docker push ${ACR_LOGIN_SERVER}/sync:latest

docker build -t ${ACR_LOGIN_SERVER}/audit:latest ./backend/services/audit
docker push ${ACR_LOGIN_SERVER}/audit:latest
```

## Step 5: Create Azure Storage for Loki

```bash
# Create storage account
export STORAGE_ACCOUNT=todoapplogsstorage

az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# Create container for Loki chunks
az storage container create \
  --name loki-chunks \
  --account-name $STORAGE_ACCOUNT

# Get storage account key
export AZURE_STORAGE_KEY=$(az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT \
  --query '[0].value' \
  --output tsv)
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

# Create Azure Storage secret for Loki
kubectl create secret generic azure-storage-secret \
  --from-literal=accountName=$STORAGE_ACCOUNT \
  --from-literal=accountKey=$AZURE_STORAGE_KEY \
  -n logging

# Create Kafka credentials (if using Azure Event Hubs)
kubectl create secret generic kafka-creds \
  --from-literal=sasl-username="<event-hub-connection-string>" \
  --from-literal=sasl-password="<event-hub-key>"
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
# Apply AKS-specific Dapr components
kubectl apply -f dapr-components/pubsub.kafka.aks.yaml
kubectl apply -f dapr-components/statestore.postgresql.yaml
kubectl apply -f dapr-components/secretstores.kubernetes.yaml
```

## Step 9: Deploy Monitoring Stack

```bash
# Deploy Prometheus + Grafana
./scripts/deploy-monitoring.sh --environment aks

# Wait for deployment
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n monitoring --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana -n monitoring --timeout=300s

# Get Grafana admin password
kubectl get secret -n monitoring kube-prometheus-stack-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode
```

## Step 10: Deploy Logging Stack

```bash
# Deploy Loki + Promtail with Azure Storage backend
./scripts/deploy-logging.sh --environment aks

# Wait for deployment
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=loki -n logging --timeout=300s
```

## Step 11: Deploy Application Services

```bash
# Deploy backend
helm upgrade --install backend ./helm/backend \
  --values ./helm/backend/values-aks.yaml \
  --set image.repository=${ACR_LOGIN_SERVER}/backend \
  --set image.tag=latest

# Deploy microservices
helm upgrade --install recurring-task ./helm/recurring-task \
  --values ./helm/recurring-task/values-aks.yaml \
  --set image.repository=${ACR_LOGIN_SERVER}/recurring-task

helm upgrade --install notification ./helm/notification \
  --values ./helm/notification/values-aks.yaml \
  --set image.repository=${ACR_LOGIN_SERVER}/notification

helm upgrade --install sync ./helm/sync \
  --values ./helm/sync/values-aks.yaml \
  --set image.repository=${ACR_LOGIN_SERVER}/sync

helm upgrade --install audit ./helm/audit \
  --values ./helm/audit/values-aks.yaml \
  --set image.repository=${ACR_LOGIN_SERVER}/audit
```

## Step 12: Configure Ingress

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Wait for Load Balancer IP
kubectl get svc -n ingress-nginx ingress-nginx-controller

# Get external IP
export EXTERNAL_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "External IP: $EXTERNAL_IP"

# Configure DNS
# Create A record: todoapp.example.com -> $EXTERNAL_IP

# Apply ingress resources
kubectl apply -f k8s/ingress-aks.yaml
```

## Step 13: Configure TLS with Let's Encrypt (Optional)

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# Update ingress to use TLS
# Add annotations and tls section to ingress-aks.yaml
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

### Azure Monitor Integration

AKS comes with Azure Monitor Container Insights enabled. You can view:

1. **Cluster Performance**: CPU, memory, network metrics
2. **Container Logs**: Centralized logging via Azure Log Analytics
3. **Live Logs**: Real-time log streaming

Access via Azure Portal: **Monitor** > **Containers** > Select your cluster

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

```bash
# Enable cluster autoscaler
az aks update \
  --resource-group $RESOURCE_GROUP \
  --name $CLUSTER_NAME \
  --enable-cluster-autoscaler \
  --min-count 3 \
  --max-count 10
```

### Node Pool Scaling

```bash
# Scale node pool manually
az aks scale \
  --resource-group $RESOURCE_GROUP \
  --name $CLUSTER_NAME \
  --node-count 5
```

## Backup and Disaster Recovery

### Velero Backup

```bash
# Install Velero
kubectl apply -f https://github.com/vmware-tanzu/velero/releases/download/v1.12.0/velero-v1.12.0-linux-amd64.tar.gz

# Create backup
velero backup create todoapp-backup --include-namespaces default,monitoring,logging

# Restore from backup
velero restore create --from-backup todoapp-backup
```

### Database Backups

Ensure Neon PostgreSQL automated backups are enabled (default: 7-day retention).

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

### ACR Authentication Issues

```bash
# Verify ACR integration
az aks check-acr \
  --resource-group $RESOURCE_GROUP \
  --name $CLUSTER_NAME \
  --acr $ACR_NAME

# Re-attach ACR if needed
az aks update \
  --resource-group $RESOURCE_GROUP \
  --name $CLUSTER_NAME \
  --attach-acr $ACR_NAME
```

### Networking Issues

```bash
# Check service endpoints
kubectl get endpoints

# Test service connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- sh
# Inside pod: wget -O- http://backend:8000/health
```

### Azure Storage Issues (Loki)

```bash
# Verify storage account access
az storage account show \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP

# Check Loki logs
kubectl logs -n logging -l app.kubernetes.io/name=loki
```

## Cost Optimization

1. **Use Azure Reserved Instances**: Save up to 72% on VM costs
2. **Enable Cluster Autoscaler**: Scale down during off-peak hours
3. **Use Spot Instances**: For non-production workloads (up to 90% savings)
4. **Right-size Node VMs**: Start with Standard_D2s_v3 and adjust based on usage
5. **Monitor with Azure Cost Management**: Track spending and set budgets
6. **Use Azure Hybrid Benefit**: If you have Windows Server licenses

## Security Best Practices

1. **Enable Azure AD Integration**: Use Azure AD for RBAC
2. **Use Azure Key Vault**: Store secrets in Key Vault instead of Kubernetes secrets
3. **Enable Network Policies**: Restrict pod-to-pod communication
4. **Use Azure Policy**: Enforce security standards across cluster
5. **Enable Azure Defender**: For advanced threat protection
6. **Regular Updates**: Keep AKS and node images up to date

## Cleanup

```bash
# Delete Helm releases
helm uninstall backend recurring-task notification sync audit
helm uninstall kube-prometheus-stack -n monitoring
helm uninstall loki -n logging

# Delete Dapr
dapr uninstall -k

# Delete AKS cluster and all resources
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

## Additional Resources

- [AKS Documentation](https://docs.microsoft.com/en-us/azure/aks/)
- [Azure Container Registry](https://docs.microsoft.com/en-us/azure/container-registry/)
- [Azure Monitor for Containers](https://docs.microsoft.com/en-us/azure/azure-monitor/containers/container-insights-overview)
- [Dapr on AKS](https://docs.dapr.io/operations/hosting/kubernetes/cluster/setup-aks/)
- [NGINX Ingress on AKS](https://docs.microsoft.com/en-us/azure/aks/ingress-basic)
