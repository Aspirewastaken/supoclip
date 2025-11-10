# SupoClip Monitoring Configuration

This directory contains all monitoring configuration files for the SupoClip backend.

## Directory Structure

```
monitoring/
├── prometheus/
│   ├── prometheus.yml           # Prometheus main configuration
│   └── alerts/
│       └── supoclip-alerts.yml  # Alert rules
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/         # Auto-provisioned datasources
│   │   │   └── prometheus.yml
│   │   └── dashboards/          # Dashboard provisioning config
│   │       └── supoclip.yml
│   └── dashboards/              # Dashboard JSON files
│       └── supoclip-overview.json
├── alertmanager/
│   ├── alertmanager.yml         # Alertmanager configuration
│   └── templates/               # Notification templates
│       └── default.tmpl
├── .env.example                 # Environment variable template
├── QUICK_START.md              # Quick start guide
└── README.md                   # This file
```

## Files Overview

### Prometheus Configuration

- **prometheus.yml**: Main Prometheus configuration
  - Scrape intervals
  - Target definitions (backend, worker, exporters)
  - Alert rule files
  - Alertmanager integration

- **alerts/supoclip-alerts.yml**: Alert rules
  - Error rate alerts
  - Latency alerts
  - Resource alerts (CPU, memory, disk)
  - Worker queue alerts
  - Database alerts

### Grafana Configuration

- **provisioning/datasources/prometheus.yml**: Auto-configures Prometheus datasource
- **provisioning/dashboards/supoclip.yml**: Auto-provisions dashboards
- **dashboards/supoclip-overview.json**: Main monitoring dashboard
  - Request metrics
  - Video processing stats
  - Resource utilization
  - Worker queue status

### Alertmanager Configuration

- **alertmanager.yml**: Alert routing and notification configuration
  - PagerDuty integration
  - Slack integration
  - Email notifications
  - Alert grouping and inhibition rules

- **templates/default.tmpl**: Notification message templates

## Quick Setup

See [QUICK_START.md](QUICK_START.md) for step-by-step instructions.

## Configuration Files You Need to Edit

### 1. Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
cp .env.example .env
nano .env
```

Required variables:
- `GRAFANA_ADMIN_PASSWORD`: Secure password for Grafana
- `PAGERDUTY_ROUTING_KEY`: From PagerDuty integration (optional)
- `SLACK_WEBHOOK_URL`: From Slack webhook setup (optional)
- `SMTP_USERNAME` / `SMTP_PASSWORD`: For email alerts (optional)

### 2. Alert Rules (Optional)

Edit `prometheus/alerts/supoclip-alerts.yml` to adjust:
- Alert thresholds
- Alert durations
- Severity levels
- Alert descriptions

Example:
```yaml
- alert: HighErrorRate
  expr: (rate(supoclip_http_requests_total{status=~"5.."}[5m])) > 0.05
  for: 5m  # Change this duration
  labels:
    severity: critical  # Change severity
```

### 3. Scrape Targets (Optional)

Edit `prometheus/prometheus.yml` to add/remove scrape targets:

```yaml
scrape_configs:
  - job_name: 'supoclip-backend'
    static_configs:
      - targets: ['backend:8000']
    scrape_interval: 15s  # Adjust interval
```

## Verification Steps

1. **Check Prometheus is scraping**:
   - Open http://localhost:9090/targets
   - All targets should show "UP"

2. **Verify Grafana connection**:
   - Open http://localhost:3001
   - Go to Configuration → Data Sources
   - Prometheus should be connected

3. **Test alerts**:
   - Open http://localhost:9090/alerts
   - Should see configured alert rules

4. **View dashboard**:
   - Grafana → Dashboards → SupoClip → SupoClip Overview
   - Should show real-time metrics

## Customization

### Add New Alert

Edit `prometheus/alerts/supoclip-alerts.yml`:

```yaml
- alert: MyCustomAlert
  expr: supoclip_my_metric > 100
  for: 5m
  labels:
    severity: warning
    component: backend
  annotations:
    summary: "My custom alert"
    description: "Metric is {{ $value }}"
```

### Add New Dashboard Panel

1. Open Grafana
2. Go to SupoClip Overview dashboard
3. Click "Add panel"
4. Enter PromQL query:
   ```promql
   rate(supoclip_http_requests_total[5m])
   ```
5. Save dashboard
6. Export JSON and save to `dashboards/`

### Add Notification Channel

Edit `alertmanager/alertmanager.yml`:

```yaml
receivers:
  - name: 'my-channel'
    webhook_configs:
      - url: 'http://my-service/webhook'
```

Then add route:

```yaml
routes:
  - match:
      severity: critical
    receiver: 'my-channel'
```

## Maintenance

### Backup Configuration

```bash
# Backup all monitoring config
tar czf monitoring-backup-$(date +%Y%m%d).tar.gz monitoring/
```

### Update Alert Rules

```bash
# Edit rules
nano prometheus/alerts/supoclip-alerts.yml

# Reload Prometheus (without restart)
curl -X POST http://localhost:9090/-/reload
```

### Export Grafana Dashboards

```bash
# Get dashboard JSON
curl http://admin:password@localhost:3001/api/dashboards/uid/supoclip-overview | \
  jq '.dashboard' > grafana/dashboards/supoclip-overview.json
```

## Troubleshooting

See [QUICK_START.md](QUICK_START.md#troubleshooting) for common issues.

## Additional Documentation

- Main guide: [../MONITORING.md](../MONITORING.md)
- Quick start: [QUICK_START.md](QUICK_START.md)
- Prometheus docs: https://prometheus.io/docs/
- Grafana docs: https://grafana.com/docs/
- Alertmanager docs: https://prometheus.io/docs/alerting/latest/alertmanager/
