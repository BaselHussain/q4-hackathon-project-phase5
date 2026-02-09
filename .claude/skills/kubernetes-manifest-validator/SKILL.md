---
name: kubernetes-manifest-validator
description: Review and validate Kubernetes YAML manifests for correctness, security, and best practices with actionable fix suggestions.
version: 1.0.0
---

# Kubernetes Manifest Validator Skill

## When to Use This Skill

Use this skill when you need to:
- Review Kubernetes manifests before deployment
- Validate Deployment, Service, Ingress, StatefulSet, DaemonSet, Job, CronJob manifests
- Check for security vulnerabilities and misconfigurations
- Ensure resource limits and requests are properly set
- Verify health probes are configured correctly
- Validate labels, selectors, and annotations
- Review Dapr sidecar configurations
- Get actionable recommendations for improvements
- Rate manifest quality (Excellent / Good / Needs Improvement)

## How This Skill Works

1. **Parse Manifest**
   - Identify resource type (Deployment, Service, etc.)
   - Extract key configurations
   - Check YAML syntax and structure

2. **Run Validation Checks**
   - API version and kind correctness
   - Resource requests and limits
   - Security context (non-root, capabilities, filesystem)
   - Health probes (liveness, readiness, startup)
   - Labels and selectors consistency
   - Dapr annotations (if applicable)
   - Image pull policy and tags
   - Service account configuration
   - Network policies and ingress rules

3. **Generate Report**
   - List all issues found (Critical / Warning / Info)
   - Provide exact code fixes for each issue
   - Rate overall manifest quality
   - Suggest improvements and best practices

4. **Provide Recommendations**
   - Security hardening suggestions
   - Performance optimization tips
   - High availability considerations
   - Monitoring and observability enhancements

## Validation Checklist

### Critical Issues (Must Fix)
- [ ] Missing resource requests/limits
- [ ] Running as root user
- [ ] No security context defined
- [ ] Missing liveness/readiness probes
- [ ] Using `latest` image tag
- [ ] Privileged containers
- [ ] Host network/PID/IPC enabled
- [ ] No replica count or replicas=1 in production

### Warnings (Should Fix)
- [ ] Missing labels (app, version, component)
- [ ] Inconsistent label selectors
- [ ] No pod disruption budget
- [ ] No resource quotas
- [ ] Image pull policy not set
- [ ] No service account specified
- [ ] Missing annotations for monitoring
- [ ] Dapr annotations incomplete

### Recommendations (Nice to Have)
- [ ] Add pod anti-affinity for HA
- [ ] Configure horizontal pod autoscaler
- [ ] Add network policies
- [ ] Enable pod security policies
- [ ] Add topology spread constraints
- [ ] Configure priority classes

## Rating Criteria

### Excellent (90-100%)
- All critical checks pass
- All warnings addressed
- Security best practices implemented
- Resource limits properly tuned
- Health probes configured correctly
- Labels and annotations complete
- High availability considerations
- Monitoring and observability ready

### Good (70-89%)
- All critical checks pass
- Most warnings addressed
- Basic security implemented
- Resource limits set
- Health probes present
- Essential labels defined

### Needs Improvement (<70%)
- Critical issues present
- Missing security context
- No resource limits
- Missing health probes
- Incomplete labels/selectors
- Not production-ready

## Validation Examples

### Example 1: Deployment Validation

#### Bad Deployment (Needs Improvement - 45%)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: app
        image: myapp:latest
        ports:
        - containerPort: 8080
```

#### Issues Found

**Critical Issues:**
1. ❌ Missing resource requests/limits
2. ❌ No security context (running as root)
3. ❌ Missing liveness/readiness probes
4. ❌ Using `latest` image tag
5. ❌ Only 1 replica (not HA)

**Warnings:**
6. ⚠️ Missing version label
7. ⚠️ No image pull policy
8. ⚠️ No service account specified
9. ⚠️ Missing component label

**Rating: Needs Improvement (45%)**

#### Fixed Deployment (Excellent - 95%)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  labels:
    app: my-app
    version: v1.0.0
    component: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
      version: v1.0.0
  template:
    metadata:
      labels:
        app: my-app
        version: v1.0.0
        component: backend
    spec:
      serviceAccountName: my-app-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: app
        image: myapp:v1.0.0
        imagePullPolicy: IfNotPresent
        ports:
        - name: http
          containerPort: 8080
          protocol: TCP
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
          readOnlyRootFilesystem: true
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /app/cache
      volumes:
      - name: tmp
        emptyDir: {}
      - name: cache
        emptyDir: {}
```

**Rating: Excellent (95%)**

---

### Example 2: Service Validation

#### Bad Service (Good - 75%)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8080
  selector:
    app: my-app
```

#### Issues Found

**Warnings:**
1. ⚠️ Missing labels
2. ⚠️ Port not named
3. ⚠️ No protocol specified
4. ⚠️ Missing annotations for monitoring

**Rating: Good (75%)**

#### Fixed Service (Excellent - 100%)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
  labels:
    app: my-app
    version: v1.0.0
    component: backend
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/metrics"
spec:
  type: ClusterIP
  ports:
  - name: http
    port: 80
    targetPort: http
    protocol: TCP
  selector:
    app: my-app
    version: v1.0.0
```

**Rating: Excellent (100%)**

---

### Example 3: Dapr-Enabled Deployment

#### Bad Dapr Deployment (Needs Improvement - 55%)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "order-service"
    spec:
      containers:
      - name: app
        image: order-service:latest
        ports:
        - containerPort: 8000
```

#### Issues Found

**Critical Issues:**
1. ❌ Missing resource requests/limits
2. ❌ No security context
3. ❌ Missing health probes
4. ❌ Using `latest` tag

**Warnings:**
5. ⚠️ Incomplete Dapr annotations (missing app-port)
6. ⚠️ No Dapr sidecar resource limits
7. ⚠️ Missing Dapr metrics configuration

**Rating: Needs Improvement (55%)**

#### Fixed Dapr Deployment (Excellent - 98%)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  labels:
    app: order-service
    version: v2.1.0
    component: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: order-service
      version: v2.1.0
  template:
    metadata:
      labels:
        app: order-service
        version: v2.1.0
        component: backend
      annotations:
        # Dapr sidecar configuration
        dapr.io/enabled: "true"
        dapr.io/app-id: "order-service"
        dapr.io/app-port: "8000"
        dapr.io/app-protocol: "http"
        dapr.io/log-level: "info"
        dapr.io/enable-metrics: "true"
        dapr.io/metrics-port: "9090"
        dapr.io/sidecar-cpu-limit: "1000m"
        dapr.io/sidecar-memory-limit: "512Mi"
        dapr.io/sidecar-cpu-request: "100m"
        dapr.io/sidecar-memory-request: "128Mi"
        # Monitoring
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: order-service-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: app
        image: order-service:v2.1.0
        imagePullPolicy: IfNotPresent
        ports:
        - name: http
          containerPort: 8000
          protocol: TCP
        env:
        - name: DAPR_HTTP_PORT
          value: "3500"
        - name: DAPR_GRPC_PORT
          value: "50001"
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
          readOnlyRootFilesystem: true
        resources:
          requests:
            cpu: 250m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: tmp
          mountPath: /tmp
      volumes:
      - name: tmp
        emptyDir: {}
```

**Rating: Excellent (98%)**

---

## Detailed Validation Rules

### 1. API Version & Kind

**Check:**
- Correct apiVersion for resource type
- Valid kind name

**Common Issues:**
```yaml
# ❌ Wrong
apiVersion: v1
kind: Deployment  # Should be apps/v1

# ✅ Correct
apiVersion: apps/v1
kind: Deployment
```

**API Versions Reference:**
- Deployment, StatefulSet, DaemonSet, ReplicaSet: `apps/v1`
- Service, ConfigMap, Secret, PersistentVolumeClaim: `v1`
- Ingress: `networking.k8s.io/v1`
- HorizontalPodAutoscaler: `autoscaling/v2`
- CronJob: `batch/v1`
- NetworkPolicy: `networking.k8s.io/v1`

### 2. Resource Requests & Limits

**Check:**
- Both requests and limits defined
- Limits >= requests
- Reasonable values for workload type

**Common Issues:**
```yaml
# ❌ Missing resources
containers:
- name: app
  image: myapp:v1

# ⚠️ Only limits (no requests)
containers:
- name: app
  resources:
    limits:
      cpu: 500m
      memory: 512Mi

# ✅ Correct
containers:
- name: app
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi
```

**Recommended Values:**

| Workload Type | CPU Request | CPU Limit | Memory Request | Memory Limit |
|---------------|-------------|-----------|----------------|--------------|
| Small API | 100m | 500m | 128Mi | 512Mi |
| Medium API | 250m | 1000m | 256Mi | 1Gi |
| Large API | 500m | 2000m | 512Mi | 2Gi |
| Worker/Consumer | 250m | 1000m | 512Mi | 2Gi |
| Frontend | 50m | 200m | 64Mi | 256Mi |

### 3. Security Context

**Check:**
- Pod security context defined
- Container security context defined
- Non-root user
- Read-only root filesystem
- Dropped capabilities
- No privilege escalation

**Common Issues:**
```yaml
# ❌ No security context (runs as root)
spec:
  containers:
  - name: app
    image: myapp:v1

# ⚠️ Partial security context
spec:
  securityContext:
    runAsNonRoot: true
  containers:
  - name: app
    # Missing container-level security context

# ✅ Correct (comprehensive security)
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
        - ALL
      readOnlyRootFilesystem: true
      runAsNonRoot: true
```

### 4. Health Probes

**Check:**
- Liveness probe configured
- Readiness probe configured
- Startup probe (for slow-starting apps)
- Appropriate delays and timeouts

**Common Issues:**
```yaml
# ❌ No probes
containers:
- name: app
  image: myapp:v1

# ⚠️ Only liveness probe
containers:
- name: app
  livenessProbe:
    httpGet:
      path: /health
      port: 8080

# ✅ Correct (both probes)
containers:
- name: app
  livenessProbe:
    httpGet:
      path: /health
      port: http
    initialDelaySeconds: 30
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 3
  readinessProbe:
    httpGet:
      path: /ready
      port: http
    initialDelaySeconds: 10
    periodSeconds: 5
    timeoutSeconds: 3
    failureThreshold: 3
```

**Probe Types:**
- `httpGet`: HTTP endpoint check
- `tcpSocket`: TCP port check
- `exec`: Command execution check

**Recommended Settings:**
- Liveness: `initialDelaySeconds: 30`, `periodSeconds: 10`
- Readiness: `initialDelaySeconds: 10`, `periodSeconds: 5`
- Startup: `initialDelaySeconds: 0`, `periodSeconds: 10`, `failureThreshold: 30`

### 5. Labels & Selectors

**Check:**
- Required labels present (app, version, component)
- Selector matches template labels
- Consistent labeling across resources

**Common Issues:**
```yaml
# ❌ Missing labels
metadata:
  name: my-app
spec:
  selector:
    matchLabels:
      app: my-app

# ⚠️ Inconsistent labels
metadata:
  labels:
    app: my-app
spec:
  selector:
    matchLabels:
      name: my-app  # Doesn't match

# ✅ Correct
metadata:
  name: my-app
  labels:
    app: my-app
    version: v1.0.0
    component: backend
    managed-by: helm
spec:
  selector:
    matchLabels:
      app: my-app
      version: v1.0.0
  template:
    metadata:
      labels:
        app: my-app
        version: v1.0.0
        component: backend
```

**Recommended Labels:**
- `app`: Application name
- `version`: Application version
- `component`: Component type (backend, frontend, database)
- `part-of`: Larger application name
- `managed-by`: Management tool (helm, kustomize)
- `environment`: Environment (dev, staging, prod)

### 6. Dapr Annotations

**Check:**
- Required Dapr annotations present
- App ID matches service name
- App port specified
- Resource limits for sidecar

**Common Issues:**
```yaml
# ❌ Incomplete Dapr config
annotations:
  dapr.io/enabled: "true"

# ⚠️ Missing sidecar resources
annotations:
  dapr.io/enabled: "true"
  dapr.io/app-id: "my-service"
  dapr.io/app-port: "8000"

# ✅ Correct (complete Dapr config)
annotations:
  dapr.io/enabled: "true"
  dapr.io/app-id: "my-service"
  dapr.io/app-port: "8000"
  dapr.io/app-protocol: "http"
  dapr.io/log-level: "info"
  dapr.io/enable-metrics: "true"
  dapr.io/metrics-port: "9090"
  dapr.io/sidecar-cpu-limit: "1000m"
  dapr.io/sidecar-memory-limit: "512Mi"
  dapr.io/sidecar-cpu-request: "100m"
  dapr.io/sidecar-memory-request: "128Mi"
```

**Required Dapr Annotations:**
- `dapr.io/enabled`: Enable Dapr sidecar
- `dapr.io/app-id`: Unique application ID
- `dapr.io/app-port`: Application port
- `dapr.io/app-protocol`: Protocol (http, grpc)

**Recommended Dapr Annotations:**
- `dapr.io/log-level`: Logging level
- `dapr.io/enable-metrics`: Enable metrics
- `dapr.io/sidecar-cpu-limit`: CPU limit for sidecar
- `dapr.io/sidecar-memory-limit`: Memory limit for sidecar

### 7. Image Configuration

**Check:**
- No `latest` tag in production
- Image pull policy set
- Image from trusted registry

**Common Issues:**
```yaml
# ❌ Using latest tag
containers:
- name: app
  image: myapp:latest

# ⚠️ No pull policy
containers:
- name: app
  image: myapp:v1.0.0

# ✅ Correct
containers:
- name: app
  image: myregistry.azurecr.io/myapp:v1.0.0
  imagePullPolicy: IfNotPresent
```

**Image Pull Policies:**
- `IfNotPresent`: Pull if not cached (recommended)
- `Always`: Always pull (use for `latest` tag)
- `Never`: Never pull (use for local images)

### 8. High Availability

**Check:**
- Multiple replicas (>= 3 for production)
- Pod disruption budget defined
- Anti-affinity rules for spreading

**Common Issues:**
```yaml
# ❌ Single replica
spec:
  replicas: 1

# ⚠️ No pod disruption budget
spec:
  replicas: 3

# ✅ Correct (HA configuration)
spec:
  replicas: 3
  template:
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - my-app
              topologyKey: kubernetes.io/hostname
```

**Pod Disruption Budget:**
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: my-app-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: my-app
```

## Validation Commands

### Kubectl Validation

```bash
# Dry-run validation
kubectl apply -f deployment.yaml --dry-run=client

# Server-side validation
kubectl apply -f deployment.yaml --dry-run=server

# Validate all manifests in directory
kubectl apply -f ./manifests/ --dry-run=server --validate=true
```

### Kubeval

```bash
# Install kubeval
brew install kubeval

# Validate single file
kubeval deployment.yaml

# Validate all YAML files
kubeval manifests/*.yaml

# Validate with specific Kubernetes version
kubeval --kubernetes-version 1.28.0 deployment.yaml
```

### Kube-score

```bash
# Install kube-score
brew install kube-score

# Score manifest
kube-score score deployment.yaml

# Score with detailed output
kube-score score deployment.yaml --output-format ci

# Score all manifests
kube-score score manifests/*.yaml
```

### Polaris

```bash
# Install Polaris
kubectl apply -f https://github.com/FairwindsOps/polaris/releases/latest/download/dashboard.yaml

# Run Polaris audit
polaris audit --audit-path ./manifests/

# Generate HTML report
polaris audit --audit-path ./manifests/ --format html > report.html
```

## Automated Validation Script

```bash
#!/bin/bash
# validate-manifests.sh
# Comprehensive Kubernetes manifest validation

set -e

MANIFEST_DIR="${1:-.}"
KUBERNETES_VERSION="${KUBERNETES_VERSION:-1.28.0}"

echo "🔍 Validating Kubernetes manifests in: $MANIFEST_DIR"
echo ""

# Check if tools are installed
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl not found"; exit 1; }
command -v kubeval >/dev/null 2>&1 || { echo "⚠️  kubeval not found (optional)"; }
command -v kube-score >/dev/null 2>&1 || { echo "⚠️  kube-score not found (optional)"; }

# 1. Kubectl dry-run validation
echo "1️⃣  Running kubectl dry-run validation..."
for file in "$MANIFEST_DIR"/*.yaml; do
    if [ -f "$file" ]; then
        echo "  Validating: $file"
        kubectl apply -f "$file" --dry-run=client --validate=true
    fi
done
echo "✅ Kubectl validation passed"
echo ""

# 2. Kubeval validation
if command -v kubeval >/dev/null 2>&1; then
    echo "2️⃣  Running kubeval validation..."
    kubeval --kubernetes-version "$KUBERNETES_VERSION" "$MANIFEST_DIR"/*.yaml
    echo "✅ Kubeval validation passed"
    echo ""
fi

# 3. Kube-score validation
if command -v kube-score >/dev/null 2>&1; then
    echo "3️⃣  Running kube-score validation..."
    kube-score score "$MANIFEST_DIR"/*.yaml --output-format ci
    echo ""
fi

echo "🎉 All validations completed!"
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Validate Kubernetes Manifests

on:
  pull_request:
    paths:
      - 'k8s/**/*.yaml'
      - 'manifests/**/*.yaml'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install tools
        run: |
          curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
          chmod +x kubectl
          sudo mv kubectl /usr/local/bin/

          wget https://github.com/instrumenta/kubeval/releases/latest/download/kubeval-linux-amd64.tar.gz
          tar xf kubeval-linux-amd64.tar.gz
          sudo mv kubeval /usr/local/bin/

      - name: Validate manifests
        run: |
          kubectl apply -f k8s/ --dry-run=client --validate=true
          kubeval k8s/*.yaml

      - name: Score manifests
        uses: zegl/kube-score-ga@v1
        with:
          manifests-folders: 'k8s/'
```

## Best Practices Summary

### Security
✅ Run as non-root user
✅ Drop all capabilities
✅ Read-only root filesystem
✅ No privilege escalation
✅ Use security context
✅ Scan images for vulnerabilities

### Reliability
✅ Set resource requests and limits
✅ Configure liveness and readiness probes
✅ Use multiple replicas (>= 3)
✅ Define pod disruption budgets
✅ Implement anti-affinity rules

### Observability
✅ Add Prometheus annotations
✅ Configure structured logging
✅ Enable metrics endpoints
✅ Use consistent labels
✅ Add monitoring dashboards

### Performance
✅ Right-size resource limits
✅ Use horizontal pod autoscaling
✅ Configure appropriate probe intervals
✅ Optimize image size
✅ Use init containers for setup

## Final Message from Skill

Your Kubernetes manifests have been validated! 🎉

**Validation Summary:**
- ✅ Critical issues: [count]
- ⚠️  Warnings: [count]
- ℹ️  Recommendations: [count]

**Overall Rating: [Excellent / Good / Needs Improvement]**

**Next Steps:**

1. **Fix Critical Issues** (if any):
   - Apply suggested security context changes
   - Add resource requests/limits
   - Configure health probes
   - Use specific image tags

2. **Address Warnings**:
   - Add missing labels
   - Complete Dapr annotations
   - Set image pull policy
   - Define service accounts

3. **Consider Recommendations**:
   - Increase replica count for HA
   - Add pod disruption budgets
   - Configure autoscaling
   - Implement anti-affinity rules

4. **Validate Again**:
   ```bash
   kubectl apply -f manifest.yaml --dry-run=server
   kubeval manifest.yaml
   kube-score score manifest.yaml
   ```

5. **Deploy with Confidence**:
   ```bash
   kubectl apply -f manifest.yaml
   kubectl rollout status deployment/my-app
   ```

**Pro Tips:**
- Use `kubectl diff` to preview changes before applying
- Enable admission controllers (PodSecurity, ResourceQuota)
- Implement GitOps with ArgoCD or Flux
- Set up automated validation in CI/CD pipeline
- Use Helm or Kustomize for templating
- Monitor resource usage and adjust limits accordingly
- Regular security audits with tools like Trivy or Snyk
- Document your manifest standards in a style guide

**Validation Tools Used:**
- kubectl (built-in validation)
- kubeval (schema validation)
- kube-score (best practices scoring)
- polaris (security and reliability checks)

Happy deploying! 🚀
