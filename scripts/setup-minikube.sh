#!/bin/bash
set -euo pipefail

# Minikube + Dapr + Kafka Setup Script for Local Development
# Spec 8 - Kafka + Dapr Event-Driven Architecture
# Spec 9 - Monitoring & Logging (optional)

echo "========================================="
echo "Minikube + Dapr + Kafka Setup"
echo "========================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Flags
SKIP_DAPR=false
SKIP_SECRETS=false
WITH_MONITORING=false
WITH_LOGGING=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-dapr)
      SKIP_DAPR=true
      shift
      ;;
    --skip-secrets)
      SKIP_SECRETS=true
      shift
      ;;
    --with-monitoring)
      WITH_MONITORING=true
      shift
      ;;
    --with-logging)
      WITH_LOGGING=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--skip-dapr] [--skip-secrets] [--with-monitoring] [--with-logging]"
      exit 1
      ;;
  esac
done

# Function to print colored messages
print_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
  echo -e "${RED}✗ $1${NC}"
}

print_info() {
  echo -e "${YELLOW}→ $1${NC}"
}

# Check if minikube is installed
check_minikube() {
  print_info "Checking if minikube is installed..."
  if ! command -v minikube &> /dev/null; then
    print_error "minikube is not installed"
    echo ""
    echo "Install minikube:"
    echo "  macOS: brew install minikube"
    echo "  Linux: curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 && sudo install minikube-linux-amd64 /usr/local/bin/minikube"
    echo "  Windows: choco install minikube"
    exit 1
  fi
  print_success "minikube is installed"
}

# Start minikube cluster
start_minikube() {
  print_info "Starting minikube cluster..."

  if minikube status &> /dev/null; then
    print_success "minikube is already running"
  else
    minikube start --cpus=4 --memory=8192 --driver=docker
    print_success "minikube cluster started"
  fi
}

# Install Dapr on Kubernetes
install_dapr() {
  if [ "$SKIP_DAPR" = true ]; then
    print_info "Skipping Dapr installation (--skip-dapr flag)"
    return
  fi

  print_info "Installing Dapr on Kubernetes..."

  if ! command -v dapr &> /dev/null; then
    print_error "Dapr CLI is not installed"
    echo ""
    echo "Install Dapr CLI:"
    echo "  macOS/Linux: wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash"
    echo "  Windows: powershell -Command \"iwr -useb https://raw.githubusercontent.com/dapr/cli/master/install/install.ps1 | iex\""
    exit 1
  fi

  dapr init -k --runtime-version 1.12.0 --wait
  print_success "Dapr installed on Kubernetes"

  # Wait for Dapr to be ready
  print_info "Waiting for Dapr to be ready..."
  kubectl wait --for=condition=ready pod -l app=dapr-operator -n dapr-system --timeout=120s
  kubectl wait --for=condition=ready pod -l app=dapr-sidecar-injector -n dapr-system --timeout=120s
  print_success "Dapr is ready"
}

# Apply Dapr components (Minikube-specific)
apply_dapr_components() {
  print_info "Applying Dapr components for Minikube..."

  if [ ! -d "dapr-components" ]; then
    print_error "dapr-components/ directory not found"
    exit 1
  fi

  # Apply Minikube-specific Pub/Sub component (Redpanda)
  kubectl apply -f dapr-components/pubsub.kafka.minikube.yaml

  # Apply common components (State Store, Secret Store)
  kubectl apply -f dapr-components/statestore.postgresql.yaml
  kubectl apply -f dapr-components/secretstores.kubernetes.yaml

  print_success "Dapr components applied (Minikube with Redpanda)"
}

# Create Kubernetes secrets
create_secrets() {
  if [ "$SKIP_SECRETS" = true ]; then
    print_info "Skipping secrets creation (--skip-secrets flag)"
    return
  fi

  print_info "Creating Kubernetes secrets..."

  # Load .env file
  if [ ! -f "backend/.env" ]; then
    print_error "backend/.env file not found"
    exit 1
  fi

  source backend/.env

  # Create redpanda-creds secret (for Minikube Dapr Pub/Sub component)
  kubectl create secret generic redpanda-creds \
    --from-literal=sasl-username="$REDPANDA_SASL_USERNAME" \
    --from-literal=sasl-password="$REDPANDA_SASL_PASSWORD" \
    --dry-run=client -o yaml | kubectl apply -f -

  # Create app-secrets (for application environment variables)
  kubectl create secret generic app-secrets \
    --from-literal=database-url="$DATABASE_URL" \
    --from-literal=better-auth-secret="$BETTER_AUTH_SECRET" \
    --from-literal=sendgrid-api-key="$SENDGRID_API_KEY" \
    --from-literal=fcm-server-key="$FCM_SERVER_KEY" \
    --dry-run=client -o yaml | kubectl apply -f -

  print_success "Kubernetes secrets created (Redpanda credentials for Minikube)"
}

# Deploy monitoring stack (Spec 9 - T024)
deploy_monitoring() {
  if [ "$WITH_MONITORING" = false ]; then
    print_info "Skipping monitoring stack deployment (use --with-monitoring to enable)"
    return
  fi

  print_info "Deploying monitoring stack (Prometheus + Grafana)..."

  # Check if Helm is installed
  if ! command -v helm &> /dev/null; then
    print_error "Helm is not installed"
    echo ""
    echo "Install Helm:"
    echo "  macOS: brew install helm"
    echo "  Linux: curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash"
    echo "  Windows: choco install kubernetes-helm"
    exit 1
  fi

  # Add Prometheus Helm repository
  print_info "Adding Prometheus Helm repository..."
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
  helm repo update

  # Create monitoring namespace
  kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

  # Deploy kube-prometheus-stack
  print_info "Installing kube-prometheus-stack..."
  helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
    --namespace monitoring \
    --values helm/monitoring/values.yaml \
    --wait \
    --timeout 10m

  # Wait for Prometheus and Grafana to be ready
  print_info "Waiting for Prometheus and Grafana to be ready..."
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n monitoring --timeout=300s || true
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana -n monitoring --timeout=300s || true

  print_success "Monitoring stack deployed successfully"
  echo ""
  echo "Access Grafana dashboard:"
  echo "  kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80"
  echo "  Open: http://localhost:3000"
  echo "  Login: admin / admin"
  echo ""
}

# Deploy logging stack (Spec 9 - T040)
deploy_logging() {
  if [ "$WITH_LOGGING" = false ]; then
    print_info "Skipping logging stack deployment (use --with-logging to enable)"
    return
  fi

  print_info "Deploying logging stack (Loki + Promtail)..."

  # Check if Helm is installed
  if ! command -v helm &> /dev/null; then
    print_error "Helm is not installed"
    echo ""
    echo "Install Helm:"
    echo "  macOS: brew install helm"
    echo "  Linux: curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash"
    echo "  Windows: choco install kubernetes-helm"
    exit 1
  fi

  # Add Grafana Helm repository
  print_info "Adding Grafana Helm repository..."
  helm repo add grafana https://grafana.github.io/helm-charts
  helm repo update

  # Create logging namespace
  kubectl create namespace logging --dry-run=client -o yaml | kubectl apply -f -

  # Deploy Loki stack
  print_info "Installing Loki stack..."
  helm upgrade --install loki grafana/loki-stack \
    --namespace logging \
    --values helm/logging/values.yaml \
    --wait \
    --timeout 10m

  # Wait for Loki and Promtail to be ready
  print_info "Waiting for Loki and Promtail to be ready..."
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=loki -n logging --timeout=300s || true
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=promtail -n logging --timeout=300s || true

  print_success "Logging stack deployed successfully"
  echo ""
  echo "Access Loki query interface:"
  echo "  kubectl port-forward -n logging svc/loki-gateway 3100:80"
  echo "  Query logs: http://localhost:3100/loki/api/v1/query"
  echo ""
  echo "View logs in Grafana:"
  echo "  1. Access Grafana dashboard (from monitoring stack)"
  echo "  2. Go to Explore"
  echo "  3. Select Loki data source"
  echo "  4. Query logs using LogQL: {namespace=\"default\", app=\"backend\"}"
  echo ""
}

# Main execution
main() {
  check_minikube
  start_minikube
  install_dapr
  apply_dapr_components
  create_secrets
  deploy_monitoring
  deploy_logging

  echo ""
  echo "========================================="
  print_success "Setup complete!"
  echo "========================================="
  echo ""
  echo "Next steps:"
  echo "  1. Build Docker images: ./scripts/deploy-local.sh"
  echo "  2. Access services:"
  echo "     - Backend API: kubectl port-forward svc/backend 8000:8000"
  echo "     - Sync Service: kubectl port-forward svc/sync-service 8003:8003"
  if [ "$WITH_MONITORING" = true ]; then
    echo "     - Grafana: kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80"
  fi
  if [ "$WITH_LOGGING" = true ]; then
    echo "     - Loki: kubectl port-forward -n logging svc/loki-gateway 3100:80"
  fi
  echo "  3. View Dapr dashboard: dapr dashboard -k"
  echo ""
}

main
