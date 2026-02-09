---
name: dapr-sidecar-injection
description: Generate correct Dapr sidecar injection annotations for Kubernetes Deployments, StatefulSets, and Jobs with best practices for app-id, ports, configuration, and observability.
version: 1.0.0
---

# Dapr Sidecar Injection Helper Skill

## When to Use This Skill

Use this skill when you need to:
- Add Dapr sidecar injection to existing Kubernetes Deployments
- Configure Dapr annotations for new microservices
- Enable service-to-service invocation between microservices
- Integrate pub/sub messaging via Dapr components
- Add state management or bindings to a service
- Configure Dapr observability (metrics, tracing, logging)
- Troubleshoot Dapr sidecar injection issues
- Standardize Dapr configuration across multiple services

## How This Skill Works

1. **Gather Service Information**
   - Service name (becomes Dapr app-id)
   - Application port (HTTP/gRPC port your app listens on)
   - Dapr features needed (service invocation, pub/sub, state, bindings)
   - Observability requirements (metrics, tracing, log level)

2. **Generate Annotations**
   - Create `podAnnotations` block with required Dapr annotations
   - Add optional annotations for advanced features
   - Include resource limits for Dapr sidecar container

3. **Apply Best Practices**
   - Consistent app-id naming (kebab-case, DNS-safe)
   - Explicit port configuration (avoid auto-detection)
   - Appropriate log levels per environment
   - mTLS enabled by default
   - Metrics and tracing endpoints configured

4. **Validate and Document**
   - Verification commands to check sidecar injection
   - Troubleshooting guidance for common issues
   - Component configuration examples

## Output Files Generated

```
k8s/
├── deployment.yaml              # Deployment with Dapr annotations
├── dapr-components/
│   ├── pubsub.yaml              # Pub/sub component (optional)
│   ├── statestore.yaml          # State store component (optional)
│   └── binding.yaml             # Input/output binding (optional)
└── dapr-config.yaml             # Dapr Configuration CRD (optional)
```

## Instructions

### 1. Basic Dapr Annotations (Minimal)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ service-name }}
  labels:
    app: {{ service-name }}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {{ service-name }}
  template:
    metadata:
      labels:
        app: {{ service-name }}
      annotations:
        # ── Required Dapr Annotations ──
        dapr.io/enabled: "true"
        dapr.io/app-id: "{{ app-id }}"              # e.g. user-service
        dapr.io/app-port: "{{ port }}"              # e.g. 8000 (your app's HTTP port)
    spec:
      containers:
      - name: {{ service-name }}
        image: {{ image }}
        ports:
        - containerPort: {{ port }}
          name: http
```

### 2. Full Dapr Annotations (Production-Ready)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ service-name }}
  labels:
    app: {{ service-name }}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: {{ service-name }}
  template:
    metadata:
      labels:
        app: {{ service-name }}
      annotations:
        # ── Core Dapr Annotations ──
        dapr.io/enabled: "true"
        dapr.io/app-id: "{{ app-id }}"                    # Unique service identifier
        dapr.io/app-port: "{{ port }}"                    # Your app's HTTP/gRPC port
        dapr.io/app-protocol: "http"                      # http | grpc | https | grpcs

        # ── Configuration ──
        dapr.io/config: "dapr-config"                     # Name of Configuration CRD
        dapr.io/app-max-concurrency: "-1"                 # Max concurrent requests (-1 = unlimited)

        # ── Logging ──
        dapr.io/log-level: "info"                         # debug | info | warn | error
        dapr.io/log-as-json: "true"                       # Structured JSON logs

        # ── Observability ──
        dapr.io/enable-metrics: "true"                    # Expose Prometheus metrics
        dapr.io/metrics-port: "9090"                      # Metrics endpoint port
        dapr.io/enable-profiling: "false"                 # pprof profiling endpoint

        # ── API Tokens (Security) ──
        dapr.io/enable-api-logging: "false"               # Log all API calls (verbose)
        dapr.io/api-token-secret: "dapr-api-token"        # Secret for API authentication

        # ── Resource Limits for Sidecar ──
        dapr.io/sidecar-cpu-limit: "500m"
        dapr.io/sidecar-memory-limit: "512Mi"
        dapr.io/sidecar-cpu-request: "100m"
        dapr.io/sidecar-memory-request: "128Mi"

        # ── Networking ──
        dapr.io/app-ssl: "false"                          # Use HTTPS to talk to app
        dapr.io/sidecar-listen-addresses: "0.0.0.0"       # Sidecar bind address
        dapr.io/http-max-request-size: "4"                # Max HTTP request body (MB)
        dapr.io/http-read-buffer-size: "4"                # HTTP read buffer (KB)

        # ── Placement (for Actors) ──
        dapr.io/placement-host-address: "dapr-placement-server.dapr-system.svc.cluster.local:50005"

        # ── Volume Mounts (for Unix Domain Sockets) ──
        dapr.io/unix-domain-socket-path: ""               # Path for UDS (advanced)
        dapr.io/volume-mounts: "name:volume-name,mountPath:/mnt/data"
        dapr.io/volume-mounts-rw: "name:rw-volume,mountPath:/mnt/rw"
    spec:
      containers:
      - name: {{ service-name }}
        image: {{ image }}
        ports:
        - containerPort: {{ port }}
          name: http
        env:
        - name: DAPR_HTTP_PORT
          value: "3500"                                   # Dapr sidecar HTTP port
        - name: DAPR_GRPC_PORT
          value: "50001"                                  # Dapr sidecar gRPC port
```

### 3. Dapr Configuration CRD (dapr-config.yaml)

```yaml
apiVersion: dapr.io/v1alpha1
kind: Configuration
metadata:
  name: dapr-config
  namespace: {{ namespace }}
spec:
  # ── Tracing ──
  tracing:
    samplingRate: "1"                                     # 1 = 100%, 0.1 = 10%
    zipkin:
      endpointAddress: "http://zipkin.observability.svc.cluster.local:9411/api/v2/spans"
    # Or use OpenTelemetry
    # otel:
    #   endpointAddress: "otel-collector.observability.svc.cluster.local:4317"
    #   isSecure: false
    #   protocol: "grpc"

  # ── Metrics ──
  metric:
    enabled: true

  # ── mTLS (Mutual TLS) ──
  mtls:
    enabled: true
    workloadCertTTL: "24h"
    allowedClockSkew: "15m"

  # ── Access Control ──
  accessControl:
    defaultAction: "deny"
    trustDomain: "public"
    policies:
    - appId: "{{ app-id }}"
      defaultAction: "allow"
      trustDomain: "public"
      namespace: "{{ namespace }}"
      operations:
      - name: "/api/*"
        httpVerb: ["GET", "POST"]
        action: "allow"

  # ── API Middleware ──
  httpPipeline:
    handlers:
    - name: oauth2
      type: middleware.http.oauth2
    - name: ratelimit
      type: middleware.http.ratelimit

  # ── Secrets ──
  secrets:
    scopes:
    - storeName: "kubernetes"
      defaultAccess: "allow"
      allowedSecrets: ["db-password", "api-key"]

  # ── Component Scopes ──
  components:
    deny:
    - "internal-statestore"
```

### 4. Service-to-Service Invocation Example

**Caller Service (order-service):**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
spec:
  template:
    metadata:
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "order-service"
        dapr.io/app-port: "8000"
        dapr.io/log-level: "info"
    spec:
      containers:
      - name: order-service
        image: order-service:latest
        env:
        - name: USER_SERVICE_URL
          value: "http://localhost:3500/v1.0/invoke/user-service/method"
```

**Called Service (user-service):**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  template:
    metadata:
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "user-service"
        dapr.io/app-port: "8001"
        dapr.io/log-level: "info"
    spec:
      containers:
      - name: user-service
        image: user-service:latest
        ports:
        - containerPort: 8001
```

**Invocation from order-service code:**

```python
# Python FastAPI example
import httpx

async def get_user(user_id: str):
    # Call user-service via Dapr sidecar
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:3500/v1.0/invoke/user-service/method/users/{user_id}"
        )
        return response.json()
```

### 5. Pub/Sub Consumer Example

**Deployment with Pub/Sub:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: event-processor
spec:
  template:
    metadata:
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "event-processor"
        dapr.io/app-port: "8002"
        dapr.io/log-level: "info"
    spec:
      containers:
      - name: event-processor
        image: event-processor:latest
```

**Pub/Sub Component (pubsub.yaml):**

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
  namespace: {{ namespace }}
spec:
  type: pubsub.kafka
  version: v1
  metadata:
  - name: brokers
    value: "dev-kafka-kafka-bootstrap.kafka.svc.cluster.local:9092"
  - name: consumerGroup
    value: "event-processor-group"
  - name: authType
    value: "none"
scopes:
- event-processor
```

**Subscription (subscription.yaml):**

```yaml
apiVersion: dapr.io/v2alpha1
kind: Subscription
metadata:
  name: order-events-sub
  namespace: {{ namespace }}
spec:
  pubsubname: pubsub
  topic: order-events
  routes:
    default: /events/orders
  scopes:
  - event-processor
```

### 6. State Store Example

**Deployment:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cart-service
spec:
  template:
    metadata:
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "cart-service"
        dapr.io/app-port: "8003"
    spec:
      containers:
      - name: cart-service
        image: cart-service:latest
```

**State Store Component (statestore.yaml):**

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
  namespace: {{ namespace }}
spec:
  type: state.redis
  version: v1
  metadata:
  - name: redisHost
    value: "redis-master.infra.svc.cluster.local:6379"
  - name: redisPassword
    secretKeyRef:
      name: redis-secret
      key: password
  - name: actorStateStore
    value: "true"
scopes:
- cart-service
```

### 7. gRPC Service Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grpc-service
spec:
  template:
    metadata:
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "grpc-service"
        dapr.io/app-port: "50051"
        dapr.io/app-protocol: "grpc"                      # Important for gRPC
        dapr.io/log-level: "info"
    spec:
      containers:
      - name: grpc-service
        image: grpc-service:latest
        ports:
        - containerPort: 50051
          name: grpc
```

## Annotation Reference

### Required Annotations

| Annotation | Values | Description |
|------------|--------|-------------|
| `dapr.io/enabled` | `"true"` \| `"false"` | Enable Dapr sidecar injection |
| `dapr.io/app-id` | DNS-safe string | Unique identifier for service invocation |
| `dapr.io/app-port` | Port number | Port your application listens on |

### Common Optional Annotations

| Annotation | Default | Description |
|------------|---------|-------------|
| `dapr.io/app-protocol` | `"http"` | `http` \| `grpc` \| `https` \| `grpcs` |
| `dapr.io/config` | `"daprsystem"` | Name of Configuration CRD |
| `dapr.io/log-level` | `"info"` | `debug` \| `info` \| `warn` \| `error` |
| `dapr.io/enable-metrics` | `"true"` | Expose Prometheus metrics on `:9090/metrics` |
| `dapr.io/metrics-port` | `"9090"` | Port for metrics endpoint |
| `dapr.io/sidecar-cpu-limit` | `"4000m"` | CPU limit for sidecar |
| `dapr.io/sidecar-memory-limit` | `"4000Mi"` | Memory limit for sidecar |
| `dapr.io/sidecar-cpu-request` | `"100m"` | CPU request for sidecar |
| `dapr.io/sidecar-memory-request` | `"250Mi"` | Memory request for sidecar |
| `dapr.io/app-max-concurrency` | `"-1"` | Max concurrent requests (-1 = unlimited) |
| `dapr.io/enable-profiling` | `"false"` | Enable pprof profiling endpoint |
| `dapr.io/log-as-json` | `"false"` | Output logs as JSON |

### Advanced Annotations

| Annotation | Default | Description |
|------------|---------|-------------|
| `dapr.io/app-ssl` | `"false"` | Use HTTPS to communicate with app |
| `dapr.io/http-max-request-size` | `"4"` | Max HTTP request body size (MB) |
| `dapr.io/http-read-buffer-size` | `"4"` | HTTP read buffer size (KB) |
| `dapr.io/enable-api-logging` | `"false"` | Log all Dapr API calls (verbose) |
| `dapr.io/api-token-secret` | `""` | Kubernetes Secret name for API token |
| `dapr.io/app-token-secret` | `""` | Secret for app-to-sidecar auth |
| `dapr.io/unix-domain-socket-path` | `""` | Unix domain socket path (advanced) |
| `dapr.io/volume-mounts` | `""` | Volume mounts for sidecar (read-only) |
| `dapr.io/volume-mounts-rw` | `""` | Volume mounts for sidecar (read-write) |
| `dapr.io/env` | `""` | Environment variables for sidecar |
| `dapr.io/sidecar-liveness-probe-*` | Various | Custom liveness probe settings |
| `dapr.io/sidecar-readiness-probe-*` | Various | Custom readiness probe settings |

## Verification Commands

### Check if Sidecar is Injected

```bash
# List pods with Dapr sidecar
kubectl get pods -l dapr.io/enabled=true

# Check specific pod has 2 containers (app + daprd)
kubectl get pod <pod-name> -o jsonpath='{.spec.containers[*].name}'
# Expected: <app-name> daprd

# View Dapr sidecar logs
kubectl logs <pod-name> -c daprd

# Check Dapr sidecar version
kubectl exec <pod-name> -c daprd -- daprd --version
```

### Test Service Invocation

```bash
# Port-forward to Dapr sidecar
kubectl port-forward <pod-name> 3500:3500

# Invoke service via Dapr
curl http://localhost:3500/v1.0/invoke/<app-id>/method/<endpoint>

# Check Dapr metadata
curl http://localhost:3500/v1.0/metadata
```

### Check Dapr Components

```bash
# List all Dapr components
kubectl get components -n <namespace>

# Describe specific component
kubectl describe component <component-name> -n <namespace>

# Check component logs in sidecar
kubectl logs <pod-name> -c daprd | grep -i component
```

### Metrics and Health

```bash
# Port-forward to metrics endpoint
kubectl port-forward <pod-name> 9090:9090

# Scrape Prometheus metrics
curl http://localhost:9090/metrics

# Check Dapr health
curl http://localhost:3500/v1.0/healthz
```

## Example Usage

### FastAPI Service with Pub/Sub

```
Service Name: order-processor
App ID: order-processor
Port: 8000
Protocol: HTTP
Features: Pub/Sub (Kafka), State Store (Redis)
Log Level: info
```

### gRPC Service with Service Invocation

```
Service Name: payment-service
App ID: payment-service
Port: 50051
Protocol: gRPC
Features: Service Invocation only
Log Level: warn
```

### Background Worker (No HTTP Server)

```
Service Name: batch-worker
App ID: batch-worker
Port: (none - omit dapr.io/app-port)
Protocol: N/A
Features: Bindings (Cron), State Store
Log Level: debug
```

## Security & Best Practices Included

✅ **Naming Conventions**
- Use kebab-case for app-id (e.g., `user-service`, not `UserService`)
- App-id must be DNS-safe (alphanumeric + hyphens)
- Keep app-id unique across the cluster
- Match app-id to Deployment name for consistency

✅ **Port Configuration**
- Always explicitly set `dapr.io/app-port` (avoid auto-detection)
- Use standard ports: 8000-8999 for HTTP, 50051+ for gRPC
- Expose Dapr sidecar ports as env vars (`DAPR_HTTP_PORT=3500`)

✅ **Security**
- Enable mTLS in Configuration CRD for production
- Use `dapr.io/api-token-secret` for API authentication
- Scope components to specific app-ids (avoid global access)
- Use Kubernetes Secrets for sensitive component metadata
- Set `accessControl` policies in Configuration CRD

✅ **Resource Management**
- Set CPU/memory limits for Dapr sidecar (default: 4 CPU / 4Gi RAM)
- Typical dev values: `100m CPU / 128Mi RAM` request, `500m / 512Mi` limit
- Monitor sidecar resource usage via Prometheus metrics

✅ **Observability**
- Enable metrics (`dapr.io/enable-metrics: "true"`)
- Configure tracing in Configuration CRD (Zipkin/OTEL)
- Use structured JSON logs (`dapr.io/log-as-json: "true"`)
- Set appropriate log levels per environment (debug → dev, info → prod)

✅ **High Availability**
- Run multiple replicas for stateless services
- Use Dapr Actors for stateful services with automatic failover
- Configure placement service for actor distribution
- Set `app-max-concurrency` based on load testing

## Customization Examples

### Add Custom Dapr Configuration

```yaml
apiVersion: dapr.io/v1alpha1
kind: Configuration
metadata:
  name: custom-config
spec:
  tracing:
    samplingRate: "0.1"                                   # 10% sampling
    zipkin:
      endpointAddress: "http://zipkin:9411/api/v2/spans"
  mtls:
    enabled: true
  metric:
    enabled: true
```

Then reference in Deployment:

```yaml
annotations:
  dapr.io/config: "custom-config"
```

### Add API Token Authentication

Create Secret:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: dapr-api-token
type: Opaque
stringData:
  token: "your-secure-token-here"
```

Reference in Deployment:

```yaml
annotations:
  dapr.io/api-token-secret: "dapr-api-token"
```

### Add Volume Mounts for Sidecar

```yaml
annotations:
  dapr.io/volume-mounts: "name:config-volume,mountPath:/etc/config"
  dapr.io/volume-mounts-rw: "name:data-volume,mountPath:/data"
spec:
  volumes:
  - name: config-volume
    configMap:
      name: app-config
  - name: data-volume
    emptyDir: {}
```

### Custom Liveness/Readiness Probes for Sidecar

```yaml
annotations:
  dapr.io/sidecar-liveness-probe-delay-seconds: "10"
  dapr.io/sidecar-liveness-probe-timeout-seconds: "5"
  dapr.io/sidecar-liveness-probe-period-seconds: "10"
  dapr.io/sidecar-readiness-probe-delay-seconds: "5"
  dapr.io/sidecar-readiness-probe-timeout-seconds: "3"
  dapr.io/sidecar-readiness-probe-period-seconds: "5"
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Sidecar not injected | Dapr not installed or wrong namespace | Run `dapr status -k` to verify Dapr installation |
| Pod stuck in Init | Dapr placement service not ready | Check `kubectl get pods -n dapr-system` |
| Service invocation fails | Wrong app-id or app-port | Verify with `curl localhost:3500/v1.0/metadata` inside pod |
| Component not loading | Scopes mismatch or wrong namespace | Check `kubectl logs <pod> -c daprd \| grep component` |
| High sidecar memory usage | Default limits too high | Set `dapr.io/sidecar-memory-limit: "512Mi"` |
| mTLS errors | Certificate issues or clock skew | Check `allowedClockSkew` in Configuration CRD |
| Pub/Sub not receiving | Subscription not created or wrong topic | Verify `kubectl get subscriptions -n <namespace>` |
| State operations fail | State store component not configured | Check component with `kubectl describe component statestore` |

## Final Message from Skill

Your Dapr sidecar annotations are ready! 🚀

**Next Steps:**
1. Add the `podAnnotations` block to your Deployment YAML
2. Replace `{{ placeholders }}` with your actual values
3. Create Dapr components in `k8s/dapr-components/` directory
4. Apply with `kubectl apply -f deployment.yaml`
5. Verify with `kubectl get pods` (should show 2/2 containers)

**Pro Tips:**
- Use `dapr dashboard -k` to visualize all Dapr-enabled services
- Scope components to specific app-ids for security
- Enable mTLS in production via Configuration CRD
- Monitor sidecar resource usage and adjust limits accordingly
- Use `dapr logs -a <app-id> -k` to tail sidecar logs
- Test service invocation with `dapr invoke -a <app-id> -m <method> -k`

Happy building with Dapr! 🎯
