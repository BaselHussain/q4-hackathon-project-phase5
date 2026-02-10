# Architecture: Monitoring & Logging Flow

## Overview

The monitoring and logging architecture provides full observability across all microservices
using Prometheus + Grafana for metrics and Loki + Promtail for logs.

## Monitoring Architecture

```
+------------------+     +------------------+     +------------------+
|   Backend API    |     | Recurring Task   |     | Notification     |
|   (port 8000)    |     |   (port 8001)    |     |   (port 8002)    |
|                  |     |                  |     |                  |
|  /metrics -------+---->|  /metrics -------+---->|  /metrics ------->
|  /health         |     |  /health         |     |  /health         |
+--------+---------+     +--------+---------+     +--------+---------+
         |                        |                        |
         v                        v                        v
+--------+------------------------+------------------------+---------+
|                        Prometheus                                  |
|   - Scrapes /metrics every 15s from all services                   |
|   - Scrapes Dapr sidecar metrics (port 9090)                       |
|   - Stores metrics with 15-30 day retention                        |
|   - Evaluates 40+ alert rules                                     |
+--------+----------------------------------------------------------+
         |
         v
+--------+----------------------------------------------------------+
|                         Grafana                                    |
|                                                                    |
|   +-------------------+  +-------------------+  +----------------+ |
|   | Service Overview  |  | Event Processing  |  | WebSocket      | |
|   | Dashboard         |  | Dashboard         |  | Dashboard      | |
|   |                   |  |                   |  |                | |
|   | - Request rate    |  | - Kafka lag       |  | - Connections  | |
|   | - Error rate      |  | - Event latency   |  | - Msg rate     | |
|   | - p95 latency     |  | - Processing rate |  | - Delivery     | |
|   | - Pod health      |  | - DLQ depth       |  | - Reconnects   | |
|   +-------------------+  +-------------------+  +----------------+ |
+--------------------------------------------------------------------+
         |
         v
+--------+----------------------------------------------------------+
|                       AlertManager                                 |
|                                                                    |
|   Alert Routing:                                                   |
|   - Critical (P1) -> PagerDuty + Slack #incidents                  |
|   - Warning  (P2) -> Slack #alerts                                 |
|   - Info     (P3) -> Slack #monitoring                             |
|                                                                    |
|   Grouping: by alertname, cluster, service                         |
|   Dedup: 4-hour repeat interval                                    |
+--------------------------------------------------------------------+

+------------------+     +------------------+
|   Sync Service   |     |  Audit Service   |
|   (port 8003)    |     |   (port 8004)    |
|                  |     |                  |
|  /metrics -------+---->|  /metrics ------->  (Also scraped by Prometheus)
|  /health         |     |  /health         |
+------------------+     +------------------+
```

## Dapr Sidecar Metrics

```
+---------------------+
|   Application Pod   |
|                     |
|  +---------------+  |         +------------------+
|  |  App Container|  |         |                  |
|  |  (port 8000)  |  |         |   Prometheus     |
|  +---------------+  |         |                  |
|                     |  9090   |  ServiceMonitor  |
|  +---------------+  +-------->|  (dapr.io/       |
|  |  Dapr Sidecar |  | metrics |   enabled=true)  |
|  |  (port 3500)  |  |         |                  |
|  +---------------+  |         +------------------+
+---------------------+

Dapr Metrics Collected:
- dapr_http_server_request_count
- dapr_http_server_latency_bucket
- dapr_component_pubsub_ingress_count
- dapr_component_pubsub_egress_count
- dapr_component_state_count
```

## Logging Architecture

```
+------------------+     +------------------+     +------------------+
|   Backend API    |     | Recurring Task   |     | Notification     |
|                  |     |                  |     |                  |
|  Structured JSON |     |  Structured JSON |     |  Structured JSON |
|  Logger          |     |  Logger          |     |  Logger          |
|                  |     |                  |     |                  |
|  stdout --------+---->|  stdout ---------+---->|  stdout --------->
+--------+---------+     +--------+---------+     +--------+---------+
         |                        |                        |
         v                        v                        v
+--------+------------------------+------------------------+---------+
|                        Promtail (DaemonSet)                        |
|                                                                    |
|   - Runs on every node                                             |
|   - Scrapes /var/log/pods/*/*.log                                  |
|   - JSON pipeline: parse -> extract -> timestamp -> labels         |
|   - Extracts: level, logger, user_id, request_id, trace_id        |
|   - Labels: namespace, pod, container, service                     |
+--------+----------------------------------------------------------+
         |
         v
+--------+----------------------------------------------------------+
|                          Loki                                      |
|                                                                    |
|   Minikube: Single-binary (filesystem storage)                     |
|   Production: Distributed (cloud object storage)                   |
|                                                                    |
|   Storage Backends:                                                |
|   +------------------+  +------------------+  +------------------+ |
|   | OCI Object       |  | Azure Blob       |  | Google Cloud     | |
|   | Storage           |  | Storage          |  | Storage          | |
|   +------------------+  +------------------+  +------------------+ |
|                                                                    |
|   Retention: 7d (dev) / 30d (prod)                                 |
+--------+----------------------------------------------------------+
         |
         v
+--------+----------------------------------------------------------+
|                     Grafana (Explore)                               |
|                                                                    |
|   Pre-defined Queries:                                             |
|   - Task creation failures                                         |
|   - Event publishing errors                                        |
|   - WebSocket disconnections                                       |
|   - Authentication failures                                        |
|   - Database errors                                                |
|   - High latency requests                                          |
|   - User activity traces                                           |
+--------------------------------------------------------------------+
```

## Log Format (JSON)

```json
{
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "level": "INFO",
  "logger": "backend.routers.tasks",
  "message": "Task created",
  "request_id": "req-a1b2c3d4",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "trace-x1y2z3",
  "span_id": "span-m1n2o3"
}
```

## Request Flow with Observability

```
Client Request
      |
      v
+-----+-----+
|  Ingress   |
|  Controller|
+-----+------+
      |
      v
+-----+------+     LoggingMiddleware:
|  Backend   |     - Generate request_id
|  API       |     - Extract trace_id, span_id
|            |     - Set context vars for structured logging
|  Metrics:  |     - Add X-Request-ID to response
|  - latency |
|  - count   |
|  - errors  |
+-----+------+
      |
      | Dapr Pub/Sub
      v
+-----+------+     +-----+------+     +-----+------+
| Recurring  |     | Notification|     |   Audit    |
| Task Svc   |     | Service     |     |  Service   |
|            |     |             |     |            |
| Metrics:   |     | Metrics:    |     | Metrics:   |
| - created  |     | - scheduled |     | - written  |
| - duration |     | - sent      |     | - duration |
+------------+     +-------------+     +------------+
```
