# Data Model: Monitoring, Logging, and Multi-Cloud Deployment

**Feature**: 009-monitoring-multicloud
**Date**: 2026-02-10
**Status**: N/A - Infrastructure Feature

## Overview

This feature focuses on observability infrastructure (monitoring and logging) and does not introduce new database entities or modify existing data models. All data models for the application services were defined in previous specs:

- **Spec 1**: Core todo entities (tasks, users)
- **Spec 7**: Advanced todo features (recurring tasks, tags, priorities)
- **Spec 8**: Event-driven architecture (audit logs)

## Observability Data

While this feature doesn't modify application data models, it does define the structure of observability data:

### 1. Metrics Data (Prometheus)

Metrics are time-series data collected by Prometheus. No persistent storage schema is needed as Prometheus manages its own TSDB (Time Series Database).

**Key Metric Types**:
- Counter: Monotonically increasing values (e.g., total requests)
- Gauge: Values that can go up or down (e.g., active connections)
- Histogram: Distribution of values (e.g., request latency)
- Summary: Similar to histogram with quantiles

**Metric Naming Convention**:
```
<namespace>_<subsystem>_<name>_<unit>

Examples:
- http_requests_total
- dapr_http_server_request_duration_seconds
- kafka_consumer_lag_messages
- websocket_connections_active
```

### 2. Log Data (Loki)

Logs are stored in Loki with labels for indexing and searching. The log format is defined in contracts/log-format.json.

**Log Labels** (indexed by Loki):
- `service`: Service name (backend, recurring-task, notification, sync, audit)
- `level`: Log level (debug, info, warning, error, critical)
- `namespace`: Kubernetes namespace (default)
- `pod`: Pod name
- `container`: Container name

**Log Fields** (in JSON body):
- `timestamp`: ISO 8601 timestamp
- `level`: Log level
- `service`: Service name
- `message`: Human-readable message
- `context`: Additional context (request_id, user_id, task_id, etc.)

### 3. Dashboard Data (Grafana)

Grafana dashboards are JSON configurations stored as ConfigMaps in Kubernetes. No database schema needed.

**Dashboard Structure**:
- Panels: Individual visualizations (graphs, tables, stats)
- Queries: PromQL queries to fetch metrics
- Variables: Dynamic filters (service, namespace, time range)
- Annotations: Event markers on graphs

## No Schema Changes Required

This feature does not require:
- Database migrations
- New tables or columns
- Changes to existing entities
- ORM model updates

All application data models remain unchanged from Spec 8.

## References

- Prometheus data model: https://prometheus.io/docs/concepts/data_model/
- Loki log format: See `contracts/log-format.json`
- Grafana dashboard format: See `contracts/dashboards/`
