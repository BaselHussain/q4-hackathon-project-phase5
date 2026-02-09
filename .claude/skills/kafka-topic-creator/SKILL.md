---
name: kafka-topic-creator
description: Generate Kafka topic configurations using Strimzi KafkaTopic CRDs or CLI scripts for kafka-topics.sh and Redpanda with production-ready settings.
version: 1.0.0
---

# Kafka Topic Creator Skill

## When to Use This Skill

Use this skill when you need to:
- Create Kafka topics for event-driven microservices
- Generate KafkaTopic YAML manifests for Strimzi operator on Kubernetes
- Create bash scripts for kafka-topics.sh or Redpanda CLI
- Standardize topic configurations across environments
- Set up topics with proper partitions, replication, and retention policies
- Document topic schemas and usage patterns

## How This Skill Works

1. **Gather Topic Requirements**
   - Topic names and purposes
   - Number of partitions (default: 3)
   - Replication factor (default: 1 for dev, 3 for prod)
   - Retention period (default: 7 days / 604800000ms)
   - Cleanup policy (delete or compact)
   - Additional configurations (compression, segment size, etc.)

2. **Generate Configurations**
   - Strimzi KafkaTopic CRDs for Kubernetes deployments
   - Bash scripts using kafka-topics.sh for traditional Kafka
   - Bash scripts using rpk (Redpanda CLI) for Redpanda clusters
   - Topic documentation with schema and usage examples

3. **Apply Best Practices**
   - Appropriate partition count for parallelism
   - Replication factor for fault tolerance
   - Retention policies to manage storage
   - Idempotent topic creation (--if-not-exists)
   - Topic naming conventions

4. **Validate and Document**
   - Include topic purpose and schema documentation
   - Add verification commands
   - Provide monitoring and troubleshooting tips

## Output Files Generated

### Strimzi Operator (Kubernetes)
```
kafka-topics/
├── strimzi/
│   ├── task-events-topic.yaml
│   ├── reminders-topic.yaml
│   ├── task-updates-topic.yaml
│   └── README.md
└── scripts/
    ├── create-topics-kafka.sh
    ├── create-topics-redpanda.sh
    ├── delete-topics.sh
    ├── describe-topics.sh
    └── README.md
```

## Instructions

### 1. Strimzi KafkaTopic CRD Template

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: {{ topic-name }}
  namespace: {{ kafka-namespace }}
  labels:
    strimzi.io/cluster: {{ kafka-cluster-name }}
    app: {{ application-name }}
    component: messaging
spec:
  partitions: 3
  replicas: 1
  config:
    retention.ms: 604800000  # 7 days
    segment.ms: 86400000     # 1 day
    compression.type: producer
    cleanup.policy: delete
    min.insync.replicas: 1
    max.message.bytes: 1048576  # 1MB
```

### 2. Default Topic Configurations

#### task-events Topic
```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: task-events
  namespace: kafka
  labels:
    strimzi.io/cluster: my-cluster
    app: task-manager
    component: messaging
spec:
  partitions: 3
  replicas: 1
  config:
    retention.ms: 604800000      # 7 days
    segment.ms: 86400000         # 1 day
    compression.type: producer
    cleanup.policy: delete
    min.insync.replicas: 1
    max.message.bytes: 1048576   # 1MB
    message.timestamp.type: CreateTime
```

#### reminders Topic
```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: reminders
  namespace: kafka
  labels:
    strimzi.io/cluster: my-cluster
    app: task-manager
    component: messaging
spec:
  partitions: 3
  replicas: 1
  config:
    retention.ms: 604800000      # 7 days
    segment.ms: 86400000         # 1 day
    compression.type: producer
    cleanup.policy: delete
    min.insync.replicas: 1
    max.message.bytes: 1048576   # 1MB
    message.timestamp.type: CreateTime
```

#### task-updates Topic
```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: task-updates
  namespace: kafka
  labels:
    strimzi.io/cluster: my-cluster
    app: task-manager
    component: messaging
spec:
  partitions: 3
  replicas: 1
  config:
    retention.ms: 604800000      # 7 days
    segment.ms: 86400000         # 1 day
    compression.type: producer
    cleanup.policy: delete
    min.insync.replicas: 1
    max.message.bytes: 1048576   # 1MB
    message.timestamp.type: CreateTime
```

### 3. Kafka CLI Script (kafka-topics.sh)

```bash
#!/bin/bash
# create-topics-kafka.sh
# Create Kafka topics using kafka-topics.sh

set -e

KAFKA_BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS:-localhost:9092}"
PARTITIONS="${PARTITIONS:-3}"
REPLICATION_FACTOR="${REPLICATION_FACTOR:-1}"
RETENTION_MS="${RETENTION_MS:-604800000}"  # 7 days

echo "Creating Kafka topics..."
echo "Bootstrap servers: $KAFKA_BOOTSTRAP_SERVERS"
echo "Partitions: $PARTITIONS"
echo "Replication factor: $REPLICATION_FACTOR"
echo "Retention: $RETENTION_MS ms (7 days)"
echo ""

# Function to create topic
create_topic() {
    local topic_name=$1
    echo "Creating topic: $topic_name"

    kafka-topics.sh --create \
        --bootstrap-server "$KAFKA_BOOTSTRAP_SERVERS" \
        --topic "$topic_name" \
        --partitions "$PARTITIONS" \
        --replication-factor "$REPLICATION_FACTOR" \
        --config retention.ms="$RETENTION_MS" \
        --config segment.ms=86400000 \
        --config compression.type=producer \
        --config cleanup.policy=delete \
        --config min.insync.replicas=1 \
        --config max.message.bytes=1048576 \
        --if-not-exists

    echo "✓ Topic $topic_name created successfully"
    echo ""
}

# Create topics
create_topic "task-events"
create_topic "reminders"
create_topic "task-updates"

echo "All topics created successfully!"
echo ""
echo "Verify topics:"
echo "kafka-topics.sh --list --bootstrap-server $KAFKA_BOOTSTRAP_SERVERS"
```

### 4. Redpanda CLI Script (rpk)

```bash
#!/bin/bash
# create-topics-redpanda.sh
# Create Kafka topics using Redpanda rpk CLI

set -e

KAFKA_BROKERS="${KAFKA_BROKERS:-localhost:9092}"
PARTITIONS="${PARTITIONS:-3}"
REPLICATION_FACTOR="${REPLICATION_FACTOR:-1}"
RETENTION_MS="${RETENTION_MS:-604800000}"  # 7 days

echo "Creating Redpanda topics..."
echo "Brokers: $KAFKA_BROKERS"
echo "Partitions: $PARTITIONS"
echo "Replication factor: $REPLICATION_FACTOR"
echo "Retention: $RETENTION_MS ms (7 days)"
echo ""

# Function to create topic
create_topic() {
    local topic_name=$1
    echo "Creating topic: $topic_name"

    rpk topic create "$topic_name" \
        --brokers "$KAFKA_BROKERS" \
        --partitions "$PARTITIONS" \
        --replicas "$REPLICATION_FACTOR" \
        --topic-config retention.ms="$RETENTION_MS" \
        --topic-config segment.ms=86400000 \
        --topic-config compression.type=producer \
        --topic-config cleanup.policy=delete \
        --topic-config min.insync.replicas=1 \
        --topic-config max.message.bytes=1048576

    echo "✓ Topic $topic_name created successfully"
    echo ""
}

# Create topics
create_topic "task-events"
create_topic "reminders"
create_topic "task-updates"

echo "All topics created successfully!"
echo ""
echo "Verify topics:"
echo "rpk topic list --brokers $KAFKA_BROKERS"
```

### 5. Topic Deletion Script

```bash
#!/bin/bash
# delete-topics.sh
# Delete Kafka topics (use with caution!)

set -e

KAFKA_BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS:-localhost:9092}"

echo "⚠️  WARNING: This will delete topics permanently!"
echo "Bootstrap servers: $KAFKA_BOOTSTRAP_SERVERS"
echo ""
read -p "Are you sure you want to delete topics? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

# Function to delete topic
delete_topic() {
    local topic_name=$1
    echo "Deleting topic: $topic_name"

    kafka-topics.sh --delete \
        --bootstrap-server "$KAFKA_BOOTSTRAP_SERVERS" \
        --topic "$topic_name"

    echo "✓ Topic $topic_name deleted"
    echo ""
}

# Delete topics
delete_topic "task-events"
delete_topic "reminders"
delete_topic "task-updates"

echo "All topics deleted!"
```

### 6. Topic Description Script

```bash
#!/bin/bash
# describe-topics.sh
# Describe Kafka topics and their configurations

set -e

KAFKA_BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS:-localhost:9092}"

echo "Describing Kafka topics..."
echo "Bootstrap servers: $KAFKA_BOOTSTRAP_SERVERS"
echo ""

# Function to describe topic
describe_topic() {
    local topic_name=$1
    echo "=========================================="
    echo "Topic: $topic_name"
    echo "=========================================="

    kafka-topics.sh --describe \
        --bootstrap-server "$KAFKA_BOOTSTRAP_SERVERS" \
        --topic "$topic_name"

    echo ""
}

# Describe topics
describe_topic "task-events"
describe_topic "reminders"
describe_topic "task-updates"

echo "Topic listing:"
kafka-topics.sh --list --bootstrap-server "$KAFKA_BOOTSTRAP_SERVERS"
```

## Example Usage

### Strimzi Operator (Kubernetes)

```bash
# Apply KafkaTopic CRDs
kubectl apply -f kafka-topics/strimzi/task-events-topic.yaml
kubectl apply -f kafka-topics/strimzi/reminders-topic.yaml
kubectl apply -f kafka-topics/strimzi/task-updates-topic.yaml

# Verify topics
kubectl get kafkatopics -n kafka

# Check topic status
kubectl describe kafkatopic task-events -n kafka

# Watch topic creation
kubectl get kafkatopics -n kafka -w
```

### Kafka CLI

```bash
# Set environment variables
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export PARTITIONS=3
export REPLICATION_FACTOR=1
export RETENTION_MS=604800000

# Create topics
chmod +x scripts/create-topics-kafka.sh
./scripts/create-topics-kafka.sh

# Verify topics
kafka-topics.sh --list --bootstrap-server localhost:9092

# Describe specific topic
kafka-topics.sh --describe --bootstrap-server localhost:9092 --topic task-events
```

### Redpanda CLI

```bash
# Set environment variables
export KAFKA_BROKERS="localhost:9092"
export PARTITIONS=3
export REPLICATION_FACTOR=1
export RETENTION_MS=604800000

# Create topics
chmod +x scripts/create-topics-redpanda.sh
./scripts/create-topics-redpanda.sh

# Verify topics
rpk topic list --brokers localhost:9092

# Describe specific topic
rpk topic describe task-events --brokers localhost:9092
```

## Topic Configurations Explained

### Core Settings

| Configuration | Value | Description |
|--------------|-------|-------------|
| `partitions` | 3 | Number of partitions for parallel processing |
| `replicas` | 1 (dev) / 3 (prod) | Replication factor for fault tolerance |
| `retention.ms` | 604800000 | Message retention time (7 days) |
| `segment.ms` | 86400000 | Log segment roll time (1 day) |
| `compression.type` | producer | Use producer's compression setting |
| `cleanup.policy` | delete | Delete old messages after retention |
| `min.insync.replicas` | 1 (dev) / 2 (prod) | Minimum replicas for ack=all |
| `max.message.bytes` | 1048576 | Maximum message size (1MB) |

### Environment-Specific Configurations

#### Development
```yaml
partitions: 3
replicas: 1
min.insync.replicas: 1
retention.ms: 604800000  # 7 days
```

#### Staging
```yaml
partitions: 3
replicas: 2
min.insync.replicas: 1
retention.ms: 604800000  # 7 days
```

#### Production
```yaml
partitions: 6
replicas: 3
min.insync.replicas: 2
retention.ms: 2592000000  # 30 days
```

## Topic Naming Conventions

Follow these naming patterns:

```
<domain>-<entity>-<event-type>

Examples:
- task-events          # General task events
- task-created         # Specific event type
- task-updated         # Specific event type
- task-deleted         # Specific event type
- reminders            # Reminder notifications
- task-updates         # Task update notifications
- user-events          # User-related events
- audit-logs           # Audit trail events
```

## Monitoring and Troubleshooting

### Check Topic Lag

```bash
# Kafka CLI
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
    --group my-consumer-group \
    --describe

# Redpanda CLI
rpk group describe my-consumer-group --brokers localhost:9092
```

### Monitor Topic Metrics

```bash
# List consumer groups
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list

# Check topic size
kafka-log-dirs.sh --bootstrap-server localhost:9092 \
    --topic-list task-events,reminders,task-updates \
    --describe
```

### Alter Topic Configuration

```bash
# Increase retention to 14 days
kafka-configs.sh --bootstrap-server localhost:9092 \
    --entity-type topics \
    --entity-name task-events \
    --alter \
    --add-config retention.ms=1209600000

# Increase partitions (cannot decrease!)
kafka-topics.sh --bootstrap-server localhost:9092 \
    --topic task-events \
    --alter \
    --partitions 6
```

## Best Practices

### 1. Partition Count
- Start with 3 partitions for low-traffic topics
- Use 6-12 partitions for medium-traffic topics
- Scale to 20+ partitions for high-traffic topics
- Consider: partitions = max(expected_throughput / partition_throughput, consumer_count)

### 2. Replication Factor
- Development: 1 replica (acceptable data loss)
- Staging: 2 replicas (some fault tolerance)
- Production: 3 replicas (high availability)
- Never use replication factor > number of brokers

### 3. Retention Policy
- Short retention (1-7 days): High-volume events, logs
- Medium retention (7-30 days): Business events, analytics
- Long retention (30-90 days): Audit logs, compliance
- Infinite retention: Use compaction for state topics

### 4. Message Size
- Keep messages small (<1MB)
- Use compression for large payloads
- Consider external storage for large files (S3, blob storage)
- Reference large data by ID/URL in messages

### 5. Topic Organization
- One topic per event type (task-created, task-updated)
- Or one topic per domain (task-events with event type field)
- Avoid mixing unrelated events in same topic
- Use consistent naming conventions

## Security Considerations

### ACLs (Access Control Lists)

```bash
# Grant producer access
kafka-acls.sh --bootstrap-server localhost:9092 \
    --add \
    --allow-principal User:task-service \
    --operation Write \
    --topic task-events

# Grant consumer access
kafka-acls.sh --bootstrap-server localhost:9092 \
    --add \
    --allow-principal User:notification-service \
    --operation Read \
    --topic task-events \
    --group notification-consumer-group
```

### Strimzi KafkaUser

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaUser
metadata:
  name: task-service
  namespace: kafka
  labels:
    strimzi.io/cluster: my-cluster
spec:
  authentication:
    type: tls
  authorization:
    type: simple
    acls:
      - resource:
          type: topic
          name: task-events
          patternType: literal
        operation: Write
      - resource:
          type: topic
          name: task-updates
          patternType: literal
        operation: Write
```

## Integration Examples

### Python Producer (aiokafka)

```python
from aiokafka import AIOKafkaProducer
import json
import asyncio

async def send_task_event(task_id: str, event_type: str, data: dict):
    producer = AIOKafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    await producer.start()
    try:
        event = {
            'task_id': task_id,
            'event_type': event_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }

        await producer.send_and_wait('task-events', value=event)
        print(f"Sent event: {event_type} for task {task_id}")
    finally:
        await producer.stop()
```

### Python Consumer (aiokafka)

```python
from aiokafka import AIOKafkaConsumer
import json
import asyncio

async def consume_task_events():
    consumer = AIOKafkaConsumer(
        'task-events',
        bootstrap_servers='localhost:9092',
        group_id='task-processor',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest'
    )

    await consumer.start()
    try:
        async for msg in consumer:
            event = msg.value
            print(f"Received: {event['event_type']} for task {event['task_id']}")
            # Process event
            await process_event(event)
    finally:
        await consumer.stop()
```

## Validation Checklist

Before deploying topics to production:

- [ ] Topic names follow naming conventions
- [ ] Partition count matches expected throughput
- [ ] Replication factor provides adequate fault tolerance
- [ ] Retention period aligns with business requirements
- [ ] Message size limits are appropriate
- [ ] Compression is enabled for large messages
- [ ] ACLs are configured for security
- [ ] Monitoring and alerting are set up
- [ ] Consumer groups are properly configured
- [ ] Backup and disaster recovery plan exists

## Final Message from Skill

Your Kafka topics are ready! 🎉

**Next Steps:**

1. **For Strimzi (Kubernetes)**:
   ```bash
   kubectl apply -f kafka-topics/strimzi/
   kubectl get kafkatopics -n kafka
   ```

2. **For Kafka CLI**:
   ```bash
   chmod +x scripts/create-topics-kafka.sh
   ./scripts/create-topics-kafka.sh
   ```

3. **For Redpanda**:
   ```bash
   chmod +x scripts/create-topics-redpanda.sh
   ./scripts/create-topics-redpanda.sh
   ```

**Pro Tips:**
- Monitor topic lag and consumer group health
- Set up alerts for high lag or failed consumers
- Use topic compaction for state/changelog topics
- Test failover scenarios in staging
- Document message schemas and contracts
- Consider schema registry for message validation
- Use idempotent producers to avoid duplicates
- Enable monitoring with Prometheus/Grafana

**Topic Configuration Summary:**
- **task-events**: General task lifecycle events
- **reminders**: Reminder notifications and scheduling
- **task-updates**: Real-time task update notifications

All topics configured with:
- 3 partitions for parallel processing
- 1 replica (adjust for production)
- 7-day retention period
- 1MB max message size

Happy streaming! 🚀
