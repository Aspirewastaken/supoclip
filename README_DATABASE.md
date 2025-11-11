# Database Documentation

This directory contains comprehensive database schema documentation and migration tools for SupoClip.

## 📚 Documentation

Start with the index file for navigation:
- **[DATABASE_AUDIT_INDEX.md](./DATABASE_AUDIT_INDEX.md)** - Master index and navigation guide

### Quick Links by Role

**For Executives:**
- [Executive Summary](./DATABASE_AUDIT_SUMMARY.md) - Critical issues and action plan

**For Database Administrators:**
- [Complete Audit Report](./DATABASE_SCHEMA_AUDIT_REPORT.md) - Full technical analysis

**For Developers:**
- [Quick Reference Guide](./DATABASE_QUICK_REFERENCE.md) - Common queries and howtos
- [Schema Diagram](./DATABASE_SCHEMA_DIAGRAM.md) - Visual ERD

## 🚨 Critical Issues

There are **3 critical issues** that must be resolved before production:

1. **Table Name Conflict:** `scheduled_posts` table defined twice
2. **Missing SQLAlchemy Models:** Social media tables not in ORM
3. **Migration Naming Conflict:** Multiple files named `001_*.sql`

See [DATABASE_AUDIT_SUMMARY.md](./DATABASE_AUDIT_SUMMARY.md) for details and fixes.

## 🛠️ Tools

### Migration Scripts
- `./scripts/run_migrations.sh` - Execute all migrations
- `./scripts/test_migrations.sh` - Test migration integrity

### Migration Files
- `./migrations/003_fix_scheduled_posts_conflict.sql` - Fix table conflict
- `./backend/migrations/MISSING_MODELS.py` - SQLAlchemy model templates

## 📊 Schema Overview

- **19 tables** (users, tasks, clips, analytics, integrations)
- **~30 foreign keys** (proper cascade actions)
- **~60 indexes** (optimized for queries)
- **~18 triggers** (auto-update timestamps)
- **~35 check constraints** (data validation)

See [DATABASE_SCHEMA_DIAGRAM.md](./DATABASE_SCHEMA_DIAGRAM.md) for complete ERD.

## 🚀 Quick Start

```bash
# 1. Read the summary (5 min)
cat DATABASE_AUDIT_SUMMARY.md

# 2. Test migrations (10 min)
export TEST_DATABASE_URL="postgresql://localhost:5432/supoclip_test"
./scripts/test_migrations.sh

# 3. Apply fixes (1 hour)
# Follow instructions in DATABASE_AUDIT_SUMMARY.md

# 4. Run migrations (5 min)
export DATABASE_URL="postgresql://user:pass@localhost:5432/supoclip"
./scripts/run_migrations.sh --backup
```

## 📖 Full Documentation List

1. [DATABASE_AUDIT_INDEX.md](./DATABASE_AUDIT_INDEX.md) - Master index
2. [DATABASE_AUDIT_SUMMARY.md](./DATABASE_AUDIT_SUMMARY.md) - Executive summary
3. [DATABASE_SCHEMA_AUDIT_REPORT.md](./DATABASE_SCHEMA_AUDIT_REPORT.md) - Complete report
4. [DATABASE_SCHEMA_DIAGRAM.md](./DATABASE_SCHEMA_DIAGRAM.md) - ERD diagram
5. [DATABASE_QUICK_REFERENCE.md](./DATABASE_QUICK_REFERENCE.md) - Query reference

Total: ~77 KB, ~18,000 words of documentation

## ⚠️ Before You Deploy

- [ ] Fix scheduled_posts conflict
- [ ] Add missing SQLAlchemy models
- [ ] Rename migration files
- [ ] Run test suite (10/10 pass)
- [ ] Backup production database

## 📞 Support

- **Quick questions:** [DATABASE_QUICK_REFERENCE.md](./DATABASE_QUICK_REFERENCE.md)
- **Technical issues:** [DATABASE_SCHEMA_AUDIT_REPORT.md](./DATABASE_SCHEMA_AUDIT_REPORT.md)
- **Architecture questions:** [DATABASE_SCHEMA_DIAGRAM.md](./DATABASE_SCHEMA_DIAGRAM.md)
- **Team chat:** #database channel

---

**Audit Date:** 2025-11-10
**Status:** ⚠️ Requires Action
**Priority:** HIGH
