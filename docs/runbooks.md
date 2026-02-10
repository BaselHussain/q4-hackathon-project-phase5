# Operational Runbooks

This document contains step-by-step procedures for common operational tasks and incident response.

## Table of Contents

1. [Deployment Procedures](#deployment-procedures)
2. [Incident Response](#incident-response)
3. [Scaling Operations](#scaling-operations)
4. [Backup and Restore](#backup-and-restore)
5. [Troubleshooting](#troubleshooting)
6. [Maintenance Tasks](#maintenance-tasks)

---

## Deployment Procedures

### Deploy to Minikube (Local Development)

**Purpose**: Set up local development environment with full stack

**Prerequisites**:
- Minikube installed
- Docker installed
- kubectl installed
- Helm 3 installed

**Steps**:

1. Start Minikube cluster:
   ```bash
   minikube start --cpus=4 --memory=8192 --driver=docker
   ```

2. Run setup script:
   ```bash
   ./scripts/setup-minikube.sh --with-monitoring --with-logging
   ```

3. Build and deploy services:
   ```bash
   ./scripts/deploy-local.sh
   ```

4. Verify deployment:
   ```bash
   ./scripts/test-e2e-minikube.sh
   ```

5. Access services:
   ```bash
   # Backend API
   kubectl port-forward svc/backend 8000:8000

   # Grafana
   kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80

   # Loki
   kubectl port-forward -n logging svc/loki-gateway 3100:80
   ```

**Rollback**: Delete Minikube cluster and restart
```bash
minikube delete
```

---

### Deploy to Oracle OKE (Production)

**Purpose**: Deploy application to production OKE cluster

**Prerequisites**:
- OKE cluster created and configured
- kubectl configured for OKE
- OCIR credentials configured
- Docker images built and pushed

**Steps**:

1. Verify cluster access:
   ```bash
   kubectl cluster-info
   kubectl get nodes
   ```

2. Create secrets:
   ```bash
   kubectl create secret generic app-secrets \
     --from-literal=database-url="$DATABASE_URL" \
     --from-literal=better-auth-secret="$BETTER_AUTH_SECRET"
   ```

3. Deploy monitoring stack:
   ```bash
   ./scripts/deploy-monitoring.sh --environment oke
   ```

4. Deploy logging stack:
   ```bash
   ./scripts/deploy-logging.sh --environment oke
   ```

5. Deploy application services:
   ```bash
   helm upgrade --install backend ./helm/backend \
     --values ./helm/backend/values-oke.yaml \
     --set image.tag=$VERSION

   # Repeat for other services
   ```

6. Verify deployment:
   ```bash
   ./scripts/test-e2e-oke.sh
   ```

7. Monitor deployment:
   - Check Grafana dashboards
   - Review logs in Loki
   - Verify metrics in Prometheus

**Rollback**:
```bash
helm rollback backend
helm rollback sync
# Rollback other services
```

---

## Incident Response

### High Error Rate Alert

**Alert**: `HighErrorRate` - Service error rate exceeds 5%

**Severity**: Critical

**Steps**:

1. **Acknowledge alert** in Alertmanager/PagerDuty

2. **Check Grafana dashboard**:
   - Navigate to Service Overview dashboard
   - Identify which service is affected
   - Check error rate trend

3. **Review logs in Loki**:
   ```
   {namespace="default", service="backend", level="ERROR"}
   ```

4. **Check recent deployments**:
   ```bash
   kubectl rollout history deployment/backend
   ```

5. **If recent deployment caused issue**:
   ```bash
   kubectl rollout undo deployment/backend
   ```

6. **Check pod status**:
   ```bash
   kubectl get pods -l app=backend
   kubectl describe pod <pod-name>
   kubectl logs <pod-name>
   ```

7. **Check Dapr sidecar**:
   ```bash
   kubectl logs <pod-name> -c daprd
   ```

8. **Verify database connectivity**:
   ```bash
   kubectl exec -it <pod-name> -- curl http://localhost:8000/health
   ```

9. **Scale up if needed**:
   ```bash
   kubectl scale deployment backend --replicas=5
   ```

10. **Document incident** in post-mortem template

**Escalation**: If issue persists after 15 minutes, escalate to senior engineer

---

### Service Down Alert

**Alert**: `ServiceDown` - Service is not responding

**Severity**: Critical

**Steps**:

1. **Check pod status**:
   ```bash
   kubectl get pods -l app=<service-name>
   ```

2. **If pod is CrashLoopBackOff**:
   ```bash
   kubectl logs <pod-name> --previous
   kubectl describe pod <pod-name>
   ```

3. **Check resource limits**:
   ```bash
   kubectl top pod <pod-name>
   ```

4. **Check events**:
   ```bash
   kubectl get events --sort-by='.lastTimestamp' | grep <pod-name>
   ```

5. **If OOMKilled**:
   - Increase memory limits in Helm values
   - Redeploy service

6. **If ImagePullBackOff**:
   - Verify image exists in registry
   - Check image pull secrets

7. **If persistent issue**:
   - Delete pod to force restart:
     ```bash
     kubectl delete pod <pod-name>
     ```

8. **Monitor recovery** in Grafana

---

### High Memory Usage Alert

**Alert**: `HighMemoryUsage` - Container using >80% of memory limit

**Severity**: Warning

**Steps**:

1. **Check current memory usage**:
   ```bash
   kubectl top pod <pod-name>
   ```

2. **Review memory trends** in Grafana

3. **Check for memory leaks**:
   - Review application logs for unusual patterns
   - Check if memory usage is steadily increasing

4. **If memory leak suspected**:
   - Restart pod:
     ```bash
     kubectl delete pod <pod-name>
     ```
   - Monitor memory usage after restart

5. **If legitimate high usage**:
   - Increase memory limits in Helm values
   - Redeploy service

6. **Long-term fix**:
   - Profile application for memory leaks
   - Optimize memory usage in code

---

### Database Connection Failures

**Alert**: `HighDatabaseErrorRate` - Database queries failing

**Severity**: Critical

**Steps**:

1. **Check database status**:
   - Verify Neon PostgreSQL dashboard
   - Check connection pool status

2. **Check connection string**:
   ```bash
   kubectl get secret app-secrets -o jsonpath='{.data.database-url}' | base64 --decode
   ```

3. **Test database connectivity**:
   ```bash
   kubectl exec -it <pod-name> -- psql $DATABASE_URL -c "SELECT 1"
   ```

4. **Check connection pool exhaustion**:
   - Review logs for "too many connections"
   - Increase connection pool size if needed

5. **Check database performance**:
   - Review slow query logs
   - Check for long-running queries

6. **If database is down**:
   - Contact Neon support
   - Check Neon status page

7. **Temporary mitigation**:
   - Reduce replica count to lower connection load
   - Enable connection pooling if not already enabled

---

## Scaling Operations

### Scale Application Services

**Purpose**: Increase or decrease service replicas

**Horizontal Scaling**:

```bash
# Scale backend to 5 replicas
kubectl scale deployment backend --replicas=5

# Scale sync service to 3 replicas
kubectl scale deployment sync-service --replicas=3

# Verify scaling
kubectl get pods -l app=backend
```

**Using HPA (Horizontal Pod Autoscaler)**:

```bash
# Create HPA
kubectl autoscale deployment backend \
  --cpu-percent=70 \
  --min=2 \
  --max=10

# Check HPA status
kubectl get hpa

# Describe HPA
kubectl describe hpa backend
```

**Vertical Scaling** (change resource limits):

1. Update Helm values:
   ```yaml
   resources:
     requests:
       cpu: 200m
       memory: 512Mi
     limits:
       cpu: 1000m
       memory: 1Gi
   ```

2. Redeploy:
   ```bash
   helm upgrade backend ./helm/backend --values values-oke.yaml
   ```

---

### Scale Kubernetes Cluster

**OKE Node Pool Scaling**:

```bash
# Scale node pool via OCI CLI
oci ce node-pool update \
  --node-pool-id <node-pool-ocid> \
  --size 5

# Verify nodes
kubectl get nodes
```

**Enable Cluster Autoscaler** (if not already enabled):

```bash
# OKE: Configure via OCI Console
# Navigate to: Kubernetes Clusters > Node Pools > Edit
# Enable "Autoscale" and set min/max nodes
```

---

## Backup and Restore

### Backup Application State

**Database Backup** (Neon PostgreSQL):

Neon provides automated backups (7-day retention by default).

To create manual backup:
1. Navigate to Neon Console
2. Select your project
3. Go to "Backups" tab
4. Click "Create Backup"

**Kubernetes Resources Backup** (using Velero):

```bash
# Install Velero (if not installed)
velero install --provider <cloud-provider>

# Create backup
velero backup create todoapp-backup \
  --include-namespaces default,monitoring,logging

# List backups
velero backup get

# Check backup status
velero backup describe todoapp-backup
```

---

### Restore from Backup

**Restore Database**:

1. Navigate to Neon Console
2. Select backup to restore
3. Click "Restore"
4. Choose restore point
5. Update DATABASE_URL in secrets if needed

**Restore Kubernetes Resources**:

```bash
# Restore from Velero backup
velero restore create --from-backup todoapp-backup

# Check restore status
velero restore describe <restore-name>

# Verify pods are running
kubectl get pods --all-namespaces
```

---

## Troubleshooting

### Pod Stuck in Pending State

**Symptoms**: Pod shows "Pending" status for extended period

**Diagnosis**:

```bash
kubectl describe pod <pod-name>
```

**Common Causes**:

1. **Insufficient resources**:
   - Check node capacity: `kubectl describe nodes`
   - Solution: Scale cluster or reduce resource requests

2. **PVC not bound**:
   - Check PVC status: `kubectl get pvc`
   - Solution: Verify storage class exists

3. **Image pull issues**:
   - Check events for ImagePullBackOff
   - Solution: Verify image exists and pull secrets are configured

---

### Dapr Sidecar Not Injecting

**Symptoms**: Pod doesn't have Dapr sidecar container

**Diagnosis**:

```bash
kubectl get pods <pod-name> -o jsonpath='{.spec.containers[*].name}'
```

**Solutions**:

1. **Check Dapr annotations**:
   ```bash
   kubectl get pod <pod-name> -o yaml | grep dapr.io
   ```

2. **Verify Dapr is installed**:
   ```bash
   kubectl get pods -n dapr-system
   ```

3. **Check sidecar injector logs**:
   ```bash
   kubectl logs -n dapr-system -l app=dapr-sidecar-injector
   ```

4. **Recreate pod**:
   ```bash
   kubectl delete pod <pod-name>
   ```

---

### Metrics Not Appearing in Prometheus

**Symptoms**: Service metrics not visible in Prometheus

**Diagnosis**:

1. **Check /metrics endpoint**:
   ```bash
   kubectl port-forward <pod-name> 8000:8000
   curl http://localhost:8000/metrics
   ```

2. **Check Prometheus targets**:
   - Navigate to Prometheus UI
   - Go to Status > Targets
   - Verify service is listed and "UP"

3. **Check ServiceMonitor**:
   ```bash
   kubectl get servicemonitor -n monitoring
   kubectl describe servicemonitor <name> -n monitoring
   ```

**Solutions**:

1. **Verify service has correct labels**
2. **Check ServiceMonitor selector matches service labels**
3. **Restart Prometheus operator**:
   ```bash
   kubectl delete pod -n monitoring -l app=prometheus-operator
   ```

---

## Maintenance Tasks

### Update Kubernetes Cluster

**Frequency**: Quarterly or as needed for security patches

**Steps**:

1. **Check current version**:
   ```bash
   kubectl version --short
   ```

2. **Review release notes** for target version

3. **Backup cluster state**:
   ```bash
   velero backup create pre-upgrade-backup
   ```

4. **Upgrade cluster** (OKE):
   ```bash
   oci ce cluster update \
     --cluster-id <cluster-ocid> \
     --kubernetes-version v1.29.0
   ```

5. **Upgrade node pools**:
   ```bash
   oci ce node-pool update \
     --node-pool-id <node-pool-ocid> \
     --kubernetes-version v1.29.0
   ```

6. **Verify upgrade**:
   ```bash
   kubectl get nodes
   kubectl get pods --all-namespaces
   ```

---

### Rotate Secrets

**Frequency**: Quarterly

**Steps**:

1. **Generate new secrets**

2. **Update secrets in Kubernetes**:
   ```bash
   kubectl create secret generic app-secrets \
     --from-literal=database-url="$NEW_DATABASE_URL" \
     --dry-run=client -o yaml | kubectl apply -f -
   ```

3. **Restart pods to pick up new secrets**:
   ```bash
   kubectl rollout restart deployment/backend
   kubectl rollout restart deployment/sync-service
   ```

4. **Verify services are healthy**:
   ```bash
   kubectl get pods
   ./scripts/test-e2e-oke.sh
   ```

---

### Clean Up Old Resources

**Frequency**: Monthly

**Steps**:

1. **Remove old Docker images**:
   ```bash
   # OCI: Use OCI Console to delete old images
   # Or use OCI CLI
   oci artifacts container image delete --image-id <image-ocid>
   ```

2. **Clean up old Helm releases**:
   ```bash
   helm list --all-namespaces
   helm uninstall <old-release>
   ```

3. **Remove unused PVCs**:
   ```bash
   kubectl get pvc --all-namespaces
   kubectl delete pvc <unused-pvc>
   ```

4. **Clean up completed jobs**:
   ```bash
   kubectl delete jobs --field-selector status.successful=1
   ```

---

## Emergency Contacts

- **On-Call Engineer**: oncall@todoapp.example.com
- **Platform Team**: platform@todoapp.example.com
- **Database Team**: database@todoapp.example.com
- **Neon Support**: support@neon.tech
- **OCI Support**: https://support.oracle.com
