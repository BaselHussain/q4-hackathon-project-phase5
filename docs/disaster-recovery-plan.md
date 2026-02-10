# Disaster Recovery Plan

This document outlines the disaster recovery (DR) procedures for the Todo App production deployment.

## Overview

**Recovery Time Objective (RTO)**: 4 hours
**Recovery Point Objective (RPO)**: 1 hour
**Last Updated**: 2024-01-15
**Next Review**: 2024-04-15

---

## Disaster Scenarios

### 1. Complete Cluster Failure

**Scenario**: Entire Kubernetes cluster becomes unavailable

**Likelihood**: Low
**Impact**: Critical
**RTO**: 4 hours
**RPO**: 1 hour

**Recovery Procedure**: See [Cluster Failure Recovery](#cluster-failure-recovery)

---

### 2. Database Failure

**Scenario**: Neon PostgreSQL database becomes unavailable or corrupted

**Likelihood**: Very Low
**Impact**: Critical
**RTO**: 2 hours
**RPO**: 1 hour

**Recovery Procedure**: See [Database Recovery](#database-recovery)

---

### 3. Region/Zone Outage

**Scenario**: Cloud provider region or availability zone becomes unavailable

**Likelihood**: Low
**Impact**: Critical
**RTO**: 4 hours
**RPO**: 1 hour

**Recovery Procedure**: See [Region Failover](#region-failover)

---

### 4. Data Corruption

**Scenario**: Application bug causes data corruption in database

**Likelihood**: Low
**Impact**: High
**RTO**: 2 hours
**RPO**: 1 hour

**Recovery Procedure**: See [Data Corruption Recovery](#data-corruption-recovery)

---

### 5. Security Breach

**Scenario**: Unauthorized access to systems or data

**Likelihood**: Low
**Impact**: Critical
**RTO**: Immediate containment, 8 hours full recovery
**RPO**: N/A

**Recovery Procedure**: See [Security Incident Response](#security-incident-response)

---

## Recovery Procedures

### Cluster Failure Recovery

**Objective**: Restore Kubernetes cluster and all services

**Prerequisites**:
- Access to cloud provider console (OCI)
- Backup of cluster configuration
- Backup of application state (Velero)
- Container images in registry

**Steps**:

1. **Assess Damage** (15 minutes)
   ```bash
   # Try to access cluster
   kubectl cluster-info

   # Check OCI Console for cluster status
   oci ce cluster get --cluster-id <cluster-ocid>
   ```

2. **Declare Disaster** (5 minutes)
   - Notify stakeholders
   - Activate DR team
   - Update status page

3. **Create New Cluster** (30 minutes)
   ```bash
   # Create new OKE cluster
   oci ce cluster create \
     --compartment-id <compartment-ocid> \
     --name todoapp-cluster-dr \
     --kubernetes-version v1.28.2 \
     --vcn-id <vcn-ocid>

   # Create node pool
   oci ce node-pool create \
     --cluster-id <new-cluster-ocid> \
     --name todoapp-nodes \
     --node-shape VM.Standard.E4.Flex \
     --size 3

   # Get kubeconfig
   oci ce cluster create-kubeconfig \
     --cluster-id <new-cluster-ocid> \
     --file ~/.kube/config-dr

   export KUBECONFIG=~/.kube/config-dr
   ```

4. **Install Dapr** (10 minutes)
   ```bash
   dapr init -k --runtime-version 1.12.0 --wait
   ```

5. **Restore from Backup** (60 minutes)
   ```bash
   # Install Velero
   velero install --provider oci

   # List available backups
   velero backup get

   # Restore latest backup
   velero restore create --from-backup <latest-backup-name>

   # Wait for restore to complete
   velero restore describe <restore-name>
   ```

6. **Restore Secrets** (10 minutes)
   ```bash
   # Recreate secrets from secure storage
   kubectl create secret generic app-secrets \
     --from-literal=database-url="$DATABASE_URL" \
     --from-literal=better-auth-secret="$BETTER_AUTH_SECRET"
   ```

7. **Deploy Monitoring Stack** (20 minutes)
   ```bash
   ./scripts/deploy-monitoring.sh --environment oke
   ```

8. **Deploy Logging Stack** (20 minutes)
   ```bash
   ./scripts/deploy-logging.sh --environment oke
   ```

9. **Verify Services** (30 minutes)
   ```bash
   # Check all pods are running
   kubectl get pods --all-namespaces

   # Run E2E tests
   ./scripts/test-e2e-oke.sh

   # Verify metrics collection
   # Verify log aggregation
   ```

10. **Update DNS** (10 minutes)
    - Point DNS to new load balancer IP
    - Wait for DNS propagation

11. **Verify Recovery** (30 minutes)
    - Test all critical user flows
    - Verify data integrity
    - Check monitoring dashboards
    - Review logs for errors

12. **Post-Recovery** (30 minutes)
    - Update status page
    - Notify stakeholders
    - Document incident
    - Schedule post-mortem

**Total Estimated Time**: 3.5 hours

---

### Database Recovery

**Objective**: Restore database from backup

**Prerequisites**:
- Access to Neon Console
- Database backup available
- Application can tolerate brief downtime

**Steps**:

1. **Assess Database State** (5 minutes)
   ```bash
   # Test database connectivity
   psql $DATABASE_URL -c "SELECT 1"

   # Check Neon Console for database status
   ```

2. **Identify Latest Good Backup** (5 minutes)
   - Navigate to Neon Console
   - Go to Backups tab
   - Identify latest backup before corruption/failure

3. **Create Restore Point** (10 minutes)
   - In Neon Console, select backup
   - Click "Restore"
   - Choose restore point
   - Create new branch or restore to main

4. **Update Connection String** (5 minutes)
   ```bash
   # Update DATABASE_URL secret
   kubectl create secret generic app-secrets \
     --from-literal=database-url="$NEW_DATABASE_URL" \
     --dry-run=client -o yaml | kubectl apply -f -
   ```

5. **Restart Application Pods** (10 minutes)
   ```bash
   kubectl rollout restart deployment/backend
   kubectl rollout restart deployment/recurring-task-service
   kubectl rollout restart deployment/notification-service
   kubectl rollout restart deployment/audit-service
   ```

6. **Verify Data Integrity** (30 minutes)
   - Run data validation queries
   - Check recent transactions
   - Verify user data is intact

7. **Monitor for Issues** (30 minutes)
   - Watch error logs
   - Monitor database metrics
   - Check application health

**Total Estimated Time**: 1.5 hours

---

### Region Failover

**Objective**: Failover to secondary region

**Prerequisites**:
- Multi-region deployment configured
- Database replication to secondary region
- DNS failover configured

**Steps**:

1. **Assess Primary Region** (10 minutes)
   - Verify region is truly unavailable
   - Check cloud provider status page

2. **Activate Secondary Region** (5 minutes)
   ```bash
   # Switch kubectl context to secondary region
   kubectl config use-context oke-secondary

   # Verify cluster is healthy
   kubectl get nodes
   kubectl get pods --all-namespaces
   ```

3. **Promote Secondary Database** (15 minutes)
   - In Neon Console, promote read replica to primary
   - Update DATABASE_URL to point to new primary

4. **Update DNS** (10 minutes)
   - Update DNS records to point to secondary region load balancer
   - Or trigger DNS failover if automated

5. **Verify Services** (30 minutes)
   - Run E2E tests in secondary region
   - Verify all services are operational
   - Check data replication lag

6. **Monitor** (ongoing)
   - Watch for any issues in secondary region
   - Monitor primary region for recovery

**Total Estimated Time**: 1 hour

**Failback Procedure** (when primary region recovers):
1. Verify primary region is stable
2. Sync data from secondary to primary
3. Update DNS to point back to primary
4. Monitor for issues

---

### Data Corruption Recovery

**Objective**: Restore clean data from backup

**Prerequisites**:
- Database backup available
- Ability to identify corruption scope
- Maintenance window scheduled

**Steps**:

1. **Identify Corruption Scope** (30 minutes)
   ```sql
   -- Run queries to identify affected data
   SELECT * FROM tasks WHERE updated_at > '2024-01-15 10:00:00';

   -- Check audit logs for suspicious activity
   SELECT * FROM audit_logs WHERE event_type = 'task.updated'
     AND timestamp > '2024-01-15 10:00:00';
   ```

2. **Stop Writes to Affected Tables** (10 minutes)
   ```bash
   # Scale down services that write to affected tables
   kubectl scale deployment backend --replicas=0
   ```

3. **Export Current Data** (15 minutes)
   ```bash
   # Export current state for forensics
   pg_dump $DATABASE_URL -t tasks > tasks_corrupted.sql
   ```

4. **Restore from Backup** (30 minutes)
   - Follow [Database Recovery](#database-recovery) procedure
   - Restore to point before corruption

5. **Replay Valid Transactions** (60 minutes)
   ```sql
   -- Identify valid transactions from audit logs
   -- Manually replay or use script to replay
   ```

6. **Verify Data Integrity** (30 minutes)
   - Run data validation queries
   - Compare with audit logs
   - Verify user-reported issues are resolved

7. **Resume Normal Operations** (10 minutes)
   ```bash
   # Scale services back up
   kubectl scale deployment backend --replicas=3
   ```

8. **Root Cause Analysis** (ongoing)
   - Identify what caused corruption
   - Implement fixes to prevent recurrence

**Total Estimated Time**: 3 hours

---

### Security Incident Response

**Objective**: Contain breach, assess damage, restore security

**Prerequisites**:
- Security incident response team activated
- Access to all system logs
- Ability to isolate affected systems

**Steps**:

1. **Immediate Containment** (15 minutes)
   ```bash
   # Isolate affected pods
   kubectl label pod <affected-pod> quarantine=true

   # Update network policies to block traffic
   kubectl apply -f network-policy-lockdown.yaml

   # Rotate all credentials immediately
   ```

2. **Assess Scope** (60 minutes)
   - Review audit logs
   - Check access logs
   - Identify compromised systems
   - Determine data accessed

3. **Preserve Evidence** (30 minutes)
   ```bash
   # Export logs for forensics
   kubectl logs <affected-pod> > incident-logs.txt

   # Take snapshots of affected systems
   # Do not delete anything yet
   ```

4. **Eradicate Threat** (60 minutes)
   - Remove malicious code/backdoors
   - Patch vulnerabilities
   - Update security rules

5. **Restore from Clean Backup** (120 minutes)
   - Follow cluster recovery procedure
   - Use backup from before breach
   - Verify no malicious code in backup

6. **Strengthen Security** (ongoing)
   - Implement additional security controls
   - Update security policies
   - Conduct security audit

7. **Notify Stakeholders** (30 minutes)
   - Notify affected users (if data breach)
   - Report to authorities (if required)
   - Update status page

8. **Post-Incident Review** (ongoing)
   - Conduct thorough security review
   - Document lessons learned
   - Implement preventive measures

**Total Estimated Time**: 8+ hours

---

## Backup Strategy

### Automated Backups

**Database (Neon PostgreSQL)**:
- Frequency: Continuous (point-in-time recovery)
- Retention: 7 days (default), 30 days (production)
- Location: Neon managed storage

**Kubernetes Resources (Velero)**:
- Frequency: Daily at 2:00 AM UTC
- Retention: 30 days
- Location: OCI Object Storage
- Includes: All namespaces (default, monitoring, logging)

**Container Images**:
- Retention: All tagged versions
- Location: OCIR (Oracle Container Registry)

### Manual Backups

Create manual backup before:
- Major deployments
- Database schema changes
- Configuration changes

```bash
# Create manual Velero backup
velero backup create manual-backup-$(date +%Y%m%d-%H%M%S) \
  --include-namespaces default,monitoring,logging
```

---

## Testing DR Procedures

### Quarterly DR Drill

**Objective**: Validate DR procedures and team readiness

**Schedule**: First Saturday of each quarter, 10:00 AM UTC

**Procedure**:
1. Announce DR drill to team
2. Simulate disaster scenario
3. Execute recovery procedure
4. Document time taken for each step
5. Identify gaps and improvements
6. Update DR plan

**Success Criteria**:
- Recovery completed within RTO
- All services operational
- Data integrity verified
- Team followed procedures correctly

---

## Contact Information

### DR Team

- **DR Coordinator**: [Name] - [Phone] - [Email]
- **Engineering Lead**: [Name] - [Phone] - [Email]
- **Database Admin**: [Name] - [Phone] - [Email]
- **Security Lead**: [Name] - [Phone] - [Email]

### Vendor Support

- **Neon Support**: support@neon.tech
- **Oracle Support**: https://support.oracle.com
- **Dapr Community**: https://discord.gg/dapr

---

## Document Control

**Version**: 1.0
**Last Updated**: 2024-01-15
**Next Review**: 2024-04-15
**Owner**: Platform Team
**Approved By**: [Engineering Manager]
