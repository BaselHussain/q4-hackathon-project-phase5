"""
Audit Service - Event logging and audit trail microservice.

This package implements a standalone FastAPI service that subscribes to
task events via Dapr Pub/Sub and logs them to the audit_logs table.
"""
