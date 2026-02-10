# Metrics Specification

**Feature**: 009-monitoring-multicloud
**Date**: 2026-02-10
**Purpose**: Define key metrics to monitor across all microservices

## Overview

This document specifies the metrics that will be collected by Prometheus and visualized in Grafana dashboards. All metrics follow Prometheus naming conventions and best practices.

## Metric Naming Convention

```
<namespace>_<subsystem>_<name>_<unit>

Examples:
- http_requests_total (counter)
- http_request_duration_seconds (histogram)
- websocket_connections_active (gauge)
```

## Service Metrics

### 1. Backend API Service

#### HTTP Request Metrics (FastAPI built-in)
```
# Total HTTP requests
http_requests_total{method="GET|POST|PUT|DELETE", path="/api/tasks", status="200|400|500"}

# HTTP request duration
http_request_duration_seconds{method="GET|POST|PUT|DELETE", path="/api/tasks"}
  - Type: Histogram
  - Buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

# HTTP requests in progress
http_requests_in_progress{method="GET|POST|PUT|DELETE", path="/api/tasks"}
  - Type: Gauge
```

#### Application Metrics (Custom)
```
# Task operations
tasks_created_total{user_id="*"}
  - Type: Counter
  - Description: Total tasks created

tasks_updated_total{user_id="*"}
  - Type: Counter
  - Description: Total tasks updated

tasks_deleted_total{user_id="*"}
  - Type: Counter
  - Description: Total tasks deleted

# Database operations
database_queries_total{operation="select|insert|update|delete", table="tasks|users"}
  - Type: Counter
  - Description: Total database queries

database_query_duration_seconds{operation="select|insert|update|delete", table="tasks|users"}
  - Type: Histogram
  - Buckets: [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
```

### 2. Recurring Task Engine Service

```
# Cron job executions
recurring_tasks_processed_total{status="success|failure"}
  - Type: Counter
  - Description: Total recurring tasks processed

recurring_tasks_created_total
  - Type: Counter
  - Description: Total new task instances created from recurring tasks

recurring_task_processing_duration_seconds
  - Type: Histogram
  - Buckets: [0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
  - Description: Time to process all recurring tasks in one cron cycle
```

### 3. Notification Service

```
# Reminder operations
reminders_scheduled_total{user_id="*"}
  - Type: Counter
  - Description: Total reminders scheduled

reminders_sent_total{channel="email|push|websocket", status="success|failure"}
  - Type: Counter
  - Description: Total reminders sent

reminder_delivery_duration_seconds{channel="email|push|websocket"}
  - Type: Histogram
  - Buckets: [0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
  - Description: Time to deliver a reminder
```

### 4. Sync Service (WebSocket)

```
# WebSocket connections
websocket_connections_active{user_id="*"}
  - Type: Gauge
  - Description: Active WebSocket connections

websocket_connections_total{status="connected|disconnected"}
  - Type: Counter
  - Description: Total WebSocket connection events

websocket_messages_sent_total{event_type="task.created|task.updated|task.deleted"}
  - Type: Counter
  - Description: Total WebSocket messages sent to clients

websocket_message_delivery_duration_seconds
  - Type: Histogram
  - Buckets: [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5]
  - Description: Time to deliver a message to a WebSocket client
```

### 5. Audit Service

```
# Audit log operations
audit_logs_written_total{event_type="task.created|task.updated|task.deleted"}
  - Type: Counter
  - Description: Total audit logs written

audit_log_write_duration_seconds
  - Type: Histogram
  - Buckets: [0.001, 0.005, 0.01, 0.025, 0.05, 0.1]
  - Description: Time to write an audit log entry
```

## Dapr Metrics

Dapr sidecars automatically expose metrics on port 9090. Key metrics include:

### Dapr HTTP Metrics
```
dapr_http_server_request_count{app_id="backend|recurring-task|notification|sync|audit", method="GET|POST", path="/v1.0/publish/*"}
  - Type: Counter
  - Description: Total HTTP requests to Dapr sidecar

dapr_http_server_request_duration_ms{app_id="*", method="*", path="*"}
  - Type: Histogram
  - Description: Dapr HTTP request duration
```

### Dapr Pub/Sub Metrics
```
dapr_component_pubsub_ingress_count{app_id="*", component="pubsub", topic="task.created|task.updated|reminder.due"}
  - Type: Counter
  - Description: Messages published to Kafka via Dapr

dapr_component_pubsub_egress_count{app_id="*", component="pubsub", topic="*"}
  - Type: Counter
  - Description: Messages consumed from Kafka via Dapr
```

### Dapr State Store Metrics
```
dapr_component_state_ingress_count{app_id="*", component="statestore", operation="get|set|delete"}
  - Type: Counter
  - Description: State store operations via Dapr
```

## Kafka Metrics

Kafka/Redpanda metrics are exposed by the Kafka exporter (if deployed) or via JMX.

### Consumer Lag (Critical)
```
kafka_consumer_lag_messages{consumer_group="recurring-task-consumer|notification-consumer|audit-consumer|sync-consumer", topic="task.created|task.updated|reminder.due", partition="0"}
  - Type: Gauge
  - Description: Number of messages behind the latest offset
  - Alert Threshold: > 1000 messages
```

### Topic Metrics
```
kafka_topic_partition_current_offset{topic="*", partition="*"}
  - Type: Gauge
  - Description: Current offset for a topic partition

kafka_topic_partition_oldest_offset{topic="*", partition="*"}
  - Type: Gauge
  - Description: Oldest offset for a topic partition
```

## System Metrics (Kubernetes)

These metrics are automatically collected by kube-prometheus-stack:

### Pod Metrics
```
container_cpu_usage_seconds_total{pod="backend-*|recurring-task-*|notification-*|sync-*|audit-*"}
  - Type: Counter
  - Description: CPU usage per pod

container_memory_usage_bytes{pod="*"}
  - Type: Gauge
  - Description: Memory usage per pod

kube_pod_container_status_restarts_total{pod="*"}
  - Type: Counter
  - Description: Pod restart count (indicator of crashes)
```

### Node Metrics
```
node_cpu_seconds_total{mode="idle|user|system"}
  - Type: Counter
  - Description: Node CPU usage

node_memory_MemAvailable_bytes
  - Type: Gauge
  - Description: Available memory on node
```

## Alerting Rules (Out of Scope for Spec 9)

While alerting is out of scope for Spec 9, the following metrics are critical for future alerting:

- `kafka_consumer_lag_messages > 1000` - Consumer lag too high
- `http_request_duration_seconds{quantile="0.95"} > 1.0` - API latency too high
- `kube_pod_container_status_restarts_total > 5` - Pod restarting frequently
- `websocket_connections_active > 1000` - Too many WebSocket connections

## Grafana Dashboard Panels

The following panels will be included in Grafana dashboards:

1. **Overview Dashboard**
   - Total requests per service (counter)
   - Request latency p50, p95, p99 (histogram quantiles)
   - Active WebSocket connections (gauge)
   - Kafka consumer lag (gauge)

2. **Service Health Dashboard**
   - Pod CPU usage (gauge)
   - Pod memory usage (gauge)
   - Pod restart count (counter)
   - HTTP error rate (counter ratio)

3. **Event Processing Dashboard**
   - Events published per topic (counter)
   - Events consumed per topic (counter)
   - Event processing latency (histogram)
   - Consumer lag per topic (gauge)

4. **WebSocket Dashboard**
   - Active connections (gauge)
   - Messages sent per event type (counter)
   - Message delivery latency (histogram)
   - Connection errors (counter)

## Implementation Notes

- All custom metrics will be exposed via Prometheus client libraries (Python: `prometheus-client`)
- Metrics endpoints: `http://<service>:8000/metrics` (FastAPI services)
- Dapr metrics: `http://localhost:9090/metrics` (Dapr sidecar)
- Scrape interval: 15 seconds (configurable in Prometheus)
- Retention: 15 days (configurable in Prometheus)

## References

- Prometheus best practices: https://prometheus.io/docs/practices/naming/
- Dapr metrics: https://docs.dapr.io/operations/observability/metrics/
- FastAPI metrics: https://github.com/trallnag/prometheus-fastapi-instrumentator
