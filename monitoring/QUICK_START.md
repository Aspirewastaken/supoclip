# Monitoring Quick Start Guide

## 1. Install & Start (2 minutes)

```bash
# Install backend dependencies
cd backend
uv sync

# Start monitoring stack
cd ..
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

## 2. Configure Alerts (5 minutes)

```bash
# Copy environment template
cp monitoring/.env.example monitoring/.env

# Edit with your credentials
nano monitoring/.env
```

Required:
- `PAGERDUTY_ROUTING_KEY` - Get from PagerDuty service integration
- `SLACK_WEBHOOK_URL` - Create at https://api.slack.com/messaging/webhooks
- `GRAFANA_ADMIN_PASSWORD` - Set a secure password

## 3. Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3001 | admin / (from .env) |
| **Prometheus** | http://localhost:9090 | None |
| **Alertmanager** | http://localhost:9093 | None |
| **Backend Metrics** | http://localhost:8000/metrics | None |
| **Backend Health** | http://localhost:8000/health | None |

## 4. Verify Setup

### Check Metrics
```bash
curl http://localhost:8000/metrics | grep supoclip
```

### Check Health
```bash
curl http://localhost:8000/health | jq
```

### Check Prometheus Targets
Open: http://localhost:9090/targets
- `supoclip-backend` should be **UP**

### View Dashboard
1. Open http://localhost:3001
2. Login with admin credentials
3. Go to Dashboards → SupoClip → SupoClip Overview

## 5. Test Alerting

### Trigger Test Alert
```bash
# Send alert to Alertmanager
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "severity": "critical",
      "component": "test"
    },
    "annotations": {
      "summary": "This is a test alert",
      "description": "Testing monitoring setup"
    }
  }]'
```

Check:
- Alertmanager UI: http://localhost:9093
- PagerDuty (if configured)
- Slack channel (if configured)
- Email (if configured)

## Common Commands

### View Logs
```bash
# Backend
docker logs -f supoclip-backend

# Prometheus
docker logs -f supoclip-prometheus

# Grafana
docker logs -f supoclip-grafana

# Alertmanager
docker logs -f supoclip-alertmanager
```

### Restart Services
```bash
# Restart monitoring stack
docker-compose -f docker-compose.monitoring.yml restart

# Restart specific service
docker-compose -f docker-compose.monitoring.yml restart prometheus
docker-compose -f docker-compose.monitoring.yml restart grafana
docker-compose -f docker-compose.monitoring.yml restart alertmanager
```

### Stop Monitoring
```bash
docker-compose -f docker-compose.monitoring.yml down
```

### Full Cleanup (including data)
```bash
docker-compose -f docker-compose.monitoring.yml down -v
```

## Useful Queries

### Request Rate
```promql
sum(rate(supoclip_http_requests_total[5m]))
```

### Error Rate
```promql
sum(rate(supoclip_http_requests_total{status=~"5.."}[5m]))
/
sum(rate(supoclip_http_requests_total[5m]))
```

### P95 Latency
```promql
histogram_quantile(0.95,
  sum(rate(supoclip_http_request_duration_seconds_bucket[5m]))
  by (le, endpoint)
)
```

### Videos Processing
```promql
supoclip_video_processing_in_progress
```

### Worker Queue Depth
```promql
sum(supoclip_worker_queue_depth)
```

### Memory Usage
```promql
supoclip_memory_usage_percent
```

### Disk Free Space (GB)
```promql
supoclip_disk_free_bytes / 1024 / 1024 / 1024
```

## Troubleshooting

### Metrics endpoint returns 404
- Check monitoring integration in `main.py`
- Run: `grep "setup_monitoring" backend/src/main.py`

### Prometheus can't reach backend
- Check Docker network: `docker network ls`
- Verify backend is running: `docker ps | grep backend`
- Check backend health: `curl http://localhost:8000/health`

### Grafana dashboard is empty
- Verify Prometheus datasource: Grafana → Configuration → Data Sources
- Test connection (should see "Data source is working")
- Check if metrics exist: `curl http://localhost:9090/api/v1/label/__name__/values`

### Alerts not firing
- Check alert rules loaded: http://localhost:9090/rules
- View active alerts: http://localhost:9090/alerts
- Check Alertmanager: http://localhost:9093/#/alerts

### PagerDuty not receiving alerts
- Verify `PAGERDUTY_ROUTING_KEY` in `.env`
- Check Alertmanager logs: `docker logs supoclip-alertmanager | grep pagerduty`
- Test PagerDuty manually:
  ```bash
  curl -X POST https://events.pagerduty.com/v2/enqueue \
    -H "Content-Type: application/json" \
    -d '{
      "routing_key": "YOUR_KEY",
      "event_action": "trigger",
      "payload": {
        "summary": "Test",
        "severity": "critical",
        "source": "SupoClip"
      }
    }'
  ```

## Next Steps

1. ✅ Review dashboards and customize
2. ✅ Adjust alert thresholds for your load
3. ✅ Configure notification channels
4. ✅ Set up escalation policies in PagerDuty
5. ✅ Document runbooks for common alerts
6. ✅ Schedule regular reviews of metrics

See [MONITORING.md](../MONITORING.md) for detailed documentation.
