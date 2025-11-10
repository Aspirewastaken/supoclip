# SupoClip Backup and Recovery System

Comprehensive automated backup and recovery system for SupoClip, supporting database backups, file backups, and disaster recovery.

## Features

- **Automated Database Backups**
  - Full PostgreSQL dumps
  - Incremental backups
  - Schema-only backups
  - Compressed backups (gzip)

- **File Backups**
  - Original uploaded videos
  - Generated clips
  - Metadata and transcripts
  - Hash-based integrity verification

- **Multiple Storage Backends**
  - Local filesystem
  - AWS S3
  - Backblaze B2
  - Any S3-compatible storage

- **Automated Scheduling**
  - Daily incremental backups
  - Weekly full backups
  - Automatic cleanup of old backups
  - Configurable retention policies

- **Verification & Monitoring**
  - Automated backup verification
  - Integrity checks (SHA256 hashes)
  - Completeness monitoring
  - Email/webhook notifications

- **Recovery Tools**
  - Full system restoration
  - Selective table restoration
  - Individual file restoration
  - Test restoration without affecting production

## Installation

### Prerequisites

```bash
# Install required system tools
sudo apt-get install postgresql-client  # For pg_dump/pg_restore

# Install Python dependencies
cd backend
uv add apscheduler boto3 aiohttp
```

### Environment Variables

Add to your `backend/.env` file:

```bash
# Backup Configuration
BACKUP_DIR=/var/backups/supoclip
BACKUP_STORAGE_BACKEND=local  # or 's3', 'b2'
BACKUP_RETENTION_DAYS=30
BACKUP_COMPRESSION=true
BACKUP_ENCRYPTION=false

# S3/B2 Configuration (if using cloud storage)
BACKUP_S3_BUCKET=my-supoclip-backups
BACKUP_S3_REGION=us-east-1
BACKUP_S3_ACCESS_KEY=your_access_key
BACKUP_S3_SECRET_KEY=your_secret_key
# BACKUP_S3_ENDPOINT=https://s3.us-west-004.backblazeb2.com  # For B2

# Incremental Backup Settings
BACKUP_INCREMENTAL=true
BACKUP_FULL_INTERVAL_DAYS=7

# Schedule
BACKUP_DAILY_TIME=02:00  # 2 AM
BACKUP_WEEKLY_DAY=0      # 0=Monday, 6=Sunday

# Verification
BACKUP_VERIFY=true

# Notifications (optional)
BACKUP_NOTIFICATION_EMAIL=admin@example.com
BACKUP_NOTIFICATION_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## Usage

### Command-Line Interface

The backup system includes a comprehensive CLI tool:

```bash
# Show configuration
python -m src.backup.cli config

# Create backups
python -m src.backup.cli backup db --full
python -m src.backup.cli backup db --incremental
python -m src.backup.cli backup db --schema
python -m src.backup.cli backup files
python -m src.backup.cli backup all

# List backups
python -m src.backup.cli list
python -m src.backup.cli list --type full

# Verify backups
python -m src.backup.cli verify

# Check backup completeness
python -m src.backup.cli completeness

# Restore from backups
python -m src.backup.cli restore db --latest
python -m src.backup.cli restore db --file /path/to/backup.sql.gz
python -m src.backup.cli restore files --category uploads
python -m src.backup.cli restore all

# Cleanup old backups
python -m src.backup.cli cleanup
```

### Programmatic Usage

```python
from src.backup import BackupConfig, DatabaseBackup, FileBackup, RestoreManager

# Initialize
config = BackupConfig()
db_backup = DatabaseBackup(config)
file_backup = FileBackup(config)
restore = RestoreManager(config)

# Create backups
await db_backup.create_full_backup()
await file_backup.backup_all_files()

# Restore
await restore.restore_database_full()
await restore.restore_all_files()
```

### Automated Scheduling

The scheduler runs automatically when integrated into your FastAPI application:

```python
from src.backup import BackupConfig, BackupScheduler

# In your FastAPI lifespan/startup
scheduler = BackupScheduler(BackupConfig())
scheduler.start()

# In your shutdown
scheduler.stop()
```

## Backup Strategy

### Database Backups

1. **Full Backups** (Weekly)
   - Complete database dump
   - All tables, indexes, and data
   - Compressed with gzip
   - Uploaded to remote storage

2. **Incremental Backups** (Daily)
   - Only changed data since last full backup
   - Based on `updated_at` timestamps
   - Smaller size, faster execution
   - Requires full backup for restoration

3. **Schema Backups** (Weekly)
   - Database structure only
   - Useful for version control
   - Quick disaster recovery planning

### File Backups

1. **Uploaded Videos** (`uploads/`)
   - Original user-uploaded files
   - Downloaded YouTube videos
   - Backed up daily

2. **Generated Clips** (`clips/`)
   - All processed video clips
   - Backed up daily

3. **Metadata**
   - Transcript cache files
   - Processing metadata
   - Configuration files

### Retention Policy

- **Default**: 30 days
- **Full backups**: Kept longer (configurable)
- **Incremental backups**: Cleaned up after corresponding full backup expires
- **Old backups**: Automatically deleted from both local and remote storage

## Storage Backends

### Local Storage

Best for development and testing:

```bash
BACKUP_STORAGE_BACKEND=local
BACKUP_DIR=/var/backups/supoclip
```

### AWS S3

Production-ready cloud storage:

```bash
BACKUP_STORAGE_BACKEND=s3
BACKUP_S3_BUCKET=my-supoclip-backups
BACKUP_S3_REGION=us-east-1
BACKUP_S3_ACCESS_KEY=AKIA...
BACKUP_S3_SECRET_KEY=...
```

**S3 Bucket Policy Example:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-supoclip-backups/*",
        "arn:aws:s3:::my-supoclip-backups"
      ]
    }
  ]
}
```

### Backblaze B2

Cost-effective alternative to S3:

```bash
BACKUP_STORAGE_BACKEND=b2
BACKUP_S3_BUCKET=my-supoclip-backups
BACKUP_S3_ACCESS_KEY=<keyID>
BACKUP_S3_SECRET_KEY=<applicationKey>
```

B2 is ~1/4 the cost of S3 with similar reliability.

## Disaster Recovery

See [DISASTER_RECOVERY.md](./DISASTER_RECOVERY.md) for detailed procedures.

### Quick Recovery Steps

1. **Restore Database**
   ```bash
   python -m src.backup.cli restore db --latest
   ```

2. **Restore Files**
   ```bash
   python -m src.backup.cli restore files
   ```

3. **Verify System**
   ```bash
   python -m src.backup.cli verify
   ```

### Recovery Time Objectives (RTO)

- **Database**: 5-15 minutes
- **Files**: 30-120 minutes (depending on size)
- **Full System**: 1-3 hours

### Recovery Point Objectives (RPO)

- **Database**: 24 hours (daily backups)
- **Files**: 24 hours (daily backups)
- **Critical data**: 1 hour (with hourly incrementals, if enabled)

## Monitoring

### Backup Verification

Automated verification runs after each backup:

1. **File Integrity**: SHA256 hash comparison
2. **Database Validity**: SQL structure validation
3. **Completeness**: All expected files present
4. **Restoration Test**: Test restore to temporary database

### Notifications

Configure notifications for:

- Backup completion (success/failure)
- Verification results
- Cleanup reports
- Completeness warnings

**Slack Webhook Example:**

```bash
BACKUP_NOTIFICATION_WEBHOOK=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXX
```

**Email Notification:**

```bash
BACKUP_NOTIFICATION_EMAIL=admin@example.com
```

## Backup Directory Structure

```
/var/backups/supoclip/
├── database/
│   ├── supoclip_full_20250110_020000.sql.gz
│   ├── supoclip_full_20250110_020000.sql.gz.meta.json
│   ├── supoclip_incremental_20250111_020000.sql.gz
│   ├── supoclip_schema_20250110_020000.sql
│   └── tables/
│       └── supoclip_table_tasks_20250110_120000.sql.gz
├── files/
│   ├── uploads/
│   │   └── 20250110/
│   │       └── video1.mp4
│   └── clips/
│       └── 20250110/
│           └── clip1.mp4
├── metadata/
│   ├── files/
│   │   └── 20250110_020000_video1.mp4.meta.json
│   ├── reports/
│   │   └── file_backup_report_20250110_020000.json
│   ├── verification/
│   │   └── verification_report_20250110_040000.json
│   └── restore_records/
│       └── restore_20250110_100000.json
├── restore/
│   └── restore_report_20250110_100000.json
└── verification/
    └── temp files (cleaned up automatically)
```

## Security

### Backup Encryption

Enable encryption for sensitive data:

```bash
BACKUP_ENCRYPTION=true
BACKUP_ENCRYPTION_KEY=your-secure-encryption-key
```

**Note**: Encryption is currently a placeholder. Implement using tools like:
- GPG for file encryption
- AWS KMS for S3 server-side encryption
- Database-level encryption

### Access Control

- **S3 Buckets**: Use IAM policies with least privilege
- **Local Storage**: Restrict directory permissions (700)
- **Database Credentials**: Store in secure environment variables

### Audit Trail

All backup and restore operations are logged:
- Timestamp and user
- Operation type
- Success/failure status
- Files affected

## Performance Optimization

### Database Backups

- **Parallel Dumps**: Use `pg_dump --jobs=4` for large databases
- **Compression**: Level 6 gzip (balance between speed and size)
- **Timing**: Schedule during low-traffic hours (2-4 AM)

### File Backups

- **Concurrent Uploads**: Limit to 5 simultaneous uploads
- **Chunk Size**: 8KB for hash calculation
- **Incremental**: Only backup new/modified files

### Network Optimization

- **S3 Transfer Acceleration**: Enable for faster uploads
- **Multipart Upload**: For files >100MB
- **Compression**: Always compress before upload

## Troubleshooting

### Common Issues

**1. "pg_dump: command not found"**
```bash
sudo apt-get install postgresql-client
```

**2. "Permission denied" on backup directory**
```bash
sudo chown -R $USER:$USER /var/backups/supoclip
chmod 700 /var/backups/supoclip
```

**3. S3 upload fails**
- Check AWS credentials
- Verify bucket exists and region is correct
- Check IAM permissions

**4. Backup size too large**
- Enable compression
- Adjust retention policy
- Use incremental backups more frequently

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Best Practices

1. **Test Restores Regularly**: Monthly restore tests to verify backups work
2. **Monitor Backup Size**: Track growth over time
3. **Multiple Storage Locations**: Local + cloud for redundancy
4. **Version Control Schemas**: Commit schema backups to git
5. **Document Recovery Procedures**: Keep disaster recovery plan updated
6. **Rotate Credentials**: Regularly update S3/B2 keys
7. **Encrypt Sensitive Data**: Enable encryption for production
8. **Monitor Notifications**: Ensure alerts are being received

## Support

For issues or questions:
- Check logs: `backend/logs/backup.log`
- Review verification reports: `backups/metadata/verification/`
- Run completeness check: `python -m src.backup.cli completeness`

## License

Part of the SupoClip project. See main LICENSE file.
