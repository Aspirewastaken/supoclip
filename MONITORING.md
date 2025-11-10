# SupoClip Monitoring Setup Guide

This guide provides comprehensive instructions for setting up monitoring and alerting for the SupoClip backend using Prometheus, Grafana, and Alertmanager.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Metrics Reference](#metrics-reference)
7. [Alerting Rules](#alerting-rules)
8. [Grafana Dashboards](#grafana-dashboards)
9. [PagerDuty Integration](#pagerduty-integration)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)

---

## Overview

The SupoClip monitoring stack provides:

- **Real-time metrics** via Prometheus
- **Visual dashboards** via Grafana
- **Automated alerting** via Alertmanager
- **Multiple notification channels** (PagerDuty, Slack, Email)

### Key Metrics Tracked

- **Request Metrics**: Latency, throughput, error rates by endpoint
- **Video Processing**: Duration by stage, success/failure rates, queue depth
- **Worker Metrics**: Queue depth, task processing time, failure rates
- **System Resources**: CPU, memory, disk usage
- **Database**: Query performance, connection pool status
- **Redis**: Connection status, memory usage

---

## Quick Start

### 1. Install Dependencies

First, install the Prometheus client libraries in the backend:

```bash
cd backend
uv sync  # This will install prometheus-client and prometheus-fastapi-instrumentator
```

### 2. Integrate Monitoring in Backend

Add monitoring to your FastAPI app in `backend/src/main.py`:

```python
from .monitoring import setup_monitoring

# After creating the FastAPI app
app = FastAPI(...)

# Setup monitoring (adds middleware, /metrics, and /health endpoints)
setup_monitoring(app, version="1.0.0")
```

### 3. Start Monitoring Stack

```bash
# From the project root
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

### 4. Access Monitoring Services

- **Grafana**: http://localhost:3001 (default: admin/admin)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093
- **Backend Metrics**: http://localhost:8000/metrics
- **Backend Health**: http://localhost:8000/health

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      SupoClip Backend                        │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   /metrics   │    │   /health    │    │  Middleware  │ │
│  │   endpoint   │    │   endpoint   │    │  (tracking)  │ │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘ │
└─────────┼──────────────────┼──────────────────┼───────────┘
          │                   │                   │
          │ (scrape)          │ (poll)           │ (emit metrics)
          │                   │                   │
      ┌───▼───────────────────▼───────────────────▼───┐
      │             Prometheus                         │
      │  - Scrapes metrics every 15s                   │
      │  - Stores time-series data                     │
      │  - Evaluates alerting rules                    │
      └───┬────────────────────────────────┬───────────┘
          │                                 │
          │ (query)                         │ (alerts)
          │                                 │
      ┌───▼────────────┐            ┌──────▼──────────┐
      │    Grafana     │            │  Alertmanager   │
      │  - Dashboards  │            │  - Route alerts │
      │  - Visualization│            │  - Notifications│
      └────────────────┘            └──────┬──────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                       │
              ┌─────▼─────┐         ┌─────▼─────┐         ┌──────▼──────┐
              │ PagerDuty │         │   Slack   │         │    Email    │
              └───────────┘         └───────────┘         └─────────────┘
```

---

## Installation

### Option 1: Docker Compose (Recommended)

The monitoring stack is included in `docker-compose.monitoring.yml`:

```bash
# Start everything (app + monitoring)
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Or start only monitoring services
docker-compose -f docker-compose.monitoring.yml up -d
```

### Option 2: Manual Installation

If not using Docker, install each component separately:

#### Prometheus

```bash
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*
./prometheus --config.file=../monitoring/prometheus/prometheus.yml
```

#### Grafana

```bash
# Ubuntu/Debian
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana

# Start Grafana
sudo systemctl start grafana-server
```

#### Alertmanager

```bash
wget https://github.com/prometheus/alertmanager/releases/download/v0.26.0/alertmanager-0.26.0.linux-amd64.tar.gz
tar xvfz alertmanager-*.tar.gz
cd alertmanager-*
./alertmanager --config.file=../monitoring/alertmanager/alertmanager.yml
```

---

## Configuration

### Backend Configuration

The monitoring module is automatically configured when you call `setup_monitoring()`. No additional configuration is needed.

#### Manual Middleware Integration

If you prefer manual integration:

```python
from fastapi import FastAPI
from .monitoring import PrometheusMiddleware, get_metrics, get_metrics_content_type

app = FastAPI()

# Add Prometheus middleware
app.add_middleware(PrometheusMiddleware)

# Add metrics endpoint
@app.get("/metrics")
async def metrics():
    from fastapi.responses import Response
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type()
    )
```

### Prometheus Configuration

Edit `monitoring/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'supoclip-backend'
    static_configs:
      - targets: ['backend:8000']
    scrape_interval: 15s
```

### Alertmanager Configuration

Configure notification channels in `monitoring/alertmanager/alertmanager.yml`.

#### Environment Variables

Create `monitoring/.env` from `.env.example`:

```bash
cp monitoring/.env.example monitoring/.env
# Edit with your actual values
```

Required variables:

```bash
# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your_secure_password

# PagerDuty (optional)
PAGERDUTY_ROUTING_KEY=your_routing_key

# Slack (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Email (optional)
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_specific_password
```

---

## Metrics Reference

### HTTP Request Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `supoclip_http_requests_total` | Counter | Total HTTP requests | method, endpoint, status |
| `supoclip_http_request_duration_seconds` | Histogram | Request duration | method, endpoint |
| `supoclip_http_requests_in_progress` | Gauge | Current requests | method, endpoint |

### Video Processing Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `supoclip_video_processing_duration_seconds` | Histogram | Processing time | stage |
| `supoclip_video_processing_total` | Counter | Videos processed | status |
| `supoclip_video_processing_in_progress` | Gauge | Active processing | - |
| `supoclip_clips_generated_total` | Counter | Clips created | source_type |

**Stages**: `download`, `transcribe`, `analyze`, `clip_generation`

### Worker Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `supoclip_worker_queue_depth` | Gauge | Tasks in queue | queue_name |
| `supoclip_worker_queue_processing_time_seconds` | Histogram | Task duration | queue_name, task_type |
| `supoclip_worker_queue_tasks_processed_total` | Counter | Tasks processed | queue_name, task_type, status |
| `supoclip_active_workers` | Gauge | Active workers | - |
| `supoclip_failed_workers_total` | Counter | Worker failures | worker_id, reason |

### Resource Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `supoclip_cpu_usage_percent` | Gauge | CPU usage | - |
| `supoclip_memory_usage_bytes` | Gauge | Memory used | - |
| `supoclip_memory_usage_percent` | Gauge | Memory percent | - |
| `supoclip_disk_usage_bytes` | Gauge | Disk space used | path |
| `supoclip_disk_usage_percent` | Gauge | Disk percent | path |
| `supoclip_disk_free_bytes` | Gauge | Free disk space | path |

### Database Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `supoclip_db_query_duration_seconds` | Histogram | Query time | query_type |
| `supoclip_db_connections_active` | Gauge | Active connections | - |
| `supoclip_db_connections_idle` | Gauge | Idle connections | - |

---

## Alerting Rules

### Critical Alerts (PagerDuty)

| Alert | Condition | Duration | Description |
|-------|-----------|----------|-------------|
| `HighErrorRate` | Error rate >5% | 5 minutes | High 5xx error rate |
| `BackendDown` | Backend unreachable | 1 minute | Service is down |
| `WorkerFailed` | Worker unreachable | 2 minutes | Worker crashed |
| `CriticalMemoryUsage` | Memory >95% | 2 minutes | Out of memory risk |
| `CriticalDiskSpace` | Free <1GB | 2 minutes | Disk almost full |
| `DatabaseDown` | DB unreachable | 1 minute | Database offline |

### Warning Alerts (Slack/Email)

| Alert | Condition | Duration | Description |
|-------|-----------|----------|-------------|
| `HighRequestLatency` | P95 latency >5s | 5 minutes | Slow responses |
| `WorkerQueueBackup` | Queue depth >10 | 10 minutes | Tasks backing up |
| `HighMemoryUsage` | Memory >85% | 5 minutes | High memory usage |
| `LowDiskSpace` | Free <5GB | 5 minutes | Low disk space |
| `HighCPUUsage` | CPU >80% | 10 minutes | High CPU load |
| `SlowVideoProcessing` | P95 >600s | 10 minutes | Slow clip generation |

### Customizing Alerts

Edit `monitoring/prometheus/alerts/supoclip-alerts.yml`:

```yaml
- alert: CustomAlert
  expr: your_metric > threshold
  for: 5m
  labels:
    severity: warning
    component: backend
  annotations:
    summary: "Custom alert fired"
    description: "Details: {{ $value }}"
```

---

## Grafana Dashboards

### Pre-configured Dashboards

1. **SupoClip Overview** (`supoclip-overview`)
   - Request metrics
   - Video processing stats
   - Resource utilization
   - Worker queue status

### Accessing Dashboards

1. Open http://localhost:3001
2. Login (default: admin/admin)
3. Navigate to Dashboards → SupoClip folder

### Creating Custom Dashboards

1. Click **+** → **Dashboard**
2. Add Panel → Select metric from Prometheus
3. Example queries:

```promql
# Request rate
sum(rate(supoclip_http_requests_total[5m]))

# Error rate
sum(rate(supoclip_http_requests_total{status=~"5.."}[5m]))
/
sum(rate(supoclip_http_requests_total[5m]))

# P95 latency by endpoint
histogram_quantile(0.95,
  sum(rate(supoclip_http_request_duration_seconds_bucket[5m]))
  by (le, endpoint)
)

# Video processing in progress
supoclip_video_processing_in_progress

# Disk free space
supoclip_disk_free_bytes / 1024 / 1024 / 1024  # Convert to GB
```

---

## PagerDuty Integration

### Setup

1. **Create PagerDuty Service**
   - Go to PagerDuty → Services → New Service
   - Name: "SupoClip Backend"
   - Integration: Events API v2

2. **Get Integration Key**
   - Copy the **Routing Key** (Events API v2) or **Service Key** (Events API v1)

3. **Configure Environment**
   ```bash
   # In monitoring/.env
   PAGERDUTY_ROUTING_KEY=your_key_here
   ```

4. **Restart Alertmanager**
   ```bash
   docker-compose -f docker-compose.monitoring.yml restart alertmanager
   ```

### Testing PagerDuty Integration

Trigger a test alert:

```bash
# Simulate high error rate
for i in {1..100}; do
  curl http://localhost:8000/nonexistent-endpoint
done
```

Or use the Alertmanager API:

```bash
curl -X POST http://localhost:9093/api/v1/alerts -H "Content-Type: application/json" -d '[
  {
    "labels": {
      "alertname": "TestAlert",
      "severity": "critical"
    },
    "annotations": {
      "summary": "Test alert for PagerDuty integration"
    }
  }
]'
```

### Alternative Integrations

#### Slack

```bash
# Create webhook at https://api.slack.com/messaging/webhooks
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

#### Email (Gmail)

```bash
# Use app-specific password: https://support.google.com/accounts/answer/185833
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
DATABASE_TEAM_EMAIL=team@example.com
BACKEND_TEAM_EMAIL=backend@example.com
```

---

## Troubleshooting

### Metrics Not Appearing

1. **Check backend metrics endpoint**:
   ```bash
   curl http://localhost:8000/metrics
   ```
   Should return Prometheus-formatted metrics.

2. **Check Prometheus targets**:
   - Visit http://localhost:9090/targets
   - Backend should be "UP"

3. **Check middleware is installed**:
   ```python
   # In main.py
   from .monitoring import setup_monitoring
   setup_monitoring(app)
   ```

### Alerts Not Firing

1. **Check alert rules**:
   ```bash
   # View active alerts
   curl http://localhost:9090/api/v1/alerts
   ```

2. **Check Alertmanager status**:
   ```bash
   curl http://localhost:9093/api/v2/status
   ```

3. **Verify alert configuration**:
   - Check `monitoring/prometheus/alerts/supoclip-alerts.yml`
   - Ensure Prometheus can read the file

### Grafana Dashboard Empty

1. **Check datasource**:
   - Grafana → Configuration → Data Sources
   - Prometheus should be connected

2. **Test query**:
   - Dashboard → Add Panel
   - Query: `up{job="supoclip-backend"}`
   - Should return `1`

### PagerDuty Not Receiving Alerts

1. **Check environment variables**:
   ```bash
   docker exec supoclip-alertmanager env | grep PAGERDUTY
   ```

2. **Check Alertmanager logs**:
   ```bash
   docker logs supoclip-alertmanager
   ```

3. **Test PagerDuty integration**:
   ```bash
   curl -X POST https://events.pagerduty.com/v2/enqueue \
     -H "Content-Type: application/json" \
     -d '{
       "routing_key": "YOUR_KEY",
       "event_action": "trigger",
       "payload": {
         "summary": "Test alert",
         "severity": "critical",
         "source": "SupoClip"
       }
     }'
   ```

---

## Best Practices

### 1. Monitor What Matters

Focus on:
- **Request latency** (P50, P95, P99)
- **Error rates** (4xx, 5xx)
- **Video processing success rate**
- **Worker queue depth**
- **Resource utilization** (CPU, memory, disk)

### 2. Set Appropriate Thresholds

- **Critical**: Immediate action required (page on-call)
- **Warning**: Investigate during business hours
- **Info**: For tracking trends

### 3. Alert Fatigue Prevention

- Use `for:` duration to avoid transient alerts
- Group related alerts
- Use inhibition rules to suppress cascading alerts
- Route different severities to different channels

### 4. Regular Review

- Review dashboards weekly
- Adjust thresholds based on actual usage
- Archive unused metrics
- Update alert rules as system evolves

### 5. Retention Policies

Prometheus default: 30 days

Adjust in `docker-compose.monitoring.yml`:
```yaml
prometheus:
  command:
    - '--storage.tsdb.retention.time=90d'  # Keep 90 days
```

### 6. Security

- Change default Grafana password
- Use HTTPS in production
- Restrict Prometheus/Grafana access
- Rotate PagerDuty keys regularly

### 7. High Availability

For production:
- Run multiple Prometheus instances
- Use Thanos for long-term storage
- Configure Alertmanager clustering
- Deploy Grafana with database backend

---

## Example: Instrumenting Custom Code

### Track Video Processing Stages

```python
from .monitoring import track_video_processing_stage, video_processing_total, clips_generated_total

async def process_video(video_url: str):
    # Track download stage
    with track_video_processing_stage("download"):
        video_path = await download_video(video_url)

    # Track transcription stage
    with track_video_processing_stage("transcribe"):
        transcript = await transcribe_video(video_path)

    # Track analysis stage
    with track_video_processing_stage("analyze"):
        segments = await analyze_transcript(transcript)

    # Track clip generation
    with track_video_processing_stage("clip_generation"):
        clips = await generate_clips(video_path, segments)

    # Record success
    video_processing_total.labels(status="success").inc()
    clips_generated_total.labels(source_type="youtube").inc(len(clips))

    return clips
```

### Track Worker Tasks

```python
from .monitoring import track_worker_task, worker_queue_depth

@track_worker_task(queue_name="video_processing", task_type="clip_generation")
async def process_video_task(ctx, task_id: str):
    # Task processing code
    result = await process_video(task_id)
    return result

# Update queue depth
async def update_queue_metrics():
    queue_size = await get_queue_size()
    worker_queue_depth.labels(queue_name="video_processing").set(queue_size)
```

### Track Database Queries

```python
from .monitoring import track_db_query

async def get_user_tasks(user_id: str):
    with track_db_query("get_user_tasks"):
        result = await db.execute(
            text("SELECT * FROM tasks WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
    return result.fetchall()
```

---

## Support

For issues or questions:

1. Check logs: `docker logs supoclip-prometheus`
2. Review Prometheus targets: http://localhost:9090/targets
3. Check Grafana datasource: http://localhost:3001
4. Review alerting rules: http://localhost:9090/alerts

---

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [PagerDuty Integration Guide](https://www.pagerduty.com/docs/guides/prometheus-integration-guide/)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)
