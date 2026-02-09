---
name: helm-chart-generator
description: Generate production-ready Helm 3 charts for FastAPI services, Kafka consumers, Dapr sidecars, and microservices with best practices.
version: 1.0.0
---

# Helm Chart Generator Skill

## When to Use This Skill

Use this skill when you need to:
- Generate Helm charts for FastAPI applications, Kafka consumers, or any microservice
- Deploy services to Kubernetes (Minikube, AKS, GKE, OKE)
- Add Dapr sidecar integration to existing services
- Create production-ready charts with security and observability best practices
- Standardize deployment configurations across multiple services

## How This Skill Works

1. **Gather Service Information**
   - Service name, type (FastAPI/Kafka/Generic), port, and image details
   - Environment variables, secrets, and ConfigMap requirements
   - Resource requirements (CPU/memory requests and limits)
   - Health check endpoints (liveness/readiness probes)

2. **Generate Chart Structure**
   - Create `Chart.yaml` with metadata and dependencies
   - Create `values.yaml` with configurable defaults
   - Generate templates: Deployment, Service, Ingress (optional), ConfigMap, Secret

3. **Apply Best Practices**
   - Non-root security context
   - Resource requests and limits
   - Liveness and readiness probes
   - Dapr annotations (if requested)
   - Rolling update strategy
   - Pod disruption budgets (optional)

4. **Validate and Document**
   - Include README.md with installation instructions
   - Add NOTES.txt for post-installation guidance
   - Validate chart structure with `helm lint`

## Output Files Generated

```
<service-name>/
├── Chart.yaml              # Chart metadata
├── values.yaml             # Default configuration values
├── README.md               # Installation and usage guide
├── templates/
│   ├── deployment.yaml     # Kubernetes Deployment
│   ├── service.yaml        # Kubernetes Service
│   ├── ingress.yaml        # Ingress (optional)
│   ├── configmap.yaml      # ConfigMap for env vars
│   ├── secret.yaml         # Secret for sensitive data
│   ├── serviceaccount.yaml # ServiceAccount (optional)
│   ├── hpa.yaml            # HorizontalPodAutoscaler (optional)
│   ├── _helpers.tpl        # Template helpers
│   └── NOTES.txt           # Post-install notes
└── .helmignore             # Files to ignore
```

## Instructions

### 1. Chart.yaml Template

```yaml
apiVersion: v2
name: {{ service-name }}
description: A Helm chart for {{ service-description }}
type: application
version: 0.1.0
appVersion: "1.0.0"
keywords:
  - fastapi
  - microservice
  - dapr
maintainers:
  - name: Your Team
    email: team@example.com
```

### 2. values.yaml Template

```yaml
# Default values for {{ service-name }}
replicaCount: 1

image:
  repository: {{ registry }}/{{ service-name }}
  pullPolicy: IfNotPresent
  tag: "latest"

imagePullSecrets: []
nameOverride: ""
fullnameOverride: ""

serviceAccount:
  create: true
  annotations: {}
  name: ""

podAnnotations:
  # Dapr sidecar annotations (uncomment if using Dapr)
  # dapr.io/enabled: "true"
  # dapr.io/app-id: "{{ service-name }}"
  # dapr.io/app-port: "8000"
  # dapr.io/log-level: "info"

podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000

securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true

service:
  type: ClusterIP
  port: 80
  targetPort: 8000

ingress:
  enabled: false
  className: "nginx"
  annotations: {}
    # cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: chart-example.local
      paths:
        - path: /
          pathType: Prefix
  tls: []

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

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

autoscaling:
  enabled: false
  minReplicas: 1
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
  targetMemoryUtilizationPercentage: 80

env:
  - name: LOG_LEVEL
    value: "info"
  - name: ENVIRONMENT
    value: "production"

envFrom: []
  # - configMapRef:
  #     name: app-config
  # - secretRef:
  #     name: app-secrets

nodeSelector: {}

tolerations: []

affinity: {}
```

### 3. Deployment Template (templates/deployment.yaml)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "chart.fullname" . }}
  labels:
    {{- include "chart.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "chart.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        {{- with .Values.podAnnotations }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
      labels:
        {{- include "chart.selectorLabels" . | nindent 8 }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      serviceAccountName: {{ include "chart.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      containers:
      - name: {{ .Chart.Name }}
        securityContext:
          {{- toYaml .Values.securityContext | nindent 12 }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - name: http
          containerPort: {{ .Values.service.targetPort }}
          protocol: TCP
        livenessProbe:
          {{- toYaml .Values.livenessProbe | nindent 12 }}
        readinessProbe:
          {{- toYaml .Values.readinessProbe | nindent 12 }}
        resources:
          {{- toYaml .Values.resources | nindent 12 }}
        env:
          {{- toYaml .Values.env | nindent 12 }}
        {{- with .Values.envFrom }}
        envFrom:
          {{- toYaml . | nindent 12 }}
        {{- end }}
        volumeMounts:
        - name: tmp
          mountPath: /tmp
      volumes:
      - name: tmp
        emptyDir: {}
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
```

### 4. Service Template (templates/service.yaml)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "chart.fullname" . }}
  labels:
    {{- include "chart.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    {{- include "chart.selectorLabels" . | nindent 4 }}
```

### 5. Helpers Template (templates/_helpers.tpl)

```yaml
{{/*
Expand the name of the chart.
*/}}
{{- define "chart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "chart.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "chart.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "chart.labels" -}}
helm.sh/chart: {{ include "chart.chart" . }}
{{ include "chart.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "chart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "chart.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "chart.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
```

## Example Usage

### FastAPI Service with Dapr

```bash
# Generate chart for FastAPI service
Service Name: user-service
Service Type: FastAPI
Port: 8000
Enable Dapr: Yes
Dapr App ID: user-service
Health Endpoint: /health
Ready Endpoint: /ready
```

### Kafka Consumer

```bash
# Generate chart for Kafka consumer
Service Name: event-processor
Service Type: Kafka Consumer
No Service/Ingress needed: Yes
Enable Dapr: Yes (for pub/sub)
```

## Security & Best Practices Included

✅ **Security**
- Non-root user (UID 1000)
- Read-only root filesystem
- Drop all capabilities
- No privilege escalation

✅ **Reliability**
- Liveness and readiness probes
- Resource requests and limits
- Rolling update strategy
- Pod disruption budgets (optional)

✅ **Observability**
- Structured logging support
- Prometheus metrics annotations (optional)
- Health check endpoints

✅ **Scalability**
- Horizontal Pod Autoscaler support
- Configurable replica count
- Resource-based scaling

✅ **Dapr Integration**
- Sidecar annotations ready
- App ID and port configuration
- Log level control

## Installation Commands

```bash
# Lint the chart
helm lint ./{{ service-name }}

# Dry run to see generated manifests
helm install {{ service-name }} ./{{ service-name }} --dry-run --debug

# Install the chart
helm install {{ service-name }} ./{{ service-name }}

# Install with custom values
helm install {{ service-name }} ./{{ service-name }} -f custom-values.yaml

# Upgrade the release
helm upgrade {{ service-name }} ./{{ service-name }}

# Uninstall the release
helm uninstall {{ service-name }}
```

## Customization Examples

### Enable Ingress

```yaml
ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: api.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: api-tls
      hosts:
        - api.example.com
```

### Enable Dapr Sidecar

```yaml
podAnnotations:
  dapr.io/enabled: "true"
  dapr.io/app-id: "user-service"
  dapr.io/app-port: "8000"
  dapr.io/log-level: "info"
  dapr.io/enable-metrics: "true"
  dapr.io/metrics-port: "9090"
```

### Add Environment Variables from ConfigMap/Secret

```yaml
envFrom:
  - configMapRef:
      name: app-config
  - secretRef:
      name: app-secrets
```

### Enable Autoscaling

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
```

## Final Message from Skill

Your Helm chart is ready! 🎉

**Next Steps:**
1. Review and customize `values.yaml` for your environment
2. Run `helm lint ./{{ service-name }}` to validate
3. Test with `helm install --dry-run --debug`
4. Deploy with `helm install {{ service-name }} ./{{ service-name }}`

**Pro Tips:**
- Use separate values files for dev/staging/prod environments
- Store sensitive data in Kubernetes Secrets, not in values.yaml
- Enable Dapr annotations if using Dapr for service mesh
- Configure resource limits based on actual usage metrics
- Set up monitoring and alerting for your deployments

Happy deploying! 🚀
