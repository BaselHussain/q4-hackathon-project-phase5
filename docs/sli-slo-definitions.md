# Service Level Indicators (SLIs) and Service Level Objectives (SLOs)

This document defines the SLIs and SLOs for the Todo App production deployment.

## Overview

**SLI (Service Level Indicator)**: A quantitative measure of service reliability
**SLO (Service Level Objective)**: Target value or range for an SLI
**SLA (Service Level Agreement)**: Contractual commitment to customers (typically SLO - error budget)

## Error Budget

Error budget = 100% - SLO

Example: If SLO is 99.9% availability, error budget is 0.1% (43.2 minutes/month)

---

## 1. Availability SLIs/SLOs

### Backend API Availability

**SLI Definition**: Percentage of successful HTTP requests (non-5xx responses)

**Measurement**:
```promql
sum(rate(http_requests_total{status!~"5.."}[30d]))
/
sum(rate(http_requests_total[30d]))
```

**SLO**: 99.9% availability over 30-day window

**Error Budget**: 0.1% (43.2 minutes/month)

**Alerting Threshold**:
- Warning: 99.95% (half error budget consumed)
- Critical: 99.9% (error budget exhausted)

---

### WebSocket Service Availability

**SLI Definition**: Percentage of successful WebSocket connections

**Measurement**:
```promql
sum(rate(websocket_connections_total{status="success"}[30d]))
/
sum(rate(websocket_connections_total[30d]))
```

**SLO**: 99.5% successful connections over 30-day window

**Error Budget**: 0.5% (3.6 hours/month)

**Alerting Threshold**:
- Warning: 99.75%
- Critical: 99.5%

---

### Microservices Availability

**SLI Definition**: Percentage of time service pods are ready

**Measurement**:
```promql
avg_over_time(up{job=~"backend|sync-service|recurring-task-service|notification-service|audit-service"}[30d])
```

**SLO**: 99.9% uptime over 30-day window

**Error Budget**: 0.1% (43.2 minutes/month)

---

## 2. Latency SLIs/SLOs

### API Response Time (p95)

**SLI Definition**: 95th percentile of HTTP request duration

**Measurement**:
```promql
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)
)
```

**SLO**: 95% of requests complete within 500ms

**Error Budget**: 5% of requests can exceed 500ms

**Alerting Threshold**:
- Warning: p95 > 750ms for 5 minutes
- Critical: p95 > 1000ms for 5 minutes

---

### API Response Time (p99)

**SLI Definition**: 99th percentile of HTTP request duration

**Measurement**:
```promql
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)
)
```

**SLO**: 99% of requests complete within 1000ms

**Error Budget**: 1% of requests can exceed 1000ms

**Alerting Threshold**:
- Warning: p99 > 1500ms for 5 minutes
- Critical: p99 > 2000ms for 5 minutes

---

### Database Query Latency (p95)

**SLI Definition**: 95th percentile of database query duration

**Measurement**:
```promql
histogram_quantile(0.95,
  sum(rate(database_query_duration_seconds_bucket[5m])) by (le, operation)
)
```

**SLO**: 95% of queries complete within 100ms

**Error Budget**: 5% of queries can exceed 100ms

**Alerting Threshold**:
- Warning: p95 > 200ms for 5 minutes
- Critical: p95 > 500ms for 5 minutes

---

### WebSocket Message Delivery Latency (p95)

**SLI Definition**: 95th percentile of WebSocket message delivery time

**Measurement**:
```promql
histogram_quantile(0.95,
  sum(rate(websocket_message_delivery_duration_seconds_bucket[5m])) by (le)
)
```

**SLO**: 95% of messages delivered within 100ms

**Error Budget**: 5% of messages can exceed 100ms

**Alerting Threshold**:
- Warning: p95 > 200ms for 5 minutes
- Critical: p95 > 500ms for 5 minutes

---

## 3. Throughput SLIs/SLOs

### API Request Rate

**SLI Definition**: Number of HTTP requests per second

**Measurement**:
```promql
sum(rate(http_requests_total[5m]))
```

**SLO**: System handles at least 100 requests/second

**Capacity Planning**: Scale when sustained load exceeds 80 req/s

**Alerting Threshold**:
- Warning: > 80 req/s for 10 minutes (capacity planning)
- Critical: > 100 req/s for 5 minutes (overload)

---

### Event Processing Rate

**SLI Definition**: Number of events processed per second

**Measurement**:
```promql
sum(rate(dapr_component_pubsub_ingress_count[5m]))
```

**SLO**: System processes at least 50 events/second

**Capacity Planning**: Scale when sustained load exceeds 40 events/s

---

## 4. Data Durability SLIs/SLOs

### Audit Log Write Success Rate

**SLI Definition**: Percentage of successful audit log writes

**Measurement**:
```promql
sum(rate(audit_logs_written_total{status="success"}[30d]))
/
sum(rate(audit_logs_written_total[30d]))
```

**SLO**: 99.99% of audit logs successfully written

**Error Budget**: 0.01% (4.3 minutes/month)

**Alerting Threshold**:
- Warning: < 99.995%
- Critical: < 99.99%

**Rationale**: Audit logs are critical for compliance; very low tolerance for loss

---

### Event Delivery Success Rate

**SLI Definition**: Percentage of events successfully published to Kafka

**Measurement**:
```promql
sum(rate(dapr_component_pubsub_egress_count{success="true"}[30d]))
/
sum(rate(dapr_component_pubsub_egress_count[30d]))
```

**SLO**: 99.9% of events successfully delivered

**Error Budget**: 0.1%

**Alerting Threshold**:
- Warning: < 99.95%
- Critical: < 99.9%

---

## 5. Correctness SLIs/SLOs

### Database Transaction Success Rate

**SLI Definition**: Percentage of successful database transactions

**Measurement**:
```promql
sum(rate(database_queries_total{status="success"}[30d]))
/
sum(rate(database_queries_total[30d]))
```

**SLO**: 99.95% of transactions succeed

**Error Budget**: 0.05%

**Alerting Threshold**:
- Warning: < 99.975%
- Critical: < 99.95%

---

### State Store Operation Success Rate

**SLI Definition**: Percentage of successful Dapr state store operations

**Measurement**:
```promql
sum(rate(dapr_component_state_operation_count{success="true"}[30d]))
/
sum(rate(dapr_component_state_operation_count[30d]))
```

**SLO**: 99.9% of operations succeed

**Error Budget**: 0.1%

---

## 6. Freshness SLIs/SLOs

### Event Processing Lag

**SLI Definition**: Time between event publication and consumption

**Measurement**:
```promql
kafka_consumer_lag
```

**SLO**: 95% of events processed within 5 seconds

**Error Budget**: 5% of events can take longer than 5 seconds

**Alerting Threshold**:
- Warning: Lag > 1000 messages for 5 minutes
- Critical: Lag > 5000 messages for 5 minutes

---

### Log Ingestion Lag

**SLI Definition**: Time between log generation and availability in Loki

**Measurement**: Manual sampling (check Loki query results)

**SLO**: 95% of logs available within 30 seconds

**Error Budget**: 5% of logs can take longer than 30 seconds

---

## 7. Capacity SLIs/SLOs

### CPU Utilization

**SLI Definition**: Average CPU utilization across all pods

**Measurement**:
```promql
avg(rate(container_cpu_usage_seconds_total{container!=""}[5m]))
```

**SLO**: Average CPU utilization < 70%

**Capacity Planning**: Scale when sustained utilization > 60%

**Alerting Threshold**:
- Warning: > 70% for 10 minutes
- Critical: > 85% for 5 minutes

---

### Memory Utilization

**SLI Definition**: Average memory utilization across all pods

**Measurement**:
```promql
avg(
  container_memory_working_set_bytes{container!=""}
  /
  container_spec_memory_limit_bytes{container!=""}
)
```

**SLO**: Average memory utilization < 70%

**Capacity Planning**: Scale when sustained utilization > 60%

**Alerting Threshold**:
- Warning: > 70% for 10 minutes
- Critical: > 85% for 5 minutes

---

### Storage Utilization

**SLI Definition**: Percentage of persistent volume capacity used

**Measurement**:
```promql
(
  kubelet_volume_stats_used_bytes
  /
  kubelet_volume_stats_capacity_bytes
) * 100
```

**SLO**: Storage utilization < 80%

**Capacity Planning**: Expand storage when utilization > 70%

**Alerting Threshold**:
- Warning: > 80% for 10 minutes
- Critical: > 90% for 5 minutes

---

## SLO Monitoring Dashboard

Create a dedicated Grafana dashboard to track all SLOs:

### Dashboard Panels

1. **Availability Overview**
   - Backend API availability (30-day rolling)
   - WebSocket availability (30-day rolling)
   - Microservices uptime (30-day rolling)

2. **Latency Overview**
   - API p95/p99 response times
   - Database query p95 latency
   - WebSocket message delivery p95 latency

3. **Error Budget Burn Rate**
   - Current error budget remaining
   - Burn rate (how fast error budget is being consumed)
   - Projected error budget exhaustion date

4. **Throughput Metrics**
   - API request rate
   - Event processing rate
   - Database query rate

5. **Data Durability**
   - Audit log write success rate
   - Event delivery success rate

6. **Capacity Metrics**
   - CPU utilization
   - Memory utilization
   - Storage utilization

---

## Error Budget Policy

### When Error Budget is Exhausted

1. **Freeze feature releases** until error budget is restored
2. **Focus on reliability improvements**:
   - Fix bugs causing errors
   - Improve monitoring and alerting
   - Conduct incident retrospectives
3. **Increase testing** before releases
4. **Review and update SLOs** if consistently unachievable

### When Error Budget is Healthy (>50% remaining)

1. **Continue normal feature development**
2. **Take calculated risks** with new features
3. **Invest in innovation**

### When Error Budget is Low (10-50% remaining)

1. **Slow down feature releases**
2. **Increase testing rigor**
3. **Focus on stability improvements**
4. **Conduct proactive incident reviews**

---

## SLO Review Process

### Monthly Review

- Review SLO compliance for past month
- Analyze error budget consumption
- Identify trends and patterns
- Adjust alerting thresholds if needed

### Quarterly Review

- Evaluate if SLOs are appropriate
- Adjust SLOs based on business needs
- Update error budget policies
- Review capacity planning

### Annual Review

- Comprehensive SLO assessment
- Align SLOs with business objectives
- Update SLA commitments (if applicable)
- Set SLO targets for next year

---

## Reporting

### Weekly SLO Report

- SLO compliance percentage
- Error budget remaining
- Top 3 incidents affecting SLOs
- Action items for next week

### Monthly SLO Report

- Detailed SLO compliance analysis
- Error budget trends
- Incident summary and impact
- Capacity planning recommendations
- Reliability improvements implemented

---

## References

- [Google SRE Book - Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)
- [Implementing SLOs](https://sre.google/workbook/implementing-slos/)
- [The Art of SLOs](https://sre.google/resources/practices-and-processes/art-of-slos/)
