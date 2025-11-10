# SupoClip Disaster Recovery Guide

This document provides step-by-step procedures for recovering from various disaster scenarios.

## Table of Contents

- [Overview](#overview)
- [Disaster Scenarios](#disaster-scenarios)
- [Recovery Procedures](#recovery-procedures)
- [Emergency Contacts](#emergency-contacts)
- [Post-Recovery Checklist](#post-recovery-checklist)

## Overview

### Recovery Objectives

- **RTO (Recovery Time Objective)**: 2-4 hours for full system restoration
- **RPO (Recovery Point Objective)**: 24 hours maximum data loss (last backup)

### Prerequisites

Before a disaster occurs, ensure:

1. ✅ Backups are running automatically (verify with `python -m src.backup.cli completeness`)
2. ✅ Remote storage (S3/B2) is configured and tested
3. ✅ Backup verification is enabled and passing
4. ✅ All team members have access to this document
5. ✅ Database credentials are securely stored (password manager)
6. ✅ S3/B2 credentials are available
7. ✅ Recent restore test completed successfully

### Backup Locations

**Primary**: Local server at `/var/backups/supoclip`

**Secondary**: Remote storage
- S3: `s3://my-supoclip-backups/`
- B2: Backblaze bucket

**Tertiary** (recommended): Off-site backup copy

## Disaster Scenarios

### Scenario 1: Database Corruption

**Symptoms:**
- Database connection errors
- Data inconsistencies
- PostgreSQL won't start
- Corrupted table errors

**Impact:** High - Application completely down

**Recovery Time:** 15-30 minutes

---

### Scenario 2: Accidental Data Deletion

**Symptoms:**
- User reports missing data
- Tables are empty or incomplete
- Accidental DELETE/DROP query

**Impact:** Medium - Partial data loss

**Recovery Time:** 30-60 minutes

---

### Scenario 3: Complete Server Failure

**Symptoms:**
- Server won't boot
- Hardware failure
- Data center outage
- Complete disk failure

**Impact:** Critical - Total system loss

**Recovery Time:** 2-4 hours

---

### Scenario 4: Ransomware Attack

**Symptoms:**
- Files encrypted
- Database locked
- Ransom note present

**Impact:** Critical - System compromised

**Recovery Time:** 4-8 hours (includes security audit)

---

### Scenario 5: File Storage Corruption

**Symptoms:**
- Videos won't play
- Clips are corrupted
- Storage errors

**Impact:** Medium - Video processing affected

**Recovery Time:** 1-3 hours

---

## Recovery Procedures

### Procedure 1: Database Recovery

**Use for:** Database corruption, accidental deletion

**Steps:**

1. **Assess the Damage**
   ```bash
   # Check database status
   psql -U supoclip -d supoclip -c "SELECT version();"

   # Check table counts
   psql -U supoclip -d supoclip -c "SELECT COUNT(*) FROM tasks;"
   ```

2. **Stop Application Services**
   ```bash
   # Stop backend
   docker-compose stop backend worker

   # Or if running directly
   pkill -f "uvicorn src.main:app"
   ```

3. **Backup Current State** (even if corrupted)
   ```bash
   # Create emergency backup
   pg_dump -U supoclip supoclip > /tmp/emergency_backup_$(date +%Y%m%d_%H%M%S).sql
   ```

4. **List Available Backups**
   ```bash
   python -m src.backup.cli list
   ```

5. **Choose Restore Point**
   - Use latest full backup if entire database is corrupted
   - Use incremental backups for recent data if available

6. **Perform Restoration**
   ```bash
   # Restore from latest backup
   python -m src.backup.cli restore db --latest

   # Or restore from specific backup
   python -m src.backup.cli restore db --file /var/backups/supoclip/database/supoclip_full_20250110_020000.sql.gz
   ```

7. **Verify Restoration**
   ```bash
   # Check database
   psql -U supoclip -d supoclip -c "SELECT COUNT(*) FROM tasks;"
   psql -U supoclip -d supoclip -c "SELECT * FROM tasks ORDER BY created_at DESC LIMIT 5;"
   ```

8. **Restart Services**
   ```bash
   docker-compose up -d backend worker
   ```

9. **Verify Application**
   - Check API: `curl http://localhost:8000/health`
   - Test video processing
   - Check frontend access

**Rollback Plan:**
If restoration fails, restore from emergency backup:
```bash
psql -U supoclip -d supoclip < /tmp/emergency_backup_*.sql
```

---

### Procedure 2: Selective Table Recovery

**Use for:** Specific table corruption, accidental table deletion

**Steps:**

1. **Identify Affected Table**
   ```bash
   # List tables
   psql -U supoclip -d supoclip -c "\dt"
   ```

2. **Backup Current Table** (if exists)
   ```bash
   pg_dump -U supoclip -t tasks supoclip > /tmp/tasks_backup_$(date +%Y%m%d_%H%M%S).sql
   ```

3. **Drop Corrupted Table** (if needed)
   ```sql
   DROP TABLE IF EXISTS tasks CASCADE;
   ```

4. **Restore Table from Backup**
   ```bash
   python -m src.backup.cli restore db --latest
   ```

   Or manually:
   ```bash
   gunzip -c /var/backups/supoclip/database/supoclip_full_20250110_020000.sql.gz | \
       psql -U supoclip -d supoclip
   ```

5. **Verify Table**
   ```bash
   psql -U supoclip -d supoclip -c "SELECT COUNT(*) FROM tasks;"
   ```

---

### Procedure 3: File Recovery

**Use for:** Deleted videos, corrupted clips, missing files

**Steps:**

1. **Identify Missing Files**
   ```bash
   # Check uploads directory
   ls -la /app/uploads/

   # Check clips directory
   ls -la /app/clips/
   ```

2. **List Available File Backups**
   ```bash
   python -m src.backup.cli list
   ```

3. **Restore Specific Category**
   ```bash
   # Restore all uploads
   python -m src.backup.cli restore files --category uploads

   # Restore all clips
   python -m src.backup.cli restore files --category clips

   # Restore everything
   python -m src.backup.cli restore files
   ```

4. **Verify Files**
   ```bash
   # Check file counts
   find /app/uploads -type f | wc -l
   find /app/clips -type f | wc -l
   ```

5. **Test Video Playback**
   - Access clip URLs through API
   - Verify videos play correctly

---

### Procedure 4: Full System Recovery (New Server)

**Use for:** Complete server failure, migration to new server

**Steps:**

1. **Prepare New Server**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh

   # Install PostgreSQL client tools
   sudo apt-get update
   sudo apt-get install postgresql-client

   # Clone repository
   git clone https://github.com/yourusername/supoclip.git
   cd supoclip
   ```

2. **Configure Environment**
   ```bash
   # Copy .env files
   cp backend/.env.example backend/.env
   # Edit with correct values
   nano backend/.env
   ```

3. **Start PostgreSQL**
   ```bash
   docker-compose up -d postgres

   # Wait for PostgreSQL to be ready
   docker-compose logs -f postgres
   ```

4. **Download Latest Backup**

   If using S3:
   ```bash
   # Install AWS CLI
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install

   # Configure AWS
   aws configure

   # Download latest backup
   aws s3 cp s3://my-supoclip-backups/database/ /tmp/backups/ --recursive
   ```

   If using B2:
   ```bash
   # Install B2 CLI
   pip install b2

   # Authenticate
   b2 authorize-account <key_id> <application_key>

   # Download latest backup
   b2 sync b2://my-supoclip-backups/database/ /tmp/backups/
   ```

5. **Restore Database**
   ```bash
   # Find latest backup
   ls -lt /tmp/backups/supoclip_full_*.sql.gz | head -1

   # Restore
   gunzip -c /tmp/backups/supoclip_full_20250110_020000.sql.gz | \
       docker exec -i supoclip-postgres psql -U supoclip -d supoclip
   ```

6. **Restore Files**
   ```bash
   # Create directories
   mkdir -p /var/supoclip/uploads /var/supoclip/clips

   # Download from S3
   aws s3 sync s3://my-supoclip-backups/files/uploads/ /var/supoclip/uploads/
   aws s3 sync s3://my-supoclip-backups/files/clips/ /var/supoclip/clips/

   # Or from B2
   b2 sync b2://my-supoclip-backups/files/uploads/ /var/supoclip/uploads/
   b2 sync b2://my-supoclip-backups/files/clips/ /var/supoclip/clips/
   ```

7. **Update Docker Volumes**
   ```yaml
   # In docker-compose.yml, update volume paths if needed
   volumes:
     - /var/supoclip/uploads:/app/uploads
     - /var/supoclip/clips:/app/clips
   ```

8. **Start All Services**
   ```bash
   docker-compose up -d
   ```

9. **Verify System**
   ```bash
   # Check all services
   docker-compose ps

   # Check logs
   docker-compose logs -f backend

   # Test API
   curl http://localhost:8000/health

   # Test frontend
   curl http://localhost:3000
   ```

10. **Update DNS** (if applicable)
    - Point domain to new server IP
    - Update load balancer configuration
    - Verify SSL certificates

---

### Procedure 5: Ransomware Recovery

**Use for:** System compromise, encryption attack

**⚠️ CRITICAL: Do NOT pay ransom. Follow these steps immediately.**

**Steps:**

1. **Isolate System**
   ```bash
   # Disconnect from network immediately
   sudo ifconfig eth0 down

   # Or pull network cable
   ```

2. **Document Attack**
   - Take screenshots of ransom note
   - Note file extensions of encrypted files
   - Record time of discovery
   - Save logs immediately

3. **Notify Security Team**
   - Alert system administrators
   - Contact security incident response team
   - File police report if required

4. **DO NOT Delete Anything**
   - Keep encrypted files for analysis
   - Don't reboot or shutdown
   - Preserve evidence

5. **Assess Damage on Clean System**
   - Boot from live CD or use separate computer
   - Check which files are encrypted
   - Verify backups are not affected

6. **Prepare Clean Server**
   - Use fresh server/VM
   - Do not restore from any local backups (may be infected)
   - Only use verified remote backups

7. **Restore from Remote Backups**
   ```bash
   # Download backups from REMOTE storage only
   aws s3 cp s3://my-supoclip-backups/database/supoclip_full_20250110_020000.sql.gz /tmp/

   # Verify backup integrity
   python -m src.backup.cli verify
   ```

8. **Restore System** (follow Procedure 4)

9. **Security Hardening**
   ```bash
   # Update all packages
   sudo apt-get update && sudo apt-get upgrade

   # Change all passwords
   # Rotate all API keys
   # Update database credentials
   ```

10. **Malware Scan**
    ```bash
    # Install ClamAV
    sudo apt-get install clamav

    # Update definitions
    sudo freshclam

    # Scan restored files
    sudo clamscan -r /var/supoclip/
    ```

11. **Monitor for Reinfection**
    - Watch logs for unusual activity
    - Monitor network traffic
    - Check for new unknown processes

---

## Testing Disaster Recovery

### Monthly Test Restore

Perform a test restore monthly to verify backups work:

```bash
# 1. Create test database
createdb -U supoclip supoclip_test

# 2. Restore to test database
python -m src.backup.cli restore db --latest

# 3. Verify data
psql -U supoclip -d supoclip_test -c "SELECT COUNT(*) FROM tasks;"

# 4. Cleanup
dropdb -U supoclip supoclip_test
```

### Quarterly Full DR Test

Every quarter, perform a complete disaster recovery simulation:

1. Provision new test server
2. Restore database from backups
3. Restore all files
4. Verify application functionality
5. Document time taken and issues encountered
6. Update procedures based on learnings

---

## Emergency Contacts

### Primary Contacts

| Role | Name | Email | Phone |
|------|------|-------|-------|
| System Administrator | TBD | admin@example.com | +1-xxx-xxx-xxxx |
| Database Administrator | TBD | dba@example.com | +1-xxx-xxx-xxxx |
| DevOps Lead | TBD | devops@example.com | +1-xxx-xxx-xxxx |

### Service Providers

| Service | Support Email | Support Phone | Portal |
|---------|--------------|---------------|--------|
| AWS | aws-support@amazon.com | 1-800-xxx-xxxx | console.aws.amazon.com |
| Backblaze B2 | help@backblaze.com | 1-650-xxx-xxxx | secure.backblaze.com |
| PostgreSQL | - | - | postgresql.org/support |

### Escalation Path

1. **Level 1**: On-call engineer (responds within 15 minutes)
2. **Level 2**: Senior DevOps (responds within 30 minutes)
3. **Level 3**: CTO/Technical Director (responds within 1 hour)

---

## Post-Recovery Checklist

After completing disaster recovery:

### Immediate (within 1 hour)

- [ ] All services are running
- [ ] Database is accessible
- [ ] API endpoints respond correctly
- [ ] Frontend is accessible
- [ ] Video processing works
- [ ] Users can log in

### Short-term (within 24 hours)

- [ ] Verify data integrity (sample checks)
- [ ] Check all recent tasks completed
- [ ] Review error logs
- [ ] Notify users of any data loss
- [ ] Update status page

### Medium-term (within 1 week)

- [ ] Complete data audit
- [ ] Root cause analysis documented
- [ ] Post-mortem meeting held
- [ ] Update recovery procedures
- [ ] Implement preventive measures
- [ ] Test new backups

### Long-term (within 1 month)

- [ ] Security audit completed
- [ ] Infrastructure improvements implemented
- [ ] Backup strategy reviewed
- [ ] Monitoring enhanced
- [ ] Team training conducted
- [ ] Documentation updated

---

## Prevention Best Practices

### Daily

- Monitor backup job success/failure
- Check disk space on backup storage
- Review system logs for anomalies

### Weekly

- Verify latest backups exist
- Check backup file sizes (detect corruption)
- Review backup verification reports

### Monthly

- Perform test restore
- Review and update recovery procedures
- Audit access controls
- Check backup retention compliance

### Quarterly

- Full disaster recovery drill
- Security audit
- Rotate credentials
- Review and update contact lists

---

## Common Issues and Solutions

### Issue: Backup restore hangs

**Solution:**
```bash
# Check database connections
psql -U supoclip -d supoclip -c "SELECT * FROM pg_stat_activity;"

# Kill hanging connections
psql -U supoclip -d supoclip -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='supoclip';"
```

### Issue: Out of disk space during restore

**Solution:**
```bash
# Check disk usage
df -h

# Clean up old logs
docker system prune -a

# Expand volume (cloud provider specific)
```

### Issue: Backup file corrupted

**Solution:**
- Try previous backup
- Download from remote storage again
- Use incremental backups to rebuild

### Issue: Database version mismatch

**Solution:**
```bash
# Check PostgreSQL versions
psql --version
pg_dump --version

# Upgrade PostgreSQL if needed
docker-compose down
# Update docker-compose.yml to new version
docker-compose up -d
```

---

## Appendix: Recovery Metrics

Track these metrics for each recovery:

- **Time to Detect**: When disaster was discovered
- **Time to Decide**: When decision to restore was made
- **Time to Restore**: How long restoration took
- **Data Lost**: Time range of lost data (if any)
- **Services Affected**: Which services were down
- **Users Impacted**: Number of users affected
- **Root Cause**: What caused the disaster
- **Preventive Actions**: Steps taken to prevent recurrence

---

## Document Maintenance

**Last Updated**: 2025-01-10

**Review Schedule**: Monthly

**Document Owner**: DevOps Team

**Change Log**:
- 2025-01-10: Initial version
- Future updates will be listed here

---

## Additional Resources

- [Backup System README](./README.md)
- [PostgreSQL Backup Documentation](https://www.postgresql.org/docs/current/backup.html)
- [AWS S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/best-practices.html)
- [Docker Disaster Recovery](https://docs.docker.com/engine/swarm/admin_guide/#back-up-the-swarm)
