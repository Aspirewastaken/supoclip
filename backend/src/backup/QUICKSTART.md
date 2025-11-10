# Backup System Quick Start Guide

Get the SupoClip backup system up and running in 5 minutes.

## Step 1: Install Dependencies

```bash
cd backend

# Install boto3 for S3/B2 support
uv add boto3

# Install PostgreSQL client tools (for pg_dump/pg_restore)
# Ubuntu/Debian:
sudo apt-get update
sudo apt-get install postgresql-client

# macOS:
brew install postgresql
```

## Step 2: Configure Environment

```bash
# Copy the example environment file
cp src/backup/.env.example .env.backup

# Edit configuration
nano .env.backup
```

**Minimal configuration for local backups:**

```bash
# Local backup (no cloud)
BACKUP_STORAGE_BACKEND=local
BACKUP_DIR=/var/backups/supoclip
BACKUP_RETENTION_DAYS=30
BACKUP_COMPRESSION=true
BACKUP_INCREMENTAL=true
```

**Or, for cloud backups (S3):**

```bash
# S3 cloud backup
BACKUP_STORAGE_BACKEND=s3
BACKUP_S3_BUCKET=my-supoclip-backups
BACKUP_S3_REGION=us-east-1
BACKUP_S3_ACCESS_KEY=AKIA...
BACKUP_S3_SECRET_KEY=...
```

Add these settings to your main `backend/.env` file.

## Step 3: Test the Backup System

```bash
# Navigate to backend directory
cd backend

# Test configuration
python -m src.backup.cli config

# Create a test backup
python -m src.backup.cli backup db --full

# List backups
python -m src.backup.cli list

# Verify backup integrity
python -m src.backup.cli verify
```

## Step 4: Enable Automated Backups

### Option A: Integrate into FastAPI (Recommended)

Add to your `src/main.py` or `src/main_refactored.py`:

```python
from contextlib import asynccontextmanager
from src.backup import BackupConfig, BackupScheduler

backup_scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global backup_scheduler

    # Startup: Start backup scheduler
    backup_config = BackupConfig()
    backup_scheduler = BackupScheduler(backup_config)
    backup_scheduler.start()

    yield

    # Shutdown: Stop backup scheduler
    if backup_scheduler:
        backup_scheduler.stop()

# Create app with lifespan
app = FastAPI(lifespan=lifespan)
```

### Option B: Run as Separate Service

```bash
# Create a systemd service file
sudo nano /etc/systemd/system/supoclip-backup.service
```

```ini
[Unit]
Description=SupoClip Backup Scheduler
After=network.target postgresql.service

[Service]
Type=simple
User=supoclip
WorkingDirectory=/path/to/supoclip/backend
ExecStart=/path/to/supoclip/backend/.venv/bin/python -m src.backup.scheduler_service
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable supoclip-backup
sudo systemctl start supoclip-backup

# Check status
sudo systemctl status supoclip-backup
```

## Step 5: Verify Automated Backups

```bash
# Check scheduled jobs
python -m src.backup.cli config

# Wait for scheduled time, or trigger manually
curl -X POST http://localhost:8000/backup/database?backup_type=full

# Check backup status
python -m src.backup.cli completeness
```

## Common Workflows

### Daily Operations

```bash
# Check backup status
python -m src.backup.cli completeness

# View recent backups
python -m src.backup.cli list

# Verify backup integrity
python -m src.backup.cli verify
```

### Manual Backups

```bash
# Full database backup
python -m src.backup.cli backup db --full

# Incremental backup
python -m src.backup.cli backup db --incremental

# Backup all files
python -m src.backup.cli backup files

# Backup everything
python -m src.backup.cli backup all
```

### Restoration

```bash
# List available backups
python -m src.backup.cli list

# Restore database from latest backup
python -m src.backup.cli restore db --latest

# Restore from specific backup
python -m src.backup.cli restore db --file /var/backups/supoclip/database/supoclip_full_20250110_020000.sql.gz

# Restore files
python -m src.backup.cli restore files
```

### Maintenance

```bash
# Clean up old backups
python -m src.backup.cli cleanup

# Verify all backups
python -m src.backup.cli verify

# Check backup completeness
python -m src.backup.cli completeness
```

## Backup Schedule (Default)

By default, the system runs:

- **Daily 2:00 AM**: Incremental database backup
- **Weekly Monday 2:00 AM**: Full database backup
- **Daily 3:00 AM**: File backup (uploads & clips)
- **Daily 4:00 AM**: Backup verification
- **Weekly Tuesday 2:00 AM**: Cleanup old backups

Configure in `.env`:
```bash
BACKUP_DAILY_TIME=02:00
BACKUP_WEEKLY_DAY=0  # 0=Monday
```

## Monitoring

### Check Backup Status via API

```bash
# Get backup system status
curl http://localhost:8000/backup/status

# List all backups
curl http://localhost:8000/backup/list

# Trigger manual backup
curl -X POST http://localhost:8000/backup/database?backup_type=full
```

### Email/Webhook Notifications

Configure in `.env`:

```bash
# Email notifications
BACKUP_NOTIFICATION_EMAIL=admin@example.com

# Slack webhook
BACKUP_NOTIFICATION_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

You'll receive notifications for:
- ✅ Successful backups
- ❌ Failed backups
- ⚠️ Verification warnings
- 🧹 Cleanup reports

## Troubleshooting

### "pg_dump: command not found"

Install PostgreSQL client tools:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql-client

# macOS
brew install postgresql
```

### "Permission denied" on backup directory

```bash
# Create directory with correct permissions
sudo mkdir -p /var/backups/supoclip
sudo chown -R $USER:$USER /var/backups/supoclip
chmod 700 /var/backups/supoclip
```

### S3 upload fails

```bash
# Test AWS credentials
aws s3 ls s3://my-supoclip-backups/

# Or using boto3
python -c "import boto3; s3 = boto3.client('s3'); print(s3.list_buckets())"
```

### Backups taking too long

- Enable compression: `BACKUP_COMPRESSION=true`
- Use incremental backups: `BACKUP_INCREMENTAL=true`
- Schedule during low-traffic hours

## Next Steps

1. **Read the full documentation**: [README.md](./README.md)
2. **Set up disaster recovery plan**: [DISASTER_RECOVERY.md](./DISASTER_RECOVERY.md)
3. **Test a full restore**: Practice disaster recovery monthly
4. **Configure monitoring**: Set up notifications and alerts
5. **Review backup strategy**: Adjust retention and frequency as needed

## Getting Help

- **Check logs**: Look for detailed error messages
- **Run verification**: `python -m src.backup.cli verify`
- **Review configuration**: `python -m src.backup.cli config`
- **Read documentation**: Full docs in [README.md](./README.md)

## Quick Reference

| Task | Command |
|------|---------|
| Create full backup | `python -m src.backup.cli backup db --full` |
| Create file backup | `python -m src.backup.cli backup files` |
| List backups | `python -m src.backup.cli list` |
| Verify backups | `python -m src.backup.cli verify` |
| Restore database | `python -m src.backup.cli restore db --latest` |
| Restore files | `python -m src.backup.cli restore files` |
| Cleanup old backups | `python -m src.backup.cli cleanup` |
| Check status | `python -m src.backup.cli completeness` |
| Show config | `python -m src.backup.cli config` |

---

**Ready to backup? Start with:**

```bash
python -m src.backup.cli backup all
```
