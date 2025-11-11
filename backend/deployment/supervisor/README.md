# Supervisor Deployment

This directory contains Supervisor configuration for SupoClip workers.

## Installation

### 1. Install Supervisor

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install supervisor
```

**CentOS/RHEL:**
```bash
sudo yum install supervisor
sudo systemctl enable supervisord
sudo systemctl start supervisord
```

**macOS:**
```bash
brew install supervisor
brew services start supervisor
```

### 2. Create Log Directory

```bash
sudo mkdir -p /var/log/supoclip
sudo chown supoclip:supoclip /var/log/supoclip
```

### 3. Copy Configuration

```bash
sudo cp supoclip-worker.conf /etc/supervisor/conf.d/
```

### 4. Update Configuration (if needed)

```bash
sudo nano /etc/supervisor/conf.d/supoclip-worker.conf
# Update paths, environment variables, etc.
```

### 5. Load Configuration

```bash
sudo supervisorctl reread
sudo supervisorctl update
```

### 6. Start Worker

```bash
sudo supervisorctl start supoclip-worker:*
```

## Management Commands

### Status
```bash
# All programs
sudo supervisorctl status

# Specific program
sudo supervisorctl status supoclip-worker:*
```

### Start/Stop/Restart
```bash
# Start
sudo supervisorctl start supoclip-worker:*

# Stop
sudo supervisorctl stop supoclip-worker:*

# Restart
sudo supervisorctl restart supoclip-worker:*

# Start all
sudo supervisorctl start all

# Stop all
sudo supervisorctl stop all
```

### Logs
```bash
# Tail logs
sudo supervisorctl tail -f supoclip-worker:supoclip-worker_01

# View stdout
sudo supervisorctl tail supoclip-worker:supoclip-worker_01 stdout

# View stderr
sudo supervisorctl tail supoclip-worker:supoclip-worker_01 stderr

# View log files directly
tail -f /var/log/supoclip/worker.log
tail -f /var/log/supoclip/worker-error.log
```

### Configuration Reload
```bash
# After editing config
sudo supervisorctl reread
sudo supervisorctl update

# Restart supervisord itself (if needed)
sudo systemctl restart supervisor
```

## Scaling Workers

To run multiple worker processes:

### Option 1: numprocs (Simple)

Edit `/etc/supervisor/conf.d/supoclip-worker.conf`:

```ini
[program:supoclip-worker]
numprocs=4  ; Run 4 worker processes
numprocs_start=1
process_name=%(program_name)s_%(process_num)02d
```

This creates:
- `supoclip-worker_01`
- `supoclip-worker_02`
- `supoclip-worker_03`
- `supoclip-worker_04`

### Option 2: Group (Advanced)

Create separate configs for different worker types:

```ini
; /etc/supervisor/conf.d/supoclip-workers.conf

[group:supoclip]
programs=supoclip-worker-1,supoclip-worker-2,supoclip-worker-3

[program:supoclip-worker-1]
command=/opt/supoclip/backend/.venv/bin/arq src.workers.tasks.WorkerSettings
directory=/opt/supoclip/backend
user=supoclip
autostart=true
autorestart=true
environment=WORKER_ID="1"

[program:supoclip-worker-2]
command=/opt/supoclip/backend/.venv/bin/arq src.workers.tasks.WorkerSettings
directory=/opt/supoclip/backend
user=supoclip
autostart=true
autorestart=true
environment=WORKER_ID="2"

[program:supoclip-worker-3]
command=/opt/supoclip/backend/.venv/bin/arq src.workers.tasks.WorkerSettings
directory=/opt/supoclip/backend
user=supoclip
autostart=true
autorestart=true
environment=WORKER_ID="3"
```

Control group:
```bash
sudo supervisorctl start supoclip:*
sudo supervisorctl status supoclip:*
sudo supervisorctl restart supoclip:*
```

## Monitoring

### Web Interface

Enable Supervisor's built-in web interface:

Edit `/etc/supervisor/supervisord.conf`:

```ini
[inet_http_server]
port=127.0.0.1:9001
username=admin
password=your_secure_password
```

Restart supervisord:
```bash
sudo systemctl restart supervisor
```

Access at: http://localhost:9001

### External Monitoring

#### Export Status to Prometheus

Install supervisor exporter:
```bash
pip install supervisor-prometheus-exporter
```

Run exporter:
```bash
supervisor-prometheus-exporter --supervisord-url http://localhost:9001
```

Add to Prometheus:
```yaml
scrape_configs:
  - job_name: 'supervisor'
    static_configs:
      - targets: ['localhost:9876']
```

## Auto-Start on Boot

### Systemd (Ubuntu/Debian/CentOS)

Supervisor should auto-start via systemd:

```bash
# Enable
sudo systemctl enable supervisor

# Check status
sudo systemctl status supervisor
```

### Init.d (Older Systems)

```bash
# Enable
sudo update-rc.d supervisor defaults

# Start
sudo service supervisor start
```

## Troubleshooting

### Worker Not Starting

1. **Check Supervisor Logs:**
   ```bash
   sudo tail -f /var/log/supervisor/supervisord.log
   ```

2. **Check Worker Logs:**
   ```bash
   sudo tail -f /var/log/supoclip/worker.log
   sudo tail -f /var/log/supoclip/worker-error.log
   ```

3. **Check Configuration:**
   ```bash
   sudo supervisorctl reread
   # Should show: supoclip-worker: available

   sudo supervisorctl update
   # Should show: supoclip-worker: added process group
   ```

4. **Test Command Manually:**
   ```bash
   sudo -u supoclip /opt/supoclip/backend/.venv/bin/arq src.workers.tasks.WorkerSettings
   ```

### Worker Keeps Restarting

1. **Check Exit Code:**
   ```bash
   sudo supervisorctl status supoclip-worker:*
   # Look for "BACKOFF" or "FATAL"
   ```

2. **Increase startretries:**
   ```ini
   startretries=10
   startsecs=10
   ```

3. **Check Resource Limits:**
   ```bash
   # Check if OOM killed
   dmesg | grep -i kill
   ```

### Configuration Not Loading

1. **Verify File Location:**
   ```bash
   ls -la /etc/supervisor/conf.d/supoclip-worker.conf
   ```

2. **Check Syntax:**
   ```bash
   sudo supervisorctl reread
   # Should show no errors
   ```

3. **Force Reload:**
   ```bash
   sudo supervisorctl reload
   ```

## Best Practices

1. **Logging:**
   - Rotate logs to prevent disk fill
   - Set reasonable `stdout_logfile_maxbytes`
   - Keep at least 5-10 backups

2. **Process Management:**
   - Use `stopasgroup=true` and `killasgroup=true`
   - Set appropriate `stopwaitsecs` for graceful shutdown

3. **Scaling:**
   - Start with 1 worker, scale based on load
   - Monitor queue depth to determine worker count

4. **Security:**
   - Run as dedicated user (not root)
   - Secure web interface with strong password
   - Use firewall to restrict web interface access

5. **Monitoring:**
   - Enable web interface for quick checks
   - Export metrics to Prometheus
   - Set up alerting for worker failures

## Integration Examples

### Nginx Reverse Proxy for Web UI

```nginx
location /supervisor/ {
    proxy_pass http://127.0.0.1:9001/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;

    # Basic auth
    auth_basic "Supervisor Admin";
    auth_basic_user_file /etc/nginx/.htpasswd;
}
```

### Systemd Integration

Supervisor is already managed by systemd on most systems:

```bash
# Status
sudo systemctl status supervisor

# Logs
sudo journalctl -u supervisor -f

# Restart
sudo systemctl restart supervisor
```

## Migration from Other Systems

### From Systemd

1. Stop systemd service:
   ```bash
   sudo systemctl stop supoclip-worker
   sudo systemctl disable supoclip-worker
   ```

2. Install Supervisor config:
   ```bash
   sudo cp supoclip-worker.conf /etc/supervisor/conf.d/
   sudo supervisorctl reread
   sudo supervisorctl update
   ```

3. Start via Supervisor:
   ```bash
   sudo supervisorctl start supoclip-worker:*
   ```

### From PM2

1. Stop PM2:
   ```bash
   pm2 stop supoclip-worker
   pm2 delete supoclip-worker
   ```

2. Follow normal Supervisor installation steps

## References

- [Supervisor Documentation](http://supervisord.org/)
- [Configuration Reference](http://supervisord.org/configuration.html)
- [Running Supervisor](http://supervisord.org/running.html)
