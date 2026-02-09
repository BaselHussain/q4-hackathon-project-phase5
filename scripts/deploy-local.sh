#!/bin/bash
set -euo pipefail

# Local Deployment Script for Minikube
# Builds Docker images and deploys all services via Helm

echo "========================================="
echo "Local Deployment to Minikube"
echo "========================================="

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
  echo -e "${RED}✗ $1${NC}"
}

print_info() {
  echo -e "${YELLOW}→ $1${NC}"
}

# Check minikube is running
check_minikube() {
  print_info "Checking minikube status..."
  if ! minikube status &> /dev/null; then
    print_error "minikube is not running"
    echo "Run: ./scripts/setup-minikube.sh"
    exit 1
  fi
  print_success "minikube is running"
}

# Build Docker images
build_images() {
  print_info "Building Docker images..."

  # Use minikube's Docker daemon
  eval $(minikube docker-env)

  # Backend API
  print_info "Building backend-api..."
  docker build -t backend-api:latest -f backend/Dockerfile backend/

  # Recurring Task Service
  print_info "Building recurring-task-service..."
  docker build -t recurring-task-service:latest -f backend/services/recurring-task/Dockerfile backend/services/recurring-task/

  # Notification Service
  print_info "Building notification-service..."
  docker build -t notification-service:latest -f backend/services/notification/Dockerfile backend/services/notification/

  # Sync Service
  print_info "Building sync-service..."
  docker build -t sync-service:latest -f backend/services/sync/Dockerfile backend/services/sync/

  # Audit Service
  print_info "Building audit-service..."
  docker build -t audit-service:latest -f backend/services/audit/Dockerfile backend/services/audit/

  print_success "All images built"
}

# Deploy Helm charts
deploy_helm_charts() {
  print_info "Deploying Helm charts..."

  helm upgrade --install backend helm/backend/ -f helm/backend/values.yaml
  helm upgrade --install recurring-task helm/recurring-task/ -f helm/recurring-task/values.yaml
  helm upgrade --install notification helm/notification/ -f helm/notification/values.yaml
  helm upgrade --install sync helm/sync/ -f helm/sync/values.yaml
  helm upgrade --install audit helm/audit/ -f helm/audit/values.yaml

  print_success "All Helm charts deployed"
}

# Wait for pods to be ready
wait_for_pods() {
  print_info "Waiting for pods to be ready..."

  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=backend --timeout=120s
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=recurring-task --timeout=120s
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=notification --timeout=120s
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=sync --timeout=120s
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=audit --timeout=120s

  print_success "All pods are ready"
}

# Print service status
print_status() {
  echo ""
  echo "========================================="
  print_success "Deployment complete!"
  echo "========================================="
  echo ""
  echo "Service Status:"
  kubectl get pods
  echo ""
  echo "Access services:"
  echo "  Backend API:  kubectl port-forward svc/backend 8000:8000"
  echo "  Sync Service: kubectl port-forward svc/sync-service 8003:8003"
  echo ""
  echo "View logs:"
  echo "  kubectl logs -l app.kubernetes.io/name=backend -c backend --tail=50 -f"
  echo ""
  echo "Dapr dashboard:"
  echo "  dapr dashboard -k"
  echo ""
}

# Main execution
main() {
  check_minikube
  build_images
  deploy_helm_charts
  wait_for_pods
  print_status
}

main
