# SupoClip Worker Deployment Configurations

This directory contains deployment configurations for SupoClip ARQ workers across different process managers and platforms.

## Directory Structure

```
deployment/
├── systemd/           # Systemd service files (Linux)
│   ├── supoclip-worker.service
│   └── README.md
├── supervisor/        # Supervisor configuration
│   ├── supoclip-worker.conf
│   └── README.md
├── pm2/              # PM2 configuration
│   ├── ecosystem.config.js
│   └── README.md
└── README.md         # This file
```

## Quick Start

Choose the deployment method that best fits your environment:

### Docker Compose (Recommended for Development)

```bash
# Start all services including worker
docker compose up -d

# Check worker logs
docker compose logs -f worker

# Restart worker
docker compose restart worker
```

See: `/home/user/supoclip/docker-compose.yml`

---

### Systemd (Recommended for Production - Linux)

Best for: Ubuntu, Debian, CentOS, RHEL, Fedora

```bash
# Copy service file
sudo cp systemd/supoclip-worker.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable supoclip-worker
sudo systemctl start supoclip-worker

# Check status
sudo systemctl status supoclip-worker
```

See: [`systemd/README.md`](systemd/README.md)

---

### Supervisor (Alternative for Linux)

Best for: When you need fine-grained process control

```bash
# Install Supervisor
sudo apt-get install supervisor

# Copy configuration
sudo cp supervisor/supoclip-worker.conf /etc/supervisor/conf.d/

# Load and start
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start supoclip-worker:*
```

See: [`supervisor/README.md`](supervisor/README.md)

---

### PM2 (Cross-Platform)

Best for: Node.js environments, easy scaling

```bash
# Install PM2
npm install -g pm2

# Start workers
cd pm2
pm2 start ecosystem.config.js

# Enable auto-start
pm2 startup
pm2 save
```

See: [`pm2/README.md`](pm2/README.md)

---

### Kubernetes (Cloud/Container Orchestration)

Best for: Large-scale deployments, multi-region

See: [Kubernetes deployment guide](#kubernetes-deployment) below

---

## Comparison Matrix

| Feature | Docker Compose | Systemd | Supervisor | PM2 | Kubernetes |
|---------|---------------|---------|------------|-----|------------|
| **Complexity** | Low | Medium | Low | Low | High |
| **Auto-restart** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Auto-scale** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Monitoring** | Basic | Journalctl | Web UI | PM2 Plus | Full Stack |
| **Resource Limits** | ✅ | ✅ | ⚠️ | ⚠️ | ✅ |
| **Multi-server** | ❌ | Manual | Manual | PM2 Deploy | ✅ |
| **Zero-downtime** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Best For** | Dev | Production | Simple Prod | Node.js Env | Enterprise |

---

## Deployment Decision Tree

```
┌─ Are you using Docker?
│  ├─ Yes → Use Docker Compose
│  └─ No ↓
│
├─ Are you on Linux?
│  ├─ Yes → Use Systemd (recommended)
│  └─ No ↓
│
├─ Do you need easy scaling?
│  ├─ Yes → Use PM2 or Kubernetes
│  └─ No → Use Supervisor or Systemd
│
└─ Large-scale deployment?
   ├─ Yes → Use Kubernetes
   └─ No → Use Systemd or PM2
```

---

## Prerequisites

### All Deployments

1. **Python Environment:**
   ```bash
   cd /opt/supoclip/backend
   uv venv .venv
   uv sync
   ```

2. **Redis Running:**
   ```bash
   # Docker
   docker run -d -p 6379:6379 redis:7-alpine

   # System package
   sudo apt-get install redis-server
   sudo systemctl start redis
   ```

3. **PostgreSQL Running:**
   ```bash
   # Docker
   docker run -d -p 5432:5432 \
     -e POSTGRES_PASSWORD=supoclip_password \
     postgres:15

   # System package
   sudo apt-get install postgresql
   ```

4. **Environment Variables:**
   ```bash
   cp .env.example .env
   nano .env  # Fill in values
   ```

5. **Create User (Linux):**
   ```bash
   sudo useradd -r -s /bin/false supoclip
   sudo chown -R supoclip:supoclip /opt/supoclip
   ```

---

## Production Checklist

Before deploying to production:

- [ ] Choose deployment method
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure log rotation
- [ ] Set resource limits
- [ ] Enable auto-start on boot
- [ ] Set up alerting (PagerDuty, Slack)
- [ ] Test restart scenarios
- [ ] Test failure scenarios
- [ ] Document runbook
- [ ] Set up backups
- [ ] Configure firewall rules
- [ ] Use strong Redis password
- [ ] Use strong database password
- [ ] Enable HTTPS
- [ ] Set up SSL certificates
- [ ] Configure CDN (if applicable)
- [ ] Test scaling procedures
- [ ] Create disaster recovery plan

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (EKS, GKE, AKS, or self-hosted)
- kubectl configured
- Docker images built and pushed to registry

### Deployment YAML

Create `k8s/worker-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: supoclip-worker
  labels:
    app: supoclip
    component: worker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: supoclip
      component: worker
  template:
    metadata:
      labels:
        app: supoclip
        component: worker
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
    spec:
      containers:
      - name: worker
        image: your-registry/supoclip-backend:latest
        command: [".venv/bin/arq"]
        args: ["src.workers.tasks.WorkerSettings"]

        env:
        - name: PYTHONPATH
          value: "/app"
        - name: PYTHONUNBUFFERED
          value: "1"
        - name: REDIS_HOST
          value: "redis-service"
        - name: REDIS_PORT
          value: "6379"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: supoclip-secrets
              key: database-url
        - name: ASSEMBLY_AI_API_KEY
          valueFrom:
            secretKeyRef:
              name: supoclip-secrets
              key: assembly-ai-key

        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"

        livenessProbe:
          exec:
            command:
            - python
            - -c
            - "import redis; r = redis.Redis(host='redis-service'); r.ping()"
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 5
          failureThreshold: 3

        readinessProbe:
          exec:
            command:
            - python
            - -c
            - "import redis; r = redis.Redis(host='redis-service'); r.ping()"
          initialDelaySeconds: 10
          periodSeconds: 10

        volumeMounts:
        - name: uploads
          mountPath: /app/uploads
        - name: clips
          mountPath: /app/clips

      volumes:
      - name: uploads
        persistentVolumeClaim:
          claimName: supoclip-uploads-pvc
      - name: clips
        persistentVolumeClaim:
          claimName: supoclip-clips-pvc

      restartPolicy: Always

---
apiVersion: v1
kind: Service
metadata:
  name: supoclip-worker
  labels:
    app: supoclip
    component: worker
spec:
  type: ClusterIP
  selector:
    app: supoclip
    component: worker
  ports:
  - port: 8000
    targetPort: 8000
    name: metrics

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: supoclip-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: supoclip-worker
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: queue_depth
      target:
        type: AverageValue
        averageValue: "10"
```

### Secrets

Create `k8s/secrets.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: supoclip-secrets
type: Opaque
stringData:
  database-url: "postgresql+asyncpg://user:pass@host:5432/db"
  assembly-ai-key: "your-key-here"
  openai-key: "your-key-here"
```

### Deploy

```bash
# Apply secrets (do this first!)
kubectl apply -f k8s/secrets.yaml

# Apply deployment
kubectl apply -f k8s/worker-deployment.yaml

# Check status
kubectl get pods -l component=worker
kubectl logs -f -l component=worker

# Scale manually
kubectl scale deployment supoclip-worker --replicas=5

# Check HPA
kubectl get hpa
```

---

## Monitoring Setup

### Prometheus + Grafana

1. **Install monitoring stack:**
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
   ```

2. **Access dashboards:**
   - Grafana: http://localhost:3001 (admin/admin)
   - Prometheus: http://localhost:9090

3. **Import dashboard:**
   - Open Grafana
   - Import dashboard from `/home/user/supoclip/monitoring/grafana/dashboards/supoclip-overview.json`

See: `/home/user/supoclip/MONITORING.md`

---

## Troubleshooting

### Worker Won't Start

1. **Check logs:**
   ```bash
   # Docker
   docker compose logs worker

   # Systemd
   sudo journalctl -u supoclip-worker -n 100

   # Supervisor
   sudo supervisorctl tail -f supoclip-worker:supoclip-worker_01

   # PM2
   pm2 logs supoclip-worker
   ```

2. **Check dependencies:**
   ```bash
   # Redis
   redis-cli ping
   # Should return: PONG

   # PostgreSQL
   psql -U supoclip -d supoclip -c "SELECT 1"
   # Should return: 1
   ```

3. **Test manually:**
   ```bash
   cd /opt/supoclip/backend
   .venv/bin/arq src.workers.tasks.WorkerSettings
   ```

### High Memory Usage

1. **Check current usage:**
   ```bash
   # Docker
   docker stats supoclip-worker

   # System
   ps aux | grep arq
   ```

2. **Adjust limits:**
   - Docker: Edit `docker-compose.yml`
   - Systemd: Edit `MemoryMax` in service file
   - PM2: Edit `max_memory_restart` in ecosystem.config.js

### Queue Backing Up

1. **Check queue depth:**
   ```bash
   redis-cli LLEN arq:queue:supoclip_tasks
   ```

2. **Scale workers:**
   ```bash
   # Docker
   docker compose up -d --scale worker=3

   # PM2
   pm2 scale supoclip-worker 5

   # Kubernetes
   kubectl scale deployment supoclip-worker --replicas=5
   ```

---

## Performance Tuning

### Worker Count

**Formula:** `Workers = CPU Cores * 1-2`

Example:
- 4 CPU cores → 4-8 workers
- 8 CPU cores → 8-16 workers

### Resource Allocation

**Per Worker:**
- Memory: 2-4 GB
- CPU: 1-2 cores
- Disk: 10-50 GB (for temp files)

**Total System:**
- Redis: 1-2 GB RAM
- PostgreSQL: 2-4 GB RAM
- System: 1-2 GB RAM

### Optimization Tips

1. **Use local SSD for temp files**
2. **Enable Redis persistence**
3. **Use connection pooling**
4. **Enable HTTP caching**
5. **Use CDN for clips**
6. **Enable gzip compression**
7. **Use async I/O**
8. **Monitor queue depth**

---

## Security Hardening

### System User

```bash
# Create dedicated user
sudo useradd -r -s /bin/false supoclip

# Restrict permissions
sudo chown -R supoclip:supoclip /opt/supoclip
sudo chmod 750 /opt/supoclip/backend
```

### File Permissions

```bash
# Protect environment file
chmod 600 /opt/supoclip/backend/.env

# Protect uploads directory
chmod 750 /opt/supoclip/backend/uploads
```

### Network Security

```bash
# Firewall rules (ufw)
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw deny 6379/tcp  # Redis (internal only)
sudo ufw deny 5432/tcp  # PostgreSQL (internal only)
sudo ufw enable
```

### Redis Security

```bash
# /etc/redis/redis.conf
requirepass your_strong_password
bind 127.0.0.1
protected-mode yes
```

---

## Backup and Disaster Recovery

### Database Backups

```bash
# PostgreSQL backup
pg_dump -U supoclip supoclip > backup-$(date +%Y%m%d).sql

# Automated daily backup
0 2 * * * pg_dump -U supoclip supoclip | gzip > /backups/db-$(date +\%Y\%m\%d).sql.gz
```

### Redis Backups

```bash
# Manual backup
redis-cli SAVE

# Copy RDB file
cp /var/lib/redis/dump.rdb /backups/redis-$(date +%Y%m%d).rdb
```

### Application Backups

```bash
# Backup uploads and clips
tar -czf /backups/media-$(date +%Y%m%d).tar.gz \
  /opt/supoclip/backend/uploads \
  /opt/supoclip/backend/clips
```

---

## Support and Documentation

- **Main Documentation:** `/home/user/supoclip/backend/WORKER_VERIFICATION_REPORT.md`
- **Test Script:** `/home/user/supoclip/backend/test_worker_queue.py`
- **Monitoring Guide:** `/home/user/supoclip/MONITORING.md`
- **Docker Compose:** `/home/user/supoclip/docker-compose.yml`

---

## Quick Reference

### Environment Variables

```bash
# Required
REDIS_HOST=localhost
REDIS_PORT=6379
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
TEMP_DIR=/app/uploads

# API Keys
ASSEMBLY_AI_API_KEY=your_key
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
GOOGLE_API_KEY=your_key
OPENROUTER_API_KEY=your_key
```

### Common Commands

```bash
# Check worker status
docker compose ps worker                    # Docker
sudo systemctl status supoclip-worker       # Systemd
sudo supervisorctl status supoclip-worker:* # Supervisor
pm2 status supoclip-worker                  # PM2

# View logs
docker compose logs -f worker               # Docker
sudo journalctl -u supoclip-worker -f       # Systemd
sudo supervisorctl tail -f supoclip-worker  # Supervisor
pm2 logs supoclip-worker                    # PM2

# Restart
docker compose restart worker               # Docker
sudo systemctl restart supoclip-worker      # Systemd
sudo supervisorctl restart supoclip-worker  # Supervisor
pm2 restart supoclip-worker                 # PM2
```

---

**Last Updated:** 2025-11-10
**Version:** 1.0.0
**Agent:** AGENT 7 - Worker System Verification
