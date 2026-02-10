#!/bin/bash
set -euo pipefail

# End-to-End Test Script for Minikube
# Spec 9 - T047: E2E Testing Automation
#
# This script runs comprehensive end-to-end tests on a Minikube deployment
# to verify all services, monitoring, and logging are working correctly.

echo "========================================="
echo "End-to-End Testing - Minikube"
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
    print_error "FAIL: $test_name (expected: $expected_output, got: $output)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    return 1
  fi
}

echo ""
print_info "Starting E2E tests..."
echo ""

# ============================================
# Test Suite 1: Cluster Health
# ============================================
echo "========================================="
echo "Test Suite 1: Cluster Health"
echo "========================================="

run_test "Minikube is running" "minikube status | grep -q 'Running'"
run_test "kubectl can connect to cluster" "kubectl cluster-info"
run_test "All nodes are ready" "kubectl get nodes | grep -q 'Ready'"

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

run_test "Backend pod is running" "kubectl get pods -l app=backend | grep -q 'Running'"
run_test "Sync service pod is running" "kubectl get pods -l app=sync-service | grep -q 'Running'"
run_test "Recurring task service pod is running" "kubectl get pods -l app=recurring-task-service | grep -q 'Running'"
run_test "Notification service pod is running" "kubectl get pods -l app=notification-service | grep -q 'Running'"
run_test "Audit service pod is running" "kubectl get pods -l app=audit-service | grep -q 'Running'"

# Check Dapr sidecars
run_test "Backend has Dapr sidecar" "kubectl get pods -l app=backend -o jsonpath='{.items[0].spec.containers[*].name}' | grep -q 'daprd'"
run_test "Sync service has Dapr sidecar" "kubectl get pods -l app=sync-service -o jsonpath='{.items[0].spec.containers[*].name}' | grep -q 'daprd'"

echo ""

# ============================================
# Test Suite 4: Service Health Checks
# ============================================
echo "========================================="
echo "Test Suite 4: Service Health Checks"
echo "========================================="

# Port-forward and test health endpoints
print_info "Testing backend health endpoint..."
kubectl port-forward svc/backend 8000:8000 > /dev/null 2>&1 &
PF_PID=$!
sleep 3
run_test_with_output "Backend health check" "curl -s http://localhost:8000/health" "healthy"
kill $PF_PID 2>/dev/null || true

print_info "Testing sync service health endpoint..."
kubectl port-forward svc/sync-service 8003:8003 > /dev/null 2>&1 &
PF_PID=$!
sleep 3
run_test_with_output "Sync service health check" "curl -s http://localhost:8003/health" "healthy"
kill $PF_PID 2>/dev/null || true

echo ""

# ============================================
# Test Suite 5: Monitoring Stack
# ============================================
echo "========================================="
echo "Test Suite 5: Monitoring Stack"
echo "========================================="

run_test "Monitoring namespace exists" "kubectl get namespace monitoring"
run_test "Prometheus is running" "kubectl get pods -n monitoring -l app.kubernetes.io/name=prometheus | grep -q 'Running'"
run_test "Grafana is running" "kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana | grep -q 'Running'"

# Test Prometheus metrics
print_info "Testing Prometheus metrics endpoint..."
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090 > /dev/null 2>&1 &
PF_PID=$!
sleep 3
run_test "Prometheus is accessible" "curl -s http://localhost:9090/-/healthy | grep -q 'Prometheus'"
kill $PF_PID 2>/dev/null || true

# Test Grafana
print_info "Testing Grafana endpoint..."
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80 > /dev/null 2>&1 &
PF_PID=$!
sleep 3
run_test "Grafana is accessible" "curl -s http://localhost:3000/api/health | grep -q 'ok'"
kill $PF_PID 2>/dev/null || true

echo ""

# ============================================
# Test Suite 6: Logging Stack
# ============================================
echo "========================================="
echo "Test Suite 6: Logging Stack"
echo "========================================="

run_test "Logging namespace exists" "kubectl get namespace logging"
run_test "Loki is running" "kubectl get pods -n logging -l app.kubernetes.io/name=loki | grep -q 'Running'"
run_test "Promtail is running" "kubectl get pods -n logging -l app.kubernetes.io/name=promtail | grep -q 'Running'"

# Test Loki
print_info "Testing Loki endpoint..."
kubectl port-forward -n logging svc/loki-gateway 3100:80 > /dev/null 2>&1 &
PF_PID=$!
sleep 3
run_test "Loki is accessible" "curl -s http://localhost:3100/ready | grep -q 'ready'"
kill $PF_PID 2>/dev/null || true

echo ""

# ============================================
# Test Suite 7: Metrics Collection
# ============================================
echo "========================================="
echo "Test Suite 7: Metrics Collection"
echo "========================================="

# Test that services expose /metrics endpoint
print_info "Testing backend metrics endpoint..."
kubectl port-forward svc/backend 8000:8000 > /dev/null 2>&1 &
PF_PID=$!
sleep 3
run_test "Backend exposes metrics" "curl -s http://localhost:8000/metrics | grep -q 'http_requests_total'"
kill $PF_PID 2>/dev/null || true

echo ""

# ============================================
# Test Suite 8: Log Collection
# ============================================
echo "========================================="
echo "Test Suite 8: Log Collection"
echo "========================================="

# Check that Promtail is scraping logs
run_test "Promtail has targets" "kubectl logs -n logging -l app.kubernetes.io/name=promtail --tail=50 | grep -q 'target'"

# Check that pods have logging annotations
run_test "Backend has Promtail annotation" "kubectl get pod -l app=backend -o jsonpath='{.items[0].metadata.annotations}' | grep -q 'prometheus.io/scrape'"

echo ""

# ============================================
# Test Suite 9: Dapr Components
# ============================================
echo "========================================="
echo "Test Suite 9: Dapr Components"
echo "========================================="

run_test "Pub/Sub component exists" "kubectl get component pubsub"
run_test "State store component exists" "kubectl get component statestore"
run_test "Secret store component exists" "kubectl get component secretstore"

echo ""

# ============================================
# Test Suite 10: Kubernetes Resources
# ============================================
echo "========================================="
echo "Test Suite 10: Kubernetes Resources"
echo "========================================="

run_test "Backend service exists" "kubectl get svc backend"
run_test "Sync service exists" "kubectl get svc sync-service"
run_test "Backend deployment has correct replicas" "kubectl get deployment backend -o jsonpath='{.status.readyReplicas}' | grep -q '1'"

echo ""

# ============================================
# Test Results Summary
# ============================================
echo "========================================="
echo "Test Results Summary"
echo "========================================="
echo ""
echo "Total Tests: $TESTS_TOTAL"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
  print_success "All tests passed! ✨"
  echo ""
  echo "Your Minikube deployment is fully functional with:"
  echo "  ✓ All application services running"
  echo "  ✓ Dapr runtime operational"
  echo "  ✓ Monitoring stack (Prometheus + Grafana) active"
  echo "  ✓ Logging stack (Loki + Promtail) collecting logs"
  echo "  ✓ Metrics exposed and collected"
  echo ""
  exit 0
else
  print_error "Some tests failed. Please review the output above."
  echo ""
  echo "Troubleshooting tips:"
  echo "  1. Check pod logs: kubectl logs <pod-name>"
  echo "  2. Check pod events: kubectl describe pod <pod-name>"
  echo "  3. Verify Dapr components: kubectl get components"
  echo "  4. Check Dapr sidecar logs: kubectl logs <pod-name> -c daprd"
  echo ""
  exit 1
fi
