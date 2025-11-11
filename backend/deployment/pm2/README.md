# PM2 Deployment

This directory contains PM2 configuration for SupoClip workers.

PM2 is a production process manager for Node.js applications, but it also works great for Python/ARQ workers.

## Installation

### 1. Install Node.js and PM2

**Ubuntu/Debian:**
```bash
# Install Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PM2 globally
sudo npm install -g pm2
```

**macOS:**
```bash
brew install node
npm install -g pm2
```

### 2. Create Log Directory

```bash
sudo mkdir -p /var/log/supoclip
sudo chown -R $USER:$USER /var/log/supoclip
```

### 3. Start Workers

```bash
cd /home/user/supoclip/backend/deployment/pm2

# Start with ecosystem file
pm2 start ecosystem.config.js

# Or start specific environment
pm2 start ecosystem.config.js --env production
pm2 start ecosystem.config.js --env staging
pm2 start ecosystem.config.js --env development
```

## Management Commands

### Status and Monitoring

```bash
# List all processes
pm2 list
pm2 ls

# Detailed status
pm2 status

# Show process details
pm2 show supoclip-worker

# Monitor in real-time
pm2 monit

# Dashboard (web UI)
pm2 plus
```

### Start/Stop/Restart

```bash
# Start all
pm2 start ecosystem.config.js

# Start specific app
pm2 start supoclip-worker

# Stop
pm2 stop supoclip-worker
pm2 stop all

# Restart
pm2 restart supoclip-worker
pm2 restart all

# Reload (0-second downtime)
pm2 reload supoclip-worker

# Delete from PM2
pm2 delete supoclip-worker
pm2 delete all
```

### Logs

```bash
# View all logs
pm2 logs

# View specific app logs
pm2 logs supoclip-worker

# View last N lines
pm2 logs supoclip-worker --lines 100

# Follow logs (like tail -f)
pm2 logs supoclip-worker --raw

# Clear logs
pm2 flush

# View log files directly
tail -f /var/log/supoclip/worker-out.log
tail -f /var/log/supoclip/worker-error.log
```

### Configuration Management

```bash
# Update ecosystem after changes
pm2 reload ecosystem.config.js

# Start with specific instance count
pm2 start ecosystem.config.js --only supoclip-worker -i 4

# Scale instances
pm2 scale supoclip-worker 5
pm2 scale supoclip-worker +2  # Add 2 more instances
pm2 scale supoclip-worker -1  # Remove 1 instance
```

## Auto-Start on Boot

### 1. Generate Startup Script

```bash
# Generate startup script for systemd
pm2 startup

# This will output a command like:
# sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u username --hp /home/username

# Run the command it outputs
```

### 2. Save Process List

```bash
# Save current PM2 process list
pm2 save

# This creates ~/.pm2/dump.pm2 with current processes
```

### 3. Test Reboot

```bash
sudo reboot

# After reboot, check PM2:
pm2 list
```

### 4. Disable Auto-Start (if needed)

```bash
pm2 unstartup systemd
```

## Scaling Workers

### Horizontal Scaling

**Option 1: Edit ecosystem.config.js**

```javascript
{
  name: 'supoclip-worker',
  instances: 4,  // Run 4 instances
}
```

**Option 2: Command line**

```bash
# Start with 4 instances
pm2 start ecosystem.config.js -i 4

# Scale to 6 instances
pm2 scale supoclip-worker 6

# Auto-scale based on CPU cores
pm2 start ecosystem.config.js -i max
```

### Load Balancing

PM2 automatically load balances across instances:

```bash
# Start with cluster mode
pm2 start ecosystem.config.js --instances max --exec-mode cluster
```

## Monitoring

### Built-in Monitoring

```bash
# Real-time monitoring
pm2 monit

# CPU and memory usage
pm2 list
```

### PM2 Plus (Cloud Monitoring)

1. **Sign up:** https://pm2.io/
2. **Link PM2:**
   ```bash
   pm2 link <secret_key> <public_key>
   ```
3. **Access dashboard:** https://app.pm2.io/

Features:
- Real-time monitoring
- Error tracking
- Log management
- Profiling
- Alerts

### Prometheus Integration

Install PM2 Prometheus exporter:

```bash
npm install -g pm2-prometheus-exporter

# Start exporter
pm2-prometheus-exporter

# Or add to ecosystem.config.js
```

Add to Prometheus:
```yaml
scrape_configs:
  - job_name: 'pm2'
    static_configs:
      - targets: ['localhost:9209']
```

## Advanced Configuration

### Environment Variables

**From .env file:**

```javascript
// ecosystem.config.js
{
  env_file: '/opt/supoclip/backend/.env',
}
```

**Inline:**

```javascript
{
  env: {
    REDIS_HOST: 'localhost',
    CUSTOM_VAR: 'value',
  }
}
```

### Process Configuration

```javascript
{
  // Cron restart
  cron_restart: '0 0 * * *',  // Restart daily at midnight

  // Exponential backoff
  exp_backoff_restart_delay: 100,

  // Memory monitoring
  max_memory_restart: '4G',

  // CPU monitoring
  max_cpu: 80,  // Restart if CPU > 80%
}
```

### Custom Metrics

```javascript
// In your worker code
const pmx = require('pmx');

pmx.action('queue depth', (reply) => {
  // Your logic to get queue depth
  reply({ depth: queueDepth });
});
```

## Deployment

### Simple Deployment

```bash
# On server
cd /opt/supoclip/backend
git pull
uv sync
pm2 reload ecosystem.config.js
```

### Automated Deployment

Use PM2's deploy feature:

```bash
# Setup (first time)
pm2 deploy ecosystem.config.js production setup

# Deploy
pm2 deploy ecosystem.config.js production

# Revert
pm2 deploy ecosystem.config.js production revert 1
```

### CI/CD Integration

**GitHub Actions:**

```yaml
# .github/workflows/deploy.yml
- name: Deploy with PM2
  run: |
    ssh user@server << 'EOF'
      cd /opt/supoclip/backend
      git pull
      uv sync
      pm2 reload ecosystem.config.js --env production
    EOF
```

**GitLab CI:**

```yaml
deploy:
  stage: deploy
  script:
    - ssh user@server "cd /opt/supoclip && git pull && pm2 reload ecosystem.config.js"
```

## Troubleshooting

### Worker Not Starting

1. **Check PM2 logs:**
   ```bash
   pm2 logs supoclip-worker --err
   ```

2. **Check process status:**
   ```bash
   pm2 describe supoclip-worker
   ```

3. **Test command manually:**
   ```bash
   cd /opt/supoclip/backend
   .venv/bin/arq src.workers.tasks.WorkerSettings
   ```

### Memory Issues

1. **Monitor memory:**
   ```bash
   pm2 monit
   ```

2. **Adjust limits:**
   ```javascript
   {
     max_memory_restart: '8G',
   }
   ```

3. **Enable memory profiling:**
   ```bash
   pm2 install pm2-profiler
   ```

### Process Keeps Restarting

1. **Check restart count:**
   ```bash
   pm2 list
   # Look at 'restart' column
   ```

2. **Increase minimum uptime:**
   ```javascript
   {
     min_uptime: '60s',
     max_restarts: 10,
   }
   ```

3. **Disable auto-restart temporarily:**
   ```bash
   pm2 stop supoclip-worker
   pm2 start supoclip-worker --no-autorestart
   ```

### Port Conflicts

PM2 doesn't handle ports, but if you're running multiple services:

```bash
# Check what's using a port
sudo lsof -i :6379
sudo netstat -tulpn | grep 6379
```

## Best Practices

1. **Resource Limits:**
   - Set `max_memory_restart`
   - Monitor with `pm2 monit`

2. **Logging:**
   - Use log rotation
   - Send logs to centralized logging (ELK, Loki)

3. **Scaling:**
   - Start with 1 instance
   - Scale based on queue depth
   - Use `instances: 'max'` for CPU-bound tasks

4. **Monitoring:**
   - Use PM2 Plus for production
   - Export metrics to Prometheus
   - Set up alerts for crashes

5. **Deployment:**
   - Always test in staging first
   - Use `pm2 reload` for zero-downtime
   - Keep ecosystem.config.js in version control

## Migration

### From Systemd

```bash
# Stop systemd service
sudo systemctl stop supoclip-worker
sudo systemctl disable supoclip-worker

# Start with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### From Supervisor

```bash
# Stop supervisor
sudo supervisorctl stop supoclip-worker:*
sudo rm /etc/supervisor/conf.d/supoclip-worker.conf
sudo supervisorctl reread

# Start with PM2
pm2 start ecosystem.config.js
```

## Useful Commands Reference

```bash
# Status
pm2 list
pm2 status
pm2 describe <name>
pm2 monit

# Start/Stop
pm2 start <name|id|file>
pm2 stop <name|id|all>
pm2 restart <name|id|all>
pm2 reload <name|id|all>
pm2 delete <name|id|all>

# Logs
pm2 logs [name]
pm2 logs --lines 200
pm2 flush  # Clear logs

# Monitoring
pm2 monit
pm2 plus

# Scaling
pm2 scale <name> <instances>

# Config
pm2 reload ecosystem.config.js
pm2 start ecosystem.config.js --env production

# Startup
pm2 startup
pm2 save
pm2 unstartup

# Updates
pm2 update  # Update PM2
pm2 resurrect  # Restore processes after update
```

## References

- [PM2 Documentation](https://pm2.keymetrics.io/)
- [Ecosystem File](https://pm2.keymetrics.io/docs/usage/application-declaration/)
- [PM2 Plus](https://pm2.io/)
- [Deployment](https://pm2.keymetrics.io/docs/usage/deployment/)
