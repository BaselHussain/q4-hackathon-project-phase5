#!/bin/bash
set -euo pipefail

# Deploy Monitoring Stack Script
# Spec 9 - Monitoring, Logging, and Multi-Cloud Deployment
#
# This script deploys the monitoring stack (Prometheus + Grafana) to any Kubernetes cluster
# (Minikube, OKE, AKS, GKE)

echo "========================================="
echo "Monitoring Stack Deployment"
echo "========================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
NAMESPACE="monitoring"
ENVIRONMENT="minikube"
VALUES_FILE=""

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

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --namespace)
      NAMESPACE="$2"
      shift 2
      ;;
    --values)
      VALUES_FILE="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --environment ENV    Target environment: minikube, oke, aks, gke (default: minikube)"
      echo "  --namespace NS       Kubernetes namespace (default: monitoring)"
      echo "  --values FILE        Custom values file (overrides environment default)"
      echo "  --help               Show this help message"
      echo ""
      echo "Examples:"
      echo "  $0                                    # Deploy to Minikube with default values"
      echo "  $0 --environment oke                  # Deploy to OKE with OKE-specific values"
      echo "  $0 --values custom-values.yaml        # Deploy with custom values file"
      exit 0
      ;;
    *)
      print_error "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Determine values file based on environment
if [ -z "$VALUES_FILE" ]; then
  case $ENVIRONMENT in
    minikube)
      VALUES_FILE="helm/monitoring/values.yaml"
      ;;
    oke)
      VALUES_FILE="helm/monitoring/values-oke.yaml"
      ;;
    aks)
      VALUES_FILE="helm/monitoring/values-aks.yaml"
      ;;
    gke)
      VALUES_FILE="helm/monitoring/values-gke.yaml"
      ;;
    *)
      print_error "Invalid environment: $ENVIRONMENT"
      echo "Valid environments: minikube, oke, aks, gke"
      exit 1
      ;;
  esac
fi

# Check if values file exists
if [ ! -f "$VALUES_FILE" ]; then
  print_error "Values file not found: $VALUES_FILE"
  exit 1
fi

print_info "Deployment configuration:"
echo "  Environment: $ENVIRONMENT"
echo "  Namespace: $NAMESPACE"
echo "  Values file: $VALUES_FILE"
echo ""

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

print_success "Helm is installed"

# Check if kubectl is configured
if ! kubectl cluster-info &> /dev/null; then
  print_error "kubectl is not configured or cluster is not accessible"
  echo ""
  echo "Configure kubectl:"
  echo "  Minikube: minikube start"
  echo "  OKE: oci ce cluster create-kubeconfig --cluster-id <cluster-ocid>"
  echo "  AKS: az aks get-credentials --resource-group <rg> --name <cluster>"
  echo "  GKE: gcloud container clusters get-credentials <cluster> --zone <zone>"
  exit 1
fi

print_success "kubectl is configured"

# Add Prometheus Helm repository
print_info "Adding Prometheus Helm repository..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
print_success "Helm repository added"

# Create namespace if it doesn't exist
print_info "Creating namespace: $NAMESPACE"
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
print_success "Namespace ready"

# Deploy kube-prometheus-stack
print_info "Deploying kube-prometheus-stack..."
echo "This may take several minutes..."

helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace $NAMESPACE \
  --values $VALUES_FILE \
  --wait \
  --timeout 10m

print_success "kube-prometheus-stack deployed"

# Apply custom resources (ServiceMonitor, Dashboards)
print_info "Applying custom resources..."

# Apply ServiceMonitor for Dapr metrics
if [ -f "helm/monitoring/templates/servicemonitor-dapr.yaml" ]; then
  kubectl apply -f helm/monitoring/templates/servicemonitor-dapr.yaml -n $NAMESPACE
  print_success "ServiceMonitor for Dapr applied"
fi

# Apply Grafana dashboards
if [ -d "helm/monitoring/templates/dashboards" ]; then
  for dashboard in helm/monitoring/templates/dashboards/*.yaml; do
    if [ -f "$dashboard" ]; then
      kubectl apply -f "$dashboard" -n $NAMESPACE
      print_success "Dashboard applied: $(basename $dashboard)"
    fi
  done
fi

# Wait for pods to be ready
print_info "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n $NAMESPACE --timeout=300s || true
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana -n $NAMESPACE --timeout=300s || true

# Get Grafana admin password
print_info "Retrieving Grafana admin password..."
GRAFANA_PASSWORD=$(kubectl get secret -n $NAMESPACE kube-prometheus-stack-grafana -o jsonpath="{.data.admin-password}" | base64 --decode)

echo ""
echo "========================================="
print_success "Monitoring stack deployed successfully!"
echo "========================================="
echo ""
echo "Access Grafana dashboard:"
if [ "$ENVIRONMENT" = "minikube" ]; then
  echo "  kubectl port-forward -n $NAMESPACE svc/kube-prometheus-stack-grafana 3000:80"
  echo "  Open: http://localhost:3000"
else
  echo "  Ingress URL: https://grafana.todoapp.example.com (configure DNS)"
  echo "  Or port-forward: kubectl port-forward -n $NAMESPACE svc/kube-prometheus-stack-grafana 3000:80"
fi
echo ""
echo "Grafana credentials:"
echo "  Username: admin"
echo "  Password: $GRAFANA_PASSWORD"
echo ""
echo "Access Prometheus:"
echo "  kubectl port-forward -n $NAMESPACE svc/kube-prometheus-stack-prometheus 9090:9090"
echo "  Open: http://localhost:9090"
echo ""
echo "Verify metrics collection:"
echo "  kubectl port-forward -n $NAMESPACE svc/kube-prometheus-stack-prometheus 9090:9090"
echo "  Open: http://localhost:9090/targets"
echo "  Check that all service targets are 'UP'"
echo ""
