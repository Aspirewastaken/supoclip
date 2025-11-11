# Systemd Service Deployment

This directory contains systemd service files for production deployment of SupoClip workers.

## Prerequisites

1. **User and Group:**
   ```bash
   sudo useradd -r -s /bin/false -d /opt/supoclip supoclip
   sudo usermod -aG video supoclip  # For ffmpeg hardware acceleration
   ```

2. **Installation Directory:**
   ```bash
   sudo mkdir -p /opt/supoclip
   sudo chown supoclip:supoclip /opt/supoclip
   ```

3. **Install Application:**
   ```bash
   sudo -u supoclip git clone <repo> /opt/supoclip
   cd /opt/supoclip/backend
   sudo -u supoclip uv venv .venv
   sudo -u supoclip uv sync
   ```

4. **Environment File:**
   ```bash
   sudo -u supoclip cp /opt/supoclip/backend/.env.example /opt/supoclip/backend/.env
   sudo -u supoclip nano /opt/supoclip/backend/.env
   # Fill in production values
   ```

5. **Create Required Directories:**
   ```bash
   sudo -u supoclip mkdir -p /opt/supoclip/backend/{uploads,clips,logs}
   ```

## Installation

1. **Copy Service File:**
   ```bash
   sudo cp supoclip-worker.service /etc/systemd/system/
   ```

2. **Edit Paths (if needed):**
   ```bash
   sudo nano /etc/systemd/system/supoclip-worker.service
   # Update WorkingDirectory and paths if not using /opt/supoclip
   ```

3. **Reload Systemd:**
   ```bash
   sudo systemctl daemon-reload
   ```

4. **Enable Service (auto-start on boot):**
   ```bash
   sudo systemctl enable supoclip-worker
   ```

5. **Start Service:**
   ```bash
   sudo systemctl start supoclip-worker
   ```

6. **Check Status:**
   ```bash
   sudo systemctl status supoclip-worker
   ```

## Management Commands

### Status Check
```bash
# Full status
sudo systemctl status supoclip-worker

# Is service running?
sudo systemctl is-active supoclip-worker

# Is service enabled?
sudo systemctl is-enabled supoclip-worker
```

### Start/Stop/Restart
```bash
# Start
sudo systemctl start supoclip-worker

# Stop
sudo systemctl stop supoclip-worker

# Restart
sudo systemctl restart supoclip-worker

# Reload (graceful restart)
sudo systemctl reload-or-restart supoclip-worker
```

### Logs
```bash
# View recent logs
sudo journalctl -u supoclip-worker -n 100

# Follow logs (like tail -f)
sudo journalctl -u supoclip-worker -f

# Logs since boot
sudo journalctl -u supoclip-worker -b

# Logs for specific time range
sudo journalctl -u supoclip-worker --since "2025-01-01" --until "2025-01-02"

# Export logs
sudo journalctl -u supoclip-worker > worker-logs.txt
```

### Enable/Disable Auto-Start
```bash
# Enable (start on boot)
sudo systemctl enable supoclip-worker

# Disable (don't start on boot)
sudo systemctl disable supoclip-worker
```

## Scaling Workers

To run multiple worker instances:

1. **Create Multiple Service Files:**
   ```bash
   sudo cp /etc/systemd/system/supoclip-worker.service /etc/systemd/system/supoclip-worker@.service
   ```

2. **Edit Template:**
   ```bash
   sudo nano /etc/systemd/system/supoclip-worker@.service
   ```

   Add `%i` to differentiate instances:
   ```ini
   [Service]
   Environment="WORKER_ID=%i"
   ```

3. **Start Multiple Instances:**
   ```bash
   sudo systemctl enable supoclip-worker@1
   sudo systemctl enable supoclip-worker@2
   sudo systemctl enable supoclip-worker@3

   sudo systemctl start supoclip-worker@{1..3}
   ```

4. **Check Status:**
   ```bash
   sudo systemctl status supoclip-worker@*
   ```

## Monitoring

### Resource Usage
```bash
# Current resource usage
sudo systemctl show supoclip-worker --property=MemoryCurrent,CPUUsageNSec

# Detailed resource stats
sudo systemd-cgtop
```

### Health Checks
```bash
# Check if worker is processing
sudo journalctl -u supoclip-worker --since "1 minute ago" | grep "processing"

# Check for errors
sudo journalctl -u supoclip-worker -p err --since "1 hour ago"
```

### Automated Monitoring
Add to cron or monitoring system:
```bash
# Check if service is running
if ! systemctl is-active --quiet supoclip-worker; then
    echo "Worker is down!" | mail -s "Alert: SupoClip Worker Down" admin@example.com
    sudo systemctl start supoclip-worker
fi
```

## Troubleshooting

### Service Won't Start
1. **Check Syntax:**
   ```bash
   sudo systemd-analyze verify supoclip-worker.service
   ```

2. **Check Dependencies:**
   ```bash
   sudo systemctl status redis.service postgresql.service
   ```

3. **Check Permissions:**
   ```bash
   sudo ls -la /opt/supoclip/backend
   sudo -u supoclip test -r /opt/supoclip/backend/.env && echo "OK" || echo "FAIL"
   ```

4. **Check Environment:**
   ```bash
   sudo systemctl show supoclip-worker --property=Environment
   ```

### Service Crashes Repeatedly
1. **Check Logs:**
   ```bash
   sudo journalctl -u supoclip-worker -n 200 --no-pager
   ```

2. **Increase Logging:**
   Edit service file:
   ```ini
   Environment="LOG_LEVEL=DEBUG"
   ```

3. **Check Resource Limits:**
   ```bash
   sudo systemctl show supoclip-worker --property=LimitNOFILE,LimitNPROC,MemoryMax
   ```

### High Resource Usage
1. **Check Current Usage:**
   ```bash
   sudo systemctl status supoclip-worker
   ```

2. **Adjust Limits:**
   Edit `/etc/systemd/system/supoclip-worker.service`:
   ```ini
   MemoryMax=8G
   CPUQuota=400%
   ```

3. **Reload:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart supoclip-worker
   ```

## Best Practices

1. **Use Separate Service User:**
   - Never run as root
   - Create dedicated `supoclip` user

2. **Resource Limits:**
   - Set `MemoryMax` to prevent OOM
   - Set `CPUQuota` to prevent CPU monopolization

3. **Restart Policy:**
   - Use `Restart=always` for production
   - Set `RestartSec` to prevent restart storms

4. **Logging:**
   - Use journald for centralized logging
   - Rotate logs regularly (journald does this automatically)

5. **Security:**
   - Enable `NoNewPrivileges`
   - Use `PrivateTmp`
   - Restrict file system access with `ProtectSystem` and `ReadWritePaths`

6. **Monitoring:**
   - Monitor with Prometheus + Grafana
   - Set up alerting for service failures
   - Monitor resource usage trends

## Backup and Recovery

### Backup Service File
```bash
sudo cp /etc/systemd/system/supoclip-worker.service /opt/supoclip/backup/
```

### Restore After System Failure
```bash
sudo cp /opt/supoclip/backup/supoclip-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable supoclip-worker
sudo systemctl start supoclip-worker
```

## Integration with Other Services

### Load Balancer Health Check
Configure HAProxy/Nginx to check worker health:
```nginx
upstream supoclip_api {
    server backend:8000 max_fails=3 fail_timeout=30s;

    # Health check
    check interval=5000 rise=2 fall=3 timeout=1000;
    check_http_send "GET /health HTTP/1.0\r\n\r\n";
    check_http_expect_alive http_2xx;
}
```

### Prometheus Monitoring
Add to Prometheus config:
```yaml
scrape_configs:
  - job_name: 'supoclip-worker'
    static_configs:
      - targets: ['localhost:8000']
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: 'worker-1'
```

## References

- [Systemd Service Documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Systemd Resource Control](https://www.freedesktop.org/software/systemd/man/systemd.resource-control.html)
- [ARQ Documentation](https://arq-docs.helpmanual.io/)
