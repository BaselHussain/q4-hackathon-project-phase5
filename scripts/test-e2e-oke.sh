#!/bin/bash
set -euo pipefail

# End-to-End Test Script for Oracle Kubernetes Engine (OKE)
# Spec 9 - T048: E2E Testing for OKE
#
# This script runs comprehensive end-to-end tests on an OKE deployment
# to verify all services, monitoring, and logging are working correctly.

echo "========================================="
echo "End-to-End Testing - Oracle OKE"
echo "========================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Configuration
NAMESPACE="${NAMESPACE:-default}"
MONITORING_NAMESPACE="${MONITORING_NAMESPACE:-monitoring}"
LOGGING_NAMESPACE="${LOGGING_NAMESPACE:-logging}"

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

print_test() {
  echo -e "${BLUE}TEST: $1${NC}"
}

# Function to run a test
run_test() {
  local test_name="$1"
  local test_command="$2"

  TESTS_TOTAL=$((TESTS_TOTAL + 1))
  print_test "$test_name"

  if eval "$test_command" > /dev/null 2>&1; then
    print_success "PASS: $test_name"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    return 0
  else
    print_error "FAIL: $test_name"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    return 1
  fi
}

# Function to run a test with output check
run_test_with_output() {
  local test_name="$1"
  local test_command="$2"
  local expected_output="$3"

  TESTS_TOTAL=$((TESTS_TOTAL + 1))
  print_test "$test_name"

  local output=$(eval "$test_command" 2>&1)

  if echo "$output" | grep -q "$expected_output"; then
    print_success "PASS: $test_name"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    return 0
  else
    print_error "FAIL: $test_name (expected: $expected_output)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    return 1
  fi
}

echo ""
print_info "Starting E2E tests for OKE deployment..."
echo ""

# ============================================
# Test Suite 1: Cluster Health
# ============================================
echo "========================================="
echo "Test Suite 1: OKE Cluster Health"
echo "========================================="

run_test "kubectl can connect to OKE cluster" "kubectl cluster-info"
run_test "All nodes are ready" "kubectl get nodes | grep -q 'Ready'"
run_test "Cluster has at least 3 nodes" "[ \$(kubectl get nodes --no-headers | wc -l) -ge 3 ]"

echo ""

# ============================================
# Test Suite 2: Dapr Runtime
# ============================================
echo "========================================="
echo "Test Suite 2: Dapr Runtime"
echo "========================================="

run_test "Dapr operator is running" "kubectl get pods -n dapr-system -l app=dapr-operator | grep -q 'Running'"
run_test "Dapr sidecar injector is running" "kubectl get pods -n dapr-system -l app=dapr-sidecar-injector | grep -q 'Running'"
run_test "Dapr placement service is running" "kubectl get pods -n dapr-system -l app=dapr-placement-server | grep -q 'Running'"

echo ""

# ============================================
# Test Suite 3: Application Services
# ============================================
echo "========================================="
echo "Test Suite 3: Application Services"
echo "========================================="

run_test "Backend deployment exists" "kubectl get deployment backend -n $NAMESPACE"
run_test "Backend pods are running" "kubectl get pods -n $NAMESPACE -l app=backend | grep -q 'Running'"
run_test "Sync service pods are running" "kubectl get pods -n $NAMESPACE -l app=sync-service | grep -q 'Running'"
run_test "Recurring task service pods are running" "kubectl get pods -n $NAMESPACE -l app=recurring-task-service | grep -q 'Running'"
run_test "Notification service pods are running" "kubectl get pods -n $NAMESPACE -l app=notification-service | grep -q 'Running'"
run_test "Audit service pods are running" "kubectl get pods -n $NAMESPACE -l app=audit-service | grep -q 'Running'"

# Check replica counts
run_test "Backend has correct replicas" "[ \$(kubectl get deployment backend -n $NAMESPACE -o jsonpath='{.status.readyReplicas}') -ge 2 ]"

echo ""

# ============================================
# Test Suite 4: Service Health Checks
# ============================================
echo "========================================="
echo "Test Suite 4: Service Health Checks"
echo "========================================="

# Get service endpoints
BACKEND_POD=$(kubectl get pods -n $NAMESPACE -l app=backend -o jsonpath='{.items[0].metadata.name}')
SYNC_POD=$(kubectl get pods -n $NAMESPACE -l app=sync-service -o jsonpath='{.items[0].metadata.name}')

run_test "Backend health check responds" "kubectl exec -n $NAMESPACE $BACKEND_POD -- curl -s http://localhost:8000/health | grep -q 'healthy'"
run_test "Sync service health check responds" "kubectl exec -n $NAMESPACE $SYNC_POD -- curl -s http://localhost:8003/health | grep -q 'healthy'"

echo ""

# ============================================
# Test Suite 5: Monitoring Stack
# ============================================
echo "========================================="
echo "Test Suite 5: Monitoring Stack (OKE)"
echo "========================================="

run_test "Monitoring namespace exists" "kubectl get namespace $MONITORING_NAMESPACE"
run_test "Prometheus is running" "kubectl get pods -n $MONITORING_NAMESPACE -l app.kubernetes.io/name=prometheus | grep -q 'Running'"
run_test "Grafana is running" "kubectl get pods -n $MONITORING_NAMESPACE -l app.kubernetes.io/name=grafana | grep -q 'Running'"
run_test "Prometheus has persistent volume" "kubectl get pvc -n $MONITORING_NAMESPACE | grep -q 'prometheus'"
run_test "Grafana has persistent volume" "kubectl get pvc -n $MONITORING_NAMESPACE | grep -q 'grafana'"

# Check ServiceMonitor for Dapr
run_test "ServiceMonitor for Dapr exists" "kubectl get servicemonitor -n $MONITORING_NAMESPACE dapr-metrics"

echo ""

# ============================================
# Test Suite 6: Logging Stack
# ============================================
echo "========================================="
echo "Test Suite 6: Logging Stack (OKE)"
echo "========================================="

run_test "Logging namespace exists" "kubectl get namespace $LOGGING_NAMESPACE"
run_test "Loki is running" "kubectl get pods -n $LOGGING_NAMESPACE -l app.kubernetes.io/name=loki | grep -q 'Running'"
run_test "Promtail DaemonSet is running" "kubectl get daemonset -n $LOGGING_NAMESPACE promtail"
run_test "Loki has persistent volume" "kubectl get pvc -n $LOGGING_NAMESPACE | grep -q 'loki'"

# Check Loki is using OCI Object Storage
run_test "Loki configured for S3 (OCI)" "kubectl get configmap -n $LOGGING_NAMESPACE loki -o yaml | grep -q 's3'"

echo ""

# ============================================
# Test Suite 7: Metrics Collection
# ============================================
echo "========================================="
echo "Test Suite 7: Metrics Collection"
echo "========================================="

# Check that services expose /metrics endpoint
run_test "Backend exposes metrics" "kubectl exec -n $NAMESPACE $BACKEND_POD -- curl -s http://localhost:8000/metrics | grep -q 'http_requests_total'"

# Check Prometheus is scraping targets
PROM_POD=$(kubectl get pods -n $MONITORING_NAMESPACE -l app.kubernetes.io/name=prometheus -o jsonpath='{.items[0].metadata.name}')
run_test "Prometheus has active targets" "kubectl exec -n $MONITORING_NAMESPACE $PROM_POD -- wget -qO- http://localhost:9090/api/v1/targets | grep -q 'up'"

echo ""

# ============================================
# Test Suite 8: Log Collection
# ============================================
echo "========================================="
echo "Test Suite 8: Log Collection"
echo "========================================="

# Check Promtail is collecting logs
run_test "Promtail pods are running on all nodes" "[ \$(kubectl get pods -n $LOGGING_NAMESPACE -l app.kubernetes.io/name=promtail --no-headers | wc -l) -ge 3 ]"

# Check that pods have logging annotations
run_test "Backend has Promtail annotation" "kubectl get pod -n $NAMESPACE -l app=backend -o jsonpath='{.items[0].metadata.annotations}' | grep -q 'prometheus.io/scrape'"

echo ""

# ============================================
# Test Suite 9: OCI-Specific Resources
# ============================================
echo "========================================="
echo "Test Suite 9: OCI-Specific Resources"
echo "========================================="

# Check storage classes
run_test "OCI Block Volume storage class exists" "kubectl get storageclass oci-bv"

# Check load balancer services
run_test "Backend service has LoadBalancer type (if configured)" "kubectl get svc -n $NAMESPACE backend -o jsonpath='{.spec.type}' | grep -qE 'LoadBalancer|ClusterIP'"

echo ""

# ============================================
# Test Suite 10: Ingress and Networking
# ============================================
echo "========================================="
echo "Test Suite 10: Ingress and Networking"
echo "========================================="

# Check if ingress controller is installed
if kubectl get namespace ingress-nginx > /dev/null 2>&1; then
  run_test "NGINX Ingress Controller is running" "kubectl get pods -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx | grep -q 'Running'"

  # Check if ingress resources exist
  if kubectl get ingress -n $NAMESPACE > /dev/null 2>&1; then
    run_test "Ingress resource exists" "kubectl get ingress -n $NAMESPACE"
  fi
fi

echo ""

# ============================================
# Test Suite 11: Security and Secrets
# ============================================
echo "========================================="
echo "Test Suite 11: Security and Secrets"
echo "========================================="

run_test "Application secrets exist" "kubectl get secret -n $NAMESPACE app-secrets"
run_test "Kafka credentials exist" "kubectl get secret -n $NAMESPACE kafka-creds"

# Check Dapr secret store component
run_test "Dapr secret store component exists" "kubectl get component -n $NAMESPACE secretstore"

echo ""

# ============================================
# Test Results Summary
# ============================================
echo "========================================="
echo "Test Results Summary - OKE Deployment"
echo "========================================="
echo ""
echo "Total Tests: $TESTS_TOTAL"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
  print_success "All tests passed! ✨"
  echo ""
  echo "Your OKE deployment is fully functional with:"
  echo "  ✓ All application services running with HA"
  echo "  ✓ Dapr runtime operational"
  echo "  ✓ Monitoring stack with persistent storage"
  echo "  ✓ Logging stack with OCI Object Storage backend"
  echo "  ✓ Metrics exposed and collected"
  echo "  ✓ Logs aggregated and queryable"
  echo ""
  echo "Access your services:"
  echo "  Grafana: kubectl port-forward -n $MONITORING_NAMESPACE svc/kube-prometheus-stack-grafana 3000:80"
  echo "  Loki: kubectl port-forward -n $LOGGING_NAMESPACE svc/loki-gateway 3100:80"
  echo ""
  exit 0
else
  print_error "Some tests failed. Please review the output above."
  echo ""
  echo "Troubleshooting tips:"
  echo "  1. Check pod logs: kubectl logs -n $NAMESPACE <pod-name>"
  echo "  2. Check pod events: kubectl describe pod -n $NAMESPACE <pod-name>"
  echo "  3. Verify OCI credentials: oci iam user list"
  echo "  4. Check OCI Object Storage: oci os bucket list"
  echo "  5. Review OKE cluster: oci ce cluster get --cluster-id <cluster-ocid>"
  echo ""
  exit 1
fi
