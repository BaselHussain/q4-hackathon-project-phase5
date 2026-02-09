# Oracle Cloud Infrastructure Setup Guide

Complete guide for deploying the Event-Driven Todo App on Oracle Cloud Infrastructure (OCI).

## Prerequisites

- OCI CLI installed and configured (`oci setup config`)
- kubectl installed
- Helm 3.x installed
- Dapr CLI 1.12+ installed
- OCI account with appropriate permissions

## Architecture on OCI

- **Compute**: Oracle Kubernetes Engine (OKE)
- **Messaging**: Oracle Streaming Service (Kafka-compatible)
- **Database**: Neon PostgreSQL (external, no change)
- **Ingress**: OCI Native Ingress Controller with Load Balancer
- **Service Mesh**: Dapr 1.12+ on OKE

---

## Step 1: Set Environment Variables

```bash
# OCI Configuration
export COMPARTMENT_ID="ocid1.compartment.oc1..your-compartment-id"
export TENANCY_NAME="your-tenancy-name"
export OCI_REGION="ap-mumbai-1"
export OCI_USERNAME="your-username"

# VCN Configuration (if creating new VCN)
export VCN_CIDR="10.0.0.0/16"
export SUBNET_CIDR="10.0.10.0/24"

# Application Configuration
export APP_NAME="todo-app"
export NAMESPACE="todo-app"
```

---

## Step 2: Create VCN and Subnets (if not exists)

```bash
# Create VCN
VCN_ID=$(oci network vcn create \
  --compartment-id $COMPARTMENT_ID \
  --display-name "${APP_NAME}-vcn" \
  --cidr-block $VCN_CIDR \
  --dns-label todovcn \
  --query 'data.id' \
  --raw-output)

echo "VCN ID: $VCN_ID"

# Create Internet Gateway
IGW_ID=$(oci network internet-gateway create \
  --compartment-id $COMPARTMENT_ID \
  --vcn-id $VCN_ID \
  --display-name "${APP_NAME}-igw" \
  --is-enabled true \
  --query 'data.id' \
  --raw-output)

# Create Route Table
RT_ID=$(oci network route-table create \
  --compartment-id $COMPARTMENT_ID \
  --vcn-id $VCN_ID \
  --display-name "${APP_NAME}-rt" \
  --route-rules '[{"destination":"0.0.0.0/0","networkEntityId":"'$IGW_ID'"}]' \
  --query 'data.id' \
  --raw-output)

# Create Security List (allow all for simplicity - restrict in production)
SL_ID=$(oci network security-list create \
  --compartment-id $COMPARTMENT_ID \
  --vcn-id $VCN_ID \
  --display-name "${APP_NAME}-sl" \
  --egress-security-rules '[{"destination":"0.0.0.0/0","protocol":"all","isStateless":false}]' \
  --ingress-security-rules '[{"source":"0.0.0.0/0","protocol":"6","isStateless":false,"tcpOptions":{"destinationPortRange":{"min":80,"max":80}}},{"source":"0.0.0.0/0","protocol":"6","isStateless":false,"tcpOptions":{"destinationPortRange":{"min":443,"max":443}}},{"source":"0.0.0.0/0","protocol":"6","isStateless":false,"tcpOptions":{"destinationPortRange":{"min":8003,"max":8003}}}]' \
  --query 'data.id' \
  --raw-output)

# Create Subnet
SUBNET_ID=$(oci network subnet create \
  --compartment-id $COMPARTMENT_ID \
  --vcn-id $VCN_ID \
  --display-name "${APP_NAME}-subnet" \
  --cidr-block $SUBNET_CIDR \
  --route-table-id $RT_ID \
  --security-list-ids "[\"$SL_ID\"]" \
  --dns-label todosubnet \
  --query 'data.id' \
  --raw-output)

echo "Subnet ID: $SUBNET_ID"
```

---

## Step 3: Create Oracle Streaming Service

### 3.1 Create Stream Pool

```bash
STREAM_POOL_ID=$(oci streaming admin stream-pool create \
  --compartment-id $COMPARTMENT_ID \
  --name "${APP_NAME}-stream-pool" \
  --query 'data.id' \
  --raw-output)

echo "Stream Pool ID: $STREAM_POOL_ID"

# Wait for stream pool to become active
oci streaming admin stream-pool get \
  --stream-pool-id $STREAM_POOL_ID \
  --wait-for-state ACTIVE
```

### 3.2 Create Streams (Topics)

```bash
# Create task-events stream (3 partitions)
STREAM_TASK_EVENTS=$(oci streaming admin stream create \
  --compartment-id $COMPARTMENT_ID \
  --stream-pool-id $STREAM_POOL_ID \
  --name "task-events" \
  --partitions 3 \
  --retention-in-hours 168 \
  --query 'data.id' \
  --raw-output)

echo "task-events Stream ID: $STREAM_TASK_EVENTS"

# Create reminders stream (1 partition)
STREAM_REMINDERS=$(oci streaming admin stream create \
  --compartment-id $COMPARTMENT_ID \
  --stream-pool-id $STREAM_POOL_ID \
  --name "reminders" \
  --partitions 1 \
  --retention-in-hours 24 \
  --query 'data.id' \
  --raw-output)

echo "reminders Stream ID: $STREAM_REMINDERS"

# Create task-updates stream (3 partitions)
STREAM_TASK_UPDATES=$(oci streaming admin stream create \
  --compartment-id $COMPARTMENT_ID \
  --stream-pool-id $STREAM_POOL_ID \
  --name "task-updates" \
  --partitions 3 \
  --retention-in-hours 24 \
  --query 'data.id' \
  --raw-output)

echo "task-updates Stream ID: $STREAM_TASK_UPDATES"

# Wait for all streams to become active
oci streaming admin stream get --stream-id $STREAM_TASK_EVENTS --wait-for-state ACTIVE
oci streaming admin stream get --stream-id $STREAM_REMINDERS --wait-for-state ACTIVE
oci streaming admin stream get --stream-id $STREAM_TASK_UPDATES --wait-for-state ACTIVE
```

### 3.3 Get Streaming Endpoint

```bash
# Get the Kafka connection endpoint
STREAMING_ENDPOINT=$(oci streaming admin stream-pool get \
  --stream-pool-id $STREAM_POOL_ID \
  --query 'data."kafka-settings"."bootstrap-servers"' \
  --raw-output)

echo "Streaming Endpoint: $STREAMING_ENDPOINT"
# Example: cell-1.streaming.ap-mumbai-1.oci.oraclecloud.com:9092
```

### 3.4 Generate Auth Token

```bash
# Create auth token for streaming authentication
# Note: Save this token securely - it won't be shown again
AUTH_TOKEN=$(oci iam auth-token create \
  --user-id $(oci iam user list --query 'data[0].id' --raw-output) \
  --description "Todo App Streaming Auth Token" \
  --query 'data.token' \
  --raw-output)

echo "Auth Token: $AUTH_TOKEN"
echo "IMPORTANT: Save this token - it cannot be retrieved later!"

# Construct SASL username
SASL_USERNAME="${TENANCY_NAME}/${OCI_USERNAME}/${STREAM_POOL_ID}"
echo "SASL Username: $SASL_USERNAME"
```

---

## Step 4: Create OKE Cluster

### 4.1 Create OKE Cluster

```bash
OKE_CLUSTER_ID=$(oci ce cluster create \
  --compartment-id $COMPARTMENT_ID \
  --name "${APP_NAME}-oke-cluster" \
  --vcn-id $VCN_ID \
  --kubernetes-version "v1.28.2" \
  --service-lb-subnet-ids "[\"$SUBNET_ID\"]" \
  --endpoint-subnet-id $SUBNET_ID \
  --options '{"serviceLbSubnetIds":["'$SUBNET_ID'"],"addOns":{"isKubernetesDashboardEnabled":true,"isTillerEnabled":false}}' \
  --query 'data.id' \
  --raw-output)

echo "OKE Cluster ID: $OKE_CLUSTER_ID"

# Wait for cluster to become active (takes ~7 minutes)
oci ce cluster get \
  --cluster-id $OKE_CLUSTER_ID \
  --wait-for-state ACTIVE
```

### 4.2 Create Node Pool

```bash
NODE_POOL_ID=$(oci ce node-pool create \
  --cluster-id $OKE_CLUSTER_ID \
  --compartment-id $COMPARTMENT_ID \
  --name "${APP_NAME}-node-pool" \
  --node-shape "VM.Standard.E4.Flex" \
  --node-shape-config '{"ocpus":2,"memoryInGBs":16}' \
  --size 3 \
  --placement-configs "[{\"availabilityDomain\":\"$(oci iam availability-domain list --query 'data[0].name' --raw-output)\",\"subnetId\":\"$SUBNET_ID\"}]" \
  --node-source-details '{"sourceType":"IMAGE","imageId":"'$(oci compute image list --compartment-id $COMPARTMENT_ID --operating-system "Oracle Linux" --operating-system-version "8" --shape "VM.Standard.E4.Flex" --query 'data[0].id' --raw-output)'"}' \
  --kubernetes-version "v1.28.2" \
  --query 'data.id' \
  --raw-output)

echo "Node Pool ID: $NODE_POOL_ID"

# Wait for node pool to become active (takes ~5 minutes)
oci ce node-pool get \
  --node-pool-id $NODE_POOL_ID \
  --wait-for-state ACTIVE
```

---

## Step 5: Configure kubectl

```bash
# Create kubeconfig for OKE cluster
mkdir -p ~/.kube
oci ce cluster create-kubeconfig \
  --cluster-id $OKE_CLUSTER_ID \
  --file ~/.kube/config-oke \
  --region $OCI_REGION \
  --token-version 2.0.0 \
  --kube-endpoint PUBLIC_ENDPOINT

# Set kubectl context
export KUBECONFIG=~/.kube/config-oke
kubectl config use-context $(kubectl config get-contexts -o name)

# Verify connection
kubectl get nodes
# Should show 3 nodes in Ready state
```

---

## Step 6: Install Dapr on OKE

```bash
# Initialize Dapr on Kubernetes
dapr init -k --runtime-version 1.12.0 --wait

# Verify Dapr installation
kubectl get pods -n dapr-system
# Should show dapr-operator, dapr-sidecar-injector, dapr-sentry, dapr-placement-server

# Wait for all Dapr pods to be ready
kubectl wait --for=condition=ready pod -l app=dapr-operator -n dapr-system --timeout=120s
kubectl wait --for=condition=ready pod -l app=dapr-sidecar-injector -n dapr-system --timeout=120s
```

---

## Step 7: Create Kubernetes Namespace and Secrets

```bash
# Create application namespace
kubectl create namespace $NAMESPACE

# Create secret for Oracle Streaming credentials
kubectl create secret generic oci-streaming-creds \
  --from-literal=sasl-username="$SASL_USERNAME" \
  --from-literal=auth-token="$AUTH_TOKEN" \
  --namespace $NAMESPACE

# Create secret for application configuration
kubectl create secret generic app-secrets \
  --from-literal=database-url="$DATABASE_URL" \
  --from-literal=better-auth-secret="$BETTER_AUTH_SECRET" \
  --from-literal=sendgrid-api-key="$SENDGRID_API_KEY" \
  --from-literal=fcm-server-key="$FCM_SERVER_KEY" \
  --namespace $NAMESPACE

# Verify secrets created
kubectl get secrets -n $NAMESPACE
```

---

## Step 8: Update Dapr Components for Oracle Streaming

The `dapr-components/pubsub.kafka.oke.yaml` is configured for Oracle Streaming Service (OKE production deployment).

Apply Dapr components:

```bash
# Apply OKE-specific Pub/Sub component (Oracle Streaming)
kubectl apply -f dapr-components/pubsub.kafka.oke.yaml -n $NAMESPACE

# Apply common components (State Store, Secret Store)
kubectl apply -f dapr-components/statestore.postgresql.yaml -n $NAMESPACE
kubectl apply -f dapr-components/secretstores.kubernetes.yaml -n $NAMESPACE

# Verify components
kubectl get components -n $NAMESPACE
# Should show: pubsub, statestore, kubernetes-secrets
```

**Note:** For Minikube local development, use `pubsub.kafka.minikube.yaml` which is configured for Redpanda.

---

## Step 9: Deploy Services via Helm

### 9.1 Build and Push Docker Images to OCIR

```bash
# Login to Oracle Container Registry
docker login ${OCI_REGION}.ocir.io -u ${TENANCY_NAME}/${OCI_USERNAME}

# Build and push images
export OCIR_REPO="${OCI_REGION}.ocir.io/${TENANCY_NAME}/${APP_NAME}"

# Backend API
docker build -t ${OCIR_REPO}/backend-api:latest -f backend/Dockerfile backend/
docker push ${OCIR_REPO}/backend-api:latest

# Recurring Task Service
docker build -t ${OCIR_REPO}/recurring-task-service:latest -f backend/services/recurring-task/Dockerfile backend/services/recurring-task/
docker push ${OCIR_REPO}/recurring-task-service:latest

# Notification Service
docker build -t ${OCIR_REPO}/notification-service:latest -f backend/services/notification/Dockerfile backend/services/notification/
docker push ${OCIR_REPO}/notification-service:latest

# Sync Service
docker build -t ${OCIR_REPO}/sync-service:latest -f backend/services/sync/Dockerfile backend/services/sync/
docker push ${OCIR_REPO}/sync-service:latest

# Audit Service
docker build -t ${OCIR_REPO}/audit-service:latest -f backend/services/audit/Dockerfile backend/services/audit/
docker push ${OCIR_REPO}/audit-service:latest
```

### 9.2 Deploy Helm Charts

```bash
# Deploy backend API
helm upgrade --install backend helm/backend/ \
  --set image.repository=${OCIR_REPO}/backend-api \
  --set image.tag=latest \
  --namespace $NAMESPACE \
  --create-namespace

# Deploy recurring-task service
helm upgrade --install recurring-task helm/recurring-task/ \
  --set image.repository=${OCIR_REPO}/recurring-task-service \
  --set image.tag=latest \
  --namespace $NAMESPACE

# Deploy notification service
helm upgrade --install notification helm/notification/ \
  --set image.repository=${OCIR_REPO}/notification-service \
  --set image.tag=latest \
  --namespace $NAMESPACE

# Deploy sync service (WebSocket)
helm upgrade --install sync helm/sync/ \
  --set image.repository=${OCIR_REPO}/sync-service \
  --set image.tag=latest \
  --namespace $NAMESPACE

# Deploy audit service
helm upgrade --install audit helm/audit/ \
  --set image.repository=${OCIR_REPO}/audit-service \
  --set image.tag=latest \
  --namespace $NAMESPACE

# Wait for all pods to be ready
kubectl wait --for=condition=ready pod --all -n $NAMESPACE --timeout=300s
```

---

## Step 10: Configure Ingress for HTTP and WebSocket

### 10.1 Install OCI Native Ingress Controller

```bash
# Install OCI Native Ingress Controller
kubectl apply -f https://github.com/oracle/oci-native-ingress-controller/releases/latest/download/oci-native-ingress-controller.yaml

# Wait for controller to be ready
kubectl wait --for=condition=ready pod -l app=oci-native-ingress-controller -n oci-native-ingress-controller-system --timeout=120s
```

### 10.2 Create Ingress Resources

See updated `helm/backend/templates/ingress.yaml` and `helm/sync/templates/ingress.yaml` files for WebSocket support.

Apply ingress:

```bash
# Backend API ingress
kubectl apply -f helm/backend/templates/ingress.yaml -n $NAMESPACE

# Sync Service ingress (WebSocket)
kubectl apply -f helm/sync/templates/ingress.yaml -n $NAMESPACE

# Get Load Balancer IP
kubectl get ingress -n $NAMESPACE
# Wait for EXTERNAL-IP to be assigned (takes ~2 minutes)
```

---

## Step 11: Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n $NAMESPACE

# Check services
kubectl get svc -n $NAMESPACE

# Check ingress
kubectl get ingress -n $NAMESPACE

# Get Load Balancer IP
LB_IP=$(kubectl get ingress backend-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Backend API: http://${LB_IP}/health"

# Test backend health
curl http://${LB_IP}/health

# Get WebSocket endpoint
WS_IP=$(kubectl get ingress sync-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "WebSocket: ws://${WS_IP}/ws/tasks"
```

---

## Step 12: View Logs and Monitor

```bash
# View backend logs
kubectl logs -l app.kubernetes.io/name=backend -c backend -n $NAMESPACE --tail=50 -f

# View Dapr sidecar logs
kubectl logs -l app.kubernetes.io/name=backend -c daprd -n $NAMESPACE --tail=50 -f

# View all service logs
kubectl logs -l dapr.io/enabled=true --all-containers -n $NAMESPACE --tail=50 -f

# Dapr dashboard
dapr dashboard -k -n $NAMESPACE
# Opens http://localhost:8080
```

---

## Cleanup (Optional)

```bash
# Delete Helm releases
helm uninstall backend recurring-task notification sync audit -n $NAMESPACE

# Delete namespace
kubectl delete namespace $NAMESPACE

# Delete OKE cluster
oci ce cluster delete --cluster-id $OKE_CLUSTER_ID --force

# Delete streams
oci streaming admin stream delete --stream-id $STREAM_TASK_EVENTS --force
oci streaming admin stream delete --stream-id $STREAM_REMINDERS --force
oci streaming admin stream delete --stream-id $STREAM_TASK_UPDATES --force

# Delete stream pool
oci streaming admin stream-pool delete --stream-pool-id $STREAM_POOL_ID --force

# Delete VCN (if created)
oci network vcn delete --vcn-id $VCN_ID --force
```

---

## Cost Optimization Tips

1. **Use Always Free Tier** where possible (2 VMs, 10GB block storage)
2. **Auto-scaling**: Configure HPA for services based on CPU/memory
3. **Spot Instances**: Use preemptible nodes for non-critical workloads
4. **Stream Retention**: Reduce retention hours for reminders/task-updates (24h vs 168h)
5. **Node Pool Size**: Start with 2 nodes, scale up as needed

---

## Troubleshooting

### Pods not starting
```bash
kubectl describe pod <pod-name> -n $NAMESPACE
kubectl logs <pod-name> -c <container-name> -n $NAMESPACE
```

### Dapr sidecar issues
```bash
kubectl logs <pod-name> -c daprd -n $NAMESPACE
kubectl get components -n $NAMESPACE
```

### Streaming connection issues
```bash
# Test connectivity from pod
kubectl run -it --rm debug --image=busybox --restart=Never -n $NAMESPACE -- sh
# Inside pod: nc -zv cell-1.streaming.ap-mumbai-1.oci.oraclecloud.com 9092
```

### WebSocket not connecting
```bash
# Check ingress configuration
kubectl describe ingress sync-ingress -n $NAMESPACE

# Check service endpoints
kubectl get endpoints -n $NAMESPACE
```
