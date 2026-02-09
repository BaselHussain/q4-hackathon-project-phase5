---
name: minikube-setup-script
description: Generate bash scripts to bootstrap a local Minikube Kubernetes cluster with Dapr, Strimzi/Redpanda Kafka, common components, and health verification for local development and CI testing.
version: 1.0.0
---

# Minikube Setup Script Generator Skill

## When to Use This Skill

Use this skill when you need to:
- Bootstrap a local Kubernetes development environment from scratch
- Set up Minikube with Dapr sidecar injection for microservices
- Install Strimzi Kafka operator or Redpanda for event-driven architectures
- Create reproducible local environments matching CI/CD pipelines
- Onboard new developers with a single-command cluster setup
- Verify all infrastructure components are healthy before running services

## How This Skill Works

1. **Gather Environment Requirements**
   - Minikube driver preference (docker, hyperv, virtualbox)
   - Kubernetes version target
   - Kafka flavor (Strimzi operator or Redpanda)
   - Dapr version and components needed
   - Resource allocation (CPUs, memory, disk)

2. **Generate Setup Script**
   - Create `scripts/minikube-setup.sh` with all bootstrap steps
   - Idempotent design — safe to re-run without breaking state
   - Color-coded output with progress indicators
   - Error handling with early exit on failures

3. **Apply Best Practices**
   - Pre-flight checks for required CLI tools
   - Wait loops with timeouts for operator readiness
   - Namespace isolation for infrastructure components
   - Cleanup/teardown companion script

4. **Validate and Verify**
   - Health checks for every installed component
   - Summary report of endpoints and access details
   - Troubleshooting guidance on failure

## Output Files Generated

```
scripts/
├── minikube-setup.sh           # Full bootstrap script
├── minikube-teardown.sh        # Clean teardown script
└── minikube-status.sh          # Health check / status script
```

## Instructions

### 1. Full Setup Script (scripts/minikube-setup.sh)

```bash
#!/usr/bin/env bash
#
# minikube-setup.sh — Bootstrap a local Minikube cluster with Dapr + Kafka
#
# Usage:
#   chmod +x scripts/minikube-setup.sh
#   ./scripts/minikube-setup.sh [--driver docker] [--kafka strimzi|redpanda] [--skip-kafka] [--skip-dapr]
#
# Prerequisites: minikube, kubectl, helm, dapr CLI
#
set -euo pipefail

# ─────────────────────────────────────────────
# Configuration (override via env vars)
# ─────────────────────────────────────────────
MINIKUBE_PROFILE="${MINIKUBE_PROFILE:-{{ profile }}}"           # e.g. dev-cluster
MINIKUBE_DRIVER="${MINIKUBE_DRIVER:-docker}"
MINIKUBE_CPUS="${MINIKUBE_CPUS:-4}"
MINIKUBE_MEMORY="${MINIKUBE_MEMORY:-8192}"
MINIKUBE_DISK="${MINIKUBE_DISK:-40g}"
KUBE_VERSION="${KUBE_VERSION:-v1.30.0}"
DAPR_VERSION="${DAPR_VERSION:-1.14}"
KAFKA_FLAVOR="${KAFKA_FLAVOR:-strimzi}"                        # strimzi | redpanda
STRIMZI_VERSION="${STRIMZI_VERSION:-0.43.0}"
REDPANDA_CHART_VERSION="${REDPANDA_CHART_VERSION:-5.9.4}"
NAMESPACE_INFRA="${NAMESPACE_INFRA:-infra}"
NAMESPACE_KAFKA="${NAMESPACE_KAFKA:-kafka}"
NAMESPACE_DAPR="${NAMESPACE_DAPR:-dapr-system}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-300s}"

SKIP_KAFKA=false
SKIP_DAPR=false

# ─────────────────────────────────────────────
# Color helpers
# ─────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }
step()    { echo -e "\n${GREEN}━━━ $* ━━━${NC}"; }

# ─────────────────────────────────────────────
# Parse arguments
# ─────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case $1 in
    --driver)      MINIKUBE_DRIVER="$2"; shift 2 ;;
    --kafka)       KAFKA_FLAVOR="$2";    shift 2 ;;
    --skip-kafka)  SKIP_KAFKA=true;      shift ;;
    --skip-dapr)   SKIP_DAPR=true;       shift ;;
    --cpus)        MINIKUBE_CPUS="$2";   shift 2 ;;
    --memory)      MINIKUBE_MEMORY="$2"; shift 2 ;;
    --profile)     MINIKUBE_PROFILE="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--driver docker|hyperv|virtualbox] [--kafka strimzi|redpanda] [--skip-kafka] [--skip-dapr] [--cpus N] [--memory MB] [--profile NAME]"
      exit 0 ;;
    *) error "Unknown option: $1"; exit 1 ;;
  esac
done

# ─────────────────────────────────────────────
# Pre-flight checks
# ─────────────────────────────────────────────
step "Pre-flight Checks"

REQUIRED_TOOLS=(minikube kubectl helm)
[[ "$SKIP_DAPR" == false ]] && REQUIRED_TOOLS+=(dapr)

MISSING=()
for tool in "${REQUIRED_TOOLS[@]}"; do
  if ! command -v "$tool" &>/dev/null; then
    MISSING+=("$tool")
  else
    success "$tool found: $(command -v "$tool")"
  fi
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
  error "Missing required tools: ${MISSING[*]}"
  echo ""
  echo "Install them:"
  echo "  minikube : https://minikube.sigs.k8s.io/docs/start/"
  echo "  kubectl  : https://kubernetes.io/docs/tasks/tools/"
  echo "  helm     : https://helm.sh/docs/intro/install/"
  echo "  dapr     : https://docs.dapr.io/getting-started/install-dapr-cli/"
  exit 1
fi

# ─────────────────────────────────────────────
# Step 1: Start Minikube
# ─────────────────────────────────────────────
step "Step 1/5 — Starting Minikube"

if minikube status -p "$MINIKUBE_PROFILE" &>/dev/null; then
  warn "Minikube profile '$MINIKUBE_PROFILE' already running — skipping start"
else
  info "Starting Minikube (profile=$MINIKUBE_PROFILE, driver=$MINIKUBE_DRIVER, cpus=$MINIKUBE_CPUS, memory=${MINIKUBE_MEMORY}MB)"
  minikube start \
    --profile="$MINIKUBE_PROFILE" \
    --driver="$MINIKUBE_DRIVER" \
    --cpus="$MINIKUBE_CPUS" \
    --memory="$MINIKUBE_MEMORY" \
    --disk-size="$MINIKUBE_DISK" \
    --kubernetes-version="$KUBE_VERSION" \
    --addons=metrics-server,dashboard,ingress \
    --embed-certs=true
  success "Minikube started"
fi

# Point kubectl to the profile
minikube profile "$MINIKUBE_PROFILE"
kubectl config use-context "$MINIKUBE_PROFILE"
success "kubectl context set to $MINIKUBE_PROFILE"

# Create namespaces
for NS in "$NAMESPACE_INFRA" "$NAMESPACE_KAFKA"; do
  kubectl create namespace "$NS" --dry-run=client -o yaml | kubectl apply -f -
done
success "Namespaces ready"

# ─────────────────────────────────────────────
# Step 2: Install Dapr
# ─────────────────────────────────────────────
step "Step 2/5 — Installing Dapr"

if [[ "$SKIP_DAPR" == true ]]; then
  warn "Skipping Dapr installation (--skip-dapr)"
else
  if kubectl get namespace "$NAMESPACE_DAPR" &>/dev/null && kubectl get pods -n "$NAMESPACE_DAPR" -l app=dapr-operator --no-headers 2>/dev/null | grep -q Running; then
    warn "Dapr already installed — skipping"
  else
    info "Initializing Dapr ${DAPR_VERSION} on Kubernetes..."
    dapr init --kubernetes \
      --runtime-version "$DAPR_VERSION" \
      --wait --timeout 300

    info "Waiting for Dapr system pods..."
    kubectl wait --for=condition=ready pod \
      --all -n "$NAMESPACE_DAPR" \
      --timeout="$WAIT_TIMEOUT"
    success "Dapr installed and healthy"
  fi

  # Apply Dapr components (if directory exists)
  if [[ -d "k8s/dapr-components" ]]; then
    info "Applying Dapr components from k8s/dapr-components/"
    kubectl apply -f k8s/dapr-components/ -n "$NAMESPACE_INFRA"
    success "Dapr components applied"
  else
    warn "No k8s/dapr-components/ directory found — skipping component apply"
  fi
fi

# ─────────────────────────────────────────────
# Step 3: Install Kafka (Strimzi or Redpanda)
# ─────────────────────────────────────────────
step "Step 3/5 — Installing Kafka ($KAFKA_FLAVOR)"

if [[ "$SKIP_KAFKA" == true ]]; then
  warn "Skipping Kafka installation (--skip-kafka)"

elif [[ "$KAFKA_FLAVOR" == "strimzi" ]]; then
  # ── Strimzi Kafka Operator ──
  if kubectl get pods -n "$NAMESPACE_KAFKA" -l strimzi.io/kind=Kafka --no-headers 2>/dev/null | grep -q Running; then
    warn "Strimzi Kafka already running — skipping"
  else
    info "Installing Strimzi operator v${STRIMZI_VERSION}..."
    kubectl apply -f "https://strimzi.io/install/latest?namespace=${NAMESPACE_KAFKA}" -n "$NAMESPACE_KAFKA"

    info "Waiting for Strimzi operator pod..."
    kubectl wait --for=condition=ready pod \
      -l name=strimzi-cluster-operator \
      -n "$NAMESPACE_KAFKA" \
      --timeout="$WAIT_TIMEOUT"
    success "Strimzi operator ready"

    info "Creating single-node Kafka cluster for development..."
    cat <<'KAFKA_EOF' | kubectl apply -n "$NAMESPACE_KAFKA" -f -
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: dev-kafka
spec:
  kafka:
    version: 3.7.0
    replicas: 1
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
      - name: external
        port: 9094
        type: nodeport
        tls: false
    config:
      offsets.topic.replication.factor: 1
      transaction.state.log.replication.factor: 1
      transaction.state.log.min.isr: 1
      default.replication.factor: 1
      min.insync.replicas: 1
      auto.create.topics.enable: "true"
    storage:
      type: jbod
      volumes:
        - id: 0
          type: persistent-claim
          size: 10Gi
          deleteClaim: true
    resources:
      requests:
        memory: 1Gi
        cpu: 500m
      limits:
        memory: 2Gi
        cpu: "1"
  zookeeper:
    replicas: 1
    storage:
      type: persistent-claim
      size: 5Gi
      deleteClaim: true
    resources:
      requests:
        memory: 512Mi
        cpu: 250m
      limits:
        memory: 1Gi
        cpu: 500m
  entityOperator:
    topicOperator: {}
    userOperator: {}
KAFKA_EOF

    info "Waiting for Kafka cluster to be ready (this may take 2-3 minutes)..."
    kubectl wait kafka/dev-kafka \
      --for=condition=Ready \
      -n "$NAMESPACE_KAFKA" \
      --timeout=600s
    success "Strimzi Kafka cluster ready"
  fi

elif [[ "$KAFKA_FLAVOR" == "redpanda" ]]; then
  # ── Redpanda ──
  if kubectl get pods -n "$NAMESPACE_KAFKA" -l app.kubernetes.io/name=redpanda --no-headers 2>/dev/null | grep -q Running; then
    warn "Redpanda already running — skipping"
  else
    info "Adding Redpanda Helm repo..."
    helm repo add redpanda https://charts.redpanda.com
    helm repo update

    info "Installing Redpanda v${REDPANDA_CHART_VERSION}..."
    helm upgrade --install redpanda redpanda/redpanda \
      --namespace "$NAMESPACE_KAFKA" \
      --version "$REDPANDA_CHART_VERSION" \
      --set statefulset.replicas=1 \
      --set resources.cpu.cores=1 \
      --set resources.memory.container.max=2Gi \
      --set storage.persistentVolume.size=10Gi \
      --set tls.enabled=false \
      --set external.enabled=false \
      --set monitoring.enabled=false \
      --set console.enabled=true \
      --wait --timeout=600s

    info "Waiting for Redpanda pods..."
    kubectl wait --for=condition=ready pod \
      -l app.kubernetes.io/name=redpanda \
      -n "$NAMESPACE_KAFKA" \
      --timeout="$WAIT_TIMEOUT"
    success "Redpanda cluster ready"
  fi

else
  error "Unknown KAFKA_FLAVOR: $KAFKA_FLAVOR (expected: strimzi | redpanda)"
  exit 1
fi

# Apply Kafka topics (if directory exists)
if [[ "$SKIP_KAFKA" == false ]] && [[ -d "k8s/kafka-topics" ]]; then
  info "Applying Kafka topics from k8s/kafka-topics/"
  kubectl apply -f k8s/kafka-topics/ -n "$NAMESPACE_KAFKA"
  success "Kafka topics applied"
fi

# ─────────────────────────────────────────────
# Step 4: Apply Common Components
# ─────────────────────────────────────────────
step "Step 4/5 — Applying Common Components"

COMMON_DIRS=("k8s/configmaps" "k8s/secrets" "k8s/common")
APPLIED=0

for DIR in "${COMMON_DIRS[@]}"; do
  if [[ -d "$DIR" ]]; then
    info "Applying manifests from $DIR/"
    kubectl apply -f "$DIR/" -n "$NAMESPACE_INFRA"
    APPLIED=$((APPLIED + 1))
  fi
done

if [[ $APPLIED -eq 0 ]]; then
  warn "No common component directories found (checked: ${COMMON_DIRS[*]})"
  info "Create k8s/common/, k8s/configmaps/, or k8s/secrets/ to auto-apply manifests"
else
  success "$APPLIED common component directories applied"
fi

# ─────────────────────────────────────────────
# Step 5: Verify Everything
# ─────────────────────────────────────────────
step "Step 5/5 — Verification"

ERRORS=0

# Minikube
if minikube status -p "$MINIKUBE_PROFILE" &>/dev/null; then
  success "Minikube cluster is running"
else
  error "Minikube cluster is NOT running"
  ERRORS=$((ERRORS + 1))
fi

# Dapr
if [[ "$SKIP_DAPR" == false ]]; then
  DAPR_PODS=$(kubectl get pods -n "$NAMESPACE_DAPR" --no-headers 2>/dev/null | grep -c Running || true)
  if [[ "$DAPR_PODS" -ge 3 ]]; then
    success "Dapr system pods running ($DAPR_PODS pods)"
  else
    error "Dapr system pods: expected >= 3 Running, found $DAPR_PODS"
    ERRORS=$((ERRORS + 1))
  fi
fi

# Kafka
if [[ "$SKIP_KAFKA" == false ]]; then
  if [[ "$KAFKA_FLAVOR" == "strimzi" ]]; then
    if kubectl get kafka dev-kafka -n "$NAMESPACE_KAFKA" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null | grep -q True; then
      BOOTSTRAP=$(kubectl get kafka dev-kafka -n "$NAMESPACE_KAFKA" -o jsonpath='{.status.listeners[?(@.name=="plain")].bootstrapServers}' 2>/dev/null)
      success "Strimzi Kafka ready (bootstrap: $BOOTSTRAP)"
    else
      error "Strimzi Kafka cluster is NOT ready"
      ERRORS=$((ERRORS + 1))
    fi
  elif [[ "$KAFKA_FLAVOR" == "redpanda" ]]; then
    RP_PODS=$(kubectl get pods -n "$NAMESPACE_KAFKA" -l app.kubernetes.io/name=redpanda --no-headers 2>/dev/null | grep -c Running || true)
    if [[ "$RP_PODS" -ge 1 ]]; then
      success "Redpanda running ($RP_PODS pods)"
    else
      error "Redpanda is NOT running"
      ERRORS=$((ERRORS + 1))
    fi
  fi
fi

# Kubernetes system health
SYSTEM_PODS=$(kubectl get pods -n kube-system --no-headers 2>/dev/null | grep -c Running || true)
success "kube-system pods running ($SYSTEM_PODS pods)"

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
echo ""
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Minikube Environment Setup Complete${NC}"
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo ""
echo "  Profile:      $MINIKUBE_PROFILE"
echo "  Driver:       $MINIKUBE_DRIVER"
echo "  Kubernetes:   $KUBE_VERSION"
echo "  Resources:    ${MINIKUBE_CPUS} CPUs / ${MINIKUBE_MEMORY}MB RAM / ${MINIKUBE_DISK} disk"
echo ""
[[ "$SKIP_DAPR" == false ]]  && echo "  Dapr:         v${DAPR_VERSION} (namespace: $NAMESPACE_DAPR)"
[[ "$SKIP_KAFKA" == false ]] && echo "  Kafka:        $KAFKA_FLAVOR (namespace: $NAMESPACE_KAFKA)"
echo ""
echo "  Dashboard:    minikube dashboard -p $MINIKUBE_PROFILE"
[[ "$SKIP_DAPR" == false ]]  && echo "  Dapr:         dapr dashboard -k"
echo ""

if [[ $ERRORS -gt 0 ]]; then
  error "$ERRORS component(s) failed verification — check output above"
  exit 1
else
  success "All components healthy"
fi
```

### 2. Teardown Script (scripts/minikube-teardown.sh)

```bash
#!/usr/bin/env bash
#
# minikube-teardown.sh — Clean teardown of the local Minikube cluster
#
# Usage:
#   ./scripts/minikube-teardown.sh [--profile NAME] [--keep-profile]
#
set -euo pipefail

MINIKUBE_PROFILE="${MINIKUBE_PROFILE:-{{ profile }}}"
KEEP_PROFILE=false

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()    { echo -e "\033[0;34m[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }

while [[ $# -gt 0 ]]; do
  case $1 in
    --profile)       MINIKUBE_PROFILE="$2"; shift 2 ;;
    --keep-profile)  KEEP_PROFILE=true;     shift ;;
    -h|--help)
      echo "Usage: $0 [--profile NAME] [--keep-profile]"
      exit 0 ;;
    *) shift ;;
  esac
done

echo ""
echo -e "${RED}This will destroy the Minikube cluster: $MINIKUBE_PROFILE${NC}"
read -rp "Continue? (y/N): " CONFIRM
if [[ "${CONFIRM,,}" != "y" ]]; then
  echo "Aborted."
  exit 0
fi

# Uninstall Dapr
if command -v dapr &>/dev/null; then
  info "Uninstalling Dapr from Kubernetes..."
  dapr uninstall --kubernetes --all 2>/dev/null || warn "Dapr uninstall skipped (not found)"
fi

# Stop and delete Minikube
if [[ "$KEEP_PROFILE" == true ]]; then
  info "Stopping Minikube profile '$MINIKUBE_PROFILE' (keeping profile)..."
  minikube stop -p "$MINIKUBE_PROFILE"
  success "Minikube stopped (profile preserved)"
else
  info "Deleting Minikube profile '$MINIKUBE_PROFILE'..."
  minikube delete -p "$MINIKUBE_PROFILE"
  success "Minikube profile deleted"
fi

echo ""
success "Teardown complete"
```

### 3. Status Script (scripts/minikube-status.sh)

```bash
#!/usr/bin/env bash
#
# minikube-status.sh — Health check for the local Minikube environment
#
# Usage:
#   ./scripts/minikube-status.sh [--profile NAME]
#
set -euo pipefail

MINIKUBE_PROFILE="${MINIKUBE_PROFILE:-{{ profile }}}"
NAMESPACE_DAPR="${NAMESPACE_DAPR:-dapr-system}"
NAMESPACE_KAFKA="${NAMESPACE_KAFKA:-kafka}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

while [[ $# -gt 0 ]]; do
  case $1 in
    --profile) MINIKUBE_PROFILE="$2"; shift 2 ;;
    *) shift ;;
  esac
done

header() { echo -e "\n${BLUE}── $* ──${NC}"; }
ok()     { echo -e "  ${GREEN}✓${NC} $*"; }
fail()   { echo -e "  ${RED}✗${NC} $*"; }
skip()   { echo -e "  ${YELLOW}–${NC} $*"; }

ERRORS=0

# ── Minikube ──
header "Minikube"
if minikube status -p "$MINIKUBE_PROFILE" &>/dev/null; then
  ok "Cluster running (profile: $MINIKUBE_PROFILE)"
  MINIKUBE_IP=$(minikube ip -p "$MINIKUBE_PROFILE" 2>/dev/null || echo "unknown")
  ok "IP: $MINIKUBE_IP"
else
  fail "Cluster not running"
  ERRORS=$((ERRORS + 1))
fi

# ── Kubernetes ──
header "Kubernetes"
if kubectl cluster-info &>/dev/null; then
  SERVER=$(kubectl cluster-info 2>/dev/null | head -1)
  ok "API server reachable"
  NODE_COUNT=$(kubectl get nodes --no-headers 2>/dev/null | wc -l)
  ok "Nodes: $NODE_COUNT"
  SYSTEM_PODS=$(kubectl get pods -n kube-system --no-headers 2>/dev/null | grep -c Running || true)
  ok "kube-system Running pods: $SYSTEM_PODS"
else
  fail "Cannot reach Kubernetes API"
  ERRORS=$((ERRORS + 1))
fi

# ── Dapr ──
header "Dapr"
if kubectl get namespace "$NAMESPACE_DAPR" &>/dev/null; then
  DAPR_PODS=$(kubectl get pods -n "$NAMESPACE_DAPR" --no-headers 2>/dev/null)
  RUNNING=$(echo "$DAPR_PODS" | grep -c Running || true)
  TOTAL=$(echo "$DAPR_PODS" | wc -l)
  if [[ "$RUNNING" -ge 3 ]]; then
    ok "Dapr healthy ($RUNNING/$TOTAL pods running)"
  else
    fail "Dapr degraded ($RUNNING/$TOTAL pods running)"
    ERRORS=$((ERRORS + 1))
  fi
  # List Dapr components
  COMPONENTS=$(kubectl get components.dapr.io --all-namespaces --no-headers 2>/dev/null | wc -l || true)
  ok "Dapr components: $COMPONENTS"
else
  skip "Dapr not installed"
fi

# ── Kafka ──
header "Kafka"
# Check Strimzi
if kubectl get kafka -n "$NAMESPACE_KAFKA" &>/dev/null 2>&1; then
  KAFKA_READY=$(kubectl get kafka -n "$NAMESPACE_KAFKA" -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "Unknown")
  if [[ "$KAFKA_READY" == "True" ]]; then
    BOOTSTRAP=$(kubectl get kafka -n "$NAMESPACE_KAFKA" -o jsonpath='{.items[0].status.listeners[?(@.name=="plain")].bootstrapServers}' 2>/dev/null)
    ok "Strimzi Kafka ready (bootstrap: $BOOTSTRAP)"
  else
    fail "Strimzi Kafka not ready (status: $KAFKA_READY)"
    ERRORS=$((ERRORS + 1))
  fi
  TOPICS=$(kubectl get kafkatopics -n "$NAMESPACE_KAFKA" --no-headers 2>/dev/null | wc -l || true)
  ok "Kafka topics: $TOPICS"
# Check Redpanda
elif kubectl get pods -n "$NAMESPACE_KAFKA" -l app.kubernetes.io/name=redpanda --no-headers 2>/dev/null | grep -q Running; then
  RP_RUNNING=$(kubectl get pods -n "$NAMESPACE_KAFKA" -l app.kubernetes.io/name=redpanda --no-headers 2>/dev/null | grep -c Running || true)
  ok "Redpanda running ($RP_RUNNING pods)"
else
  skip "Kafka not installed"
fi

# ── Ingress ──
header "Ingress"
if kubectl get pods -n ingress-nginx --no-headers 2>/dev/null | grep -q Running; then
  ok "NGINX Ingress controller running"
elif minikube addons list -p "$MINIKUBE_PROFILE" 2>/dev/null | grep -q "ingress: enabled"; then
  ok "Minikube ingress addon enabled"
else
  skip "Ingress not configured"
fi

# ── Summary ──
echo ""
if [[ $ERRORS -gt 0 ]]; then
  echo -e "${RED}Status: $ERRORS component(s) unhealthy${NC}"
  exit 1
else
  echo -e "${GREEN}Status: All components healthy${NC}"
fi
```

## Required CLI Tools

| Tool | Install | Purpose |
|------|---------|---------|
| `minikube` | https://minikube.sigs.k8s.io/docs/start/ | Local Kubernetes cluster |
| `kubectl` | https://kubernetes.io/docs/tasks/tools/ | Kubernetes CLI |
| `helm` | https://helm.sh/docs/intro/install/ | Package manager for Kubernetes |
| `dapr` | https://docs.dapr.io/getting-started/install-dapr-cli/ | Dapr sidecar runtime CLI |

## Example Usage

### Minimal Setup (Dapr + Strimzi)

```bash
./scripts/minikube-setup.sh
```

### Redpanda Instead of Strimzi

```bash
./scripts/minikube-setup.sh --kafka redpanda
```

### Skip Kafka (Dapr Only)

```bash
./scripts/minikube-setup.sh --skip-kafka
```

### Skip Dapr (Kafka Only)

```bash
./scripts/minikube-setup.sh --skip-dapr
```

### Custom Resources

```bash
./scripts/minikube-setup.sh --cpus 6 --memory 12288 --driver hyperv --profile my-project
```

### Using Environment Variables

```bash
MINIKUBE_CPUS=8 MINIKUBE_MEMORY=16384 KAFKA_FLAVOR=redpanda ./scripts/minikube-setup.sh
```

### Full Lifecycle

```bash
# Bootstrap
./scripts/minikube-setup.sh --kafka strimzi

# Check health
./scripts/minikube-status.sh

# Teardown (preserves profile)
./scripts/minikube-teardown.sh --keep-profile

# Full delete
./scripts/minikube-teardown.sh
```

## Expected Directory Structure for Auto-Apply

The setup script automatically applies manifests from these directories if they exist:

```
k8s/
├── dapr-components/        # Dapr component YAMLs (pubsub, statestore, bindings)
│   ├── pubsub.yaml
│   └── statestore.yaml
├── kafka-topics/           # Strimzi KafkaTopic CRDs
│   ├── orders-topic.yaml
│   └── events-topic.yaml
├── configmaps/             # ConfigMaps for shared config
│   └── app-config.yaml
├── secrets/                # Secrets (use sealed-secrets in production)
│   └── db-credentials.yaml
└── common/                 # Any other shared manifests
    └── network-policies.yaml
```

## Security & Best Practices Included

- **Idempotent Execution**
  - Safe to re-run; checks existing state before each step
  - Skips already-running components with warning
  - Uses `--dry-run=client | kubectl apply` for namespace creation

- **Error Handling**
  - `set -euo pipefail` for strict error mode
  - Pre-flight checks for all required CLI tools
  - Timeout-bounded wait loops (no infinite hangs)
  - Detailed error output with actionable install links

- **Resource Management**
  - Configurable CPU, memory, and disk allocation
  - Dev-appropriate Kafka sizing (single broker, minimal resources)
  - Namespace isolation (infra, kafka, dapr-system)

- **Developer Experience**
  - Color-coded output with step progress
  - CLI flags and environment variable overrides
  - Companion teardown and status scripts
  - Summary report with access commands (dashboard, Dapr UI)

- **CI Compatibility**
  - Non-interactive (no prompts in setup, only teardown confirms)
  - Exit code reflects health status
  - Works with GitHub Actions `medyagh/setup-minikube` action
  - Configurable via environment variables for CI pipelines

## Customization Examples

### Add Custom Dapr Component (Redis State Store)

Create `k8s/dapr-components/statestore.yaml`:

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
spec:
  type: state.redis
  version: v1
  metadata:
    - name: redisHost
      value: redis-master.infra.svc.cluster.local:6379
    - name: redisPassword
      secretKeyRef:
        name: redis-secret
        key: password
```

### Add Strimzi Kafka Topic

Create `k8s/kafka-topics/orders-topic.yaml`:

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: orders
  labels:
    strimzi.io/cluster: dev-kafka
spec:
  partitions: 3
  replicas: 1
  config:
    retention.ms: "86400000"
    cleanup.policy: "delete"
```

### Use in GitHub Actions CI

```yaml
  integration-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: medyagh/setup-minikube@latest
        with:
          kubernetes-version: "v1.30.0"
          cpus: 2
          memory: 4096

      - name: Bootstrap environment
        run: |
          chmod +x scripts/minikube-setup.sh
          ./scripts/minikube-setup.sh --skip-dapr --kafka strimzi

      - name: Verify
        run: ./scripts/minikube-status.sh
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Minikube fails to start | Insufficient resources | Reduce `--cpus` / `--memory` or close other VMs |
| Strimzi pods pending | PVC not provisioned | Run `minikube addons enable storage-provisioner` |
| Dapr init hangs | Network timeout pulling images | Run `minikube ssh -- docker pull daprio/dapr:$VERSION` first |
| Kafka not ready after 10min | Insufficient memory for ZooKeeper + broker | Increase `--memory` to at least 8192 |
| `kubectl` wrong context | Multiple profiles | Run `minikube profile <name>` or `kubectl config use-context <name>` |

## Final Message from Skill

Your Minikube environment is ready!

**Next Steps:**
1. Copy the scripts to your `scripts/` directory
2. Replace `{{ profile }}` with your project name
3. Run `chmod +x scripts/minikube-*.sh`
4. Bootstrap with `./scripts/minikube-setup.sh`
5. Verify with `./scripts/minikube-status.sh`

**Pro Tips:**
- Add `k8s/dapr-components/` for auto-applied Dapr components
- Add `k8s/kafka-topics/` for auto-applied Strimzi KafkaTopic CRDs
- Use `--skip-kafka` or `--skip-dapr` for lighter setups
- Use the status script in CI to gate deployments on healthy infra
- Set env vars in `.env` and source before running for team consistency
- Use `--keep-profile` on teardown to preserve the profile for faster restarts

Happy developing!
