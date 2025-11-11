#!/bin/bash
#
# Database Migration Execution Script
# Run all migrations in the correct order
#
# Usage:
#   ./scripts/run_migrations.sh [options]
#
# Options:
#   --fresh         Drop and recreate database (WARNING: DESTROYS ALL DATA)
#   --dry-run       Show SQL without executing
#   --backup        Create backup before running migrations
#   --skip-init     Skip init.sql (for existing databases)
#
# Environment Variables:
#   DATABASE_URL    PostgreSQL connection string (required)
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check for DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}ERROR: DATABASE_URL environment variable not set${NC}"
    echo "Example: export DATABASE_URL='postgresql://user:pass@localhost:5432/supoclip'"
    exit 1
fi

# Parse command line arguments
FRESH=false
DRY_RUN=false
BACKUP=false
SKIP_INIT=false

for arg in "$@"; do
    case $arg in
        --fresh)
            FRESH=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --backup)
            BACKUP=true
            shift
            ;;
        --skip-init)
            SKIP_INIT=true
            shift
            ;;
        --help)
            echo "Database Migration Script"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --fresh      Drop and recreate database (WARNING: DESTROYS ALL DATA)"
            echo "  --dry-run    Show SQL without executing"
            echo "  --backup     Create backup before running migrations"
            echo "  --skip-init  Skip init.sql (for existing databases)"
            echo "  --help       Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $arg${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to execute SQL file
execute_sql() {
    local file=$1
    local description=$2

    echo -e "${BLUE}▶ $description${NC}"
    echo -e "  File: $(basename $file)"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}  [DRY RUN] Would execute: $file${NC}"
        return 0
    fi

    if psql "$DATABASE_URL" -f "$file" > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ Success${NC}"
        return 0
    else
        echo -e "${RED}  ✗ Failed${NC}"
        psql "$DATABASE_URL" -f "$file"  # Run again to show error
        return 1
    fi
}

# Function to create backup
create_backup() {
    local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    local backup_path="$PROJECT_ROOT/backups/$backup_file"

    echo -e "${BLUE}Creating backup: $backup_file${NC}"

    mkdir -p "$PROJECT_ROOT/backups"

    if pg_dump "$DATABASE_URL" > "$backup_path"; then
        echo -e "${GREEN}✓ Backup created: $backup_path${NC}"
        return 0
    else
        echo -e "${RED}✗ Backup failed${NC}"
        return 1
    fi
}

# Function to drop and recreate database
drop_and_recreate() {
    echo -e "${RED}WARNING: About to drop and recreate database${NC}"
    echo -e "${YELLOW}This will DESTROY ALL DATA!${NC}"
    echo ""
    read -p "Are you sure? Type 'yes' to continue: " confirm

    if [ "$confirm" != "yes" ]; then
        echo "Aborted."
        exit 1
    fi

    # Extract database name from DATABASE_URL
    DB_NAME=$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')

    # Connection URL without database name
    BASE_URL=$(echo "$DATABASE_URL" | sed 's/\/[^/]*$/\/postgres/')

    echo -e "${BLUE}Dropping database: $DB_NAME${NC}"
    psql "$BASE_URL" -c "DROP DATABASE IF EXISTS $DB_NAME;" || true

    echo -e "${BLUE}Creating database: $DB_NAME${NC}"
    psql "$BASE_URL" -c "CREATE DATABASE $DB_NAME;"

    echo -e "${GREEN}✓ Database recreated${NC}"
}

# Main execution
echo ""
echo "================================================"
echo "  SupoClip Database Migration Script"
echo "================================================"
echo ""
echo "Database: $DATABASE_URL"
echo "Fresh install: $FRESH"
echo "Dry run: $DRY_RUN"
echo "Backup: $BACKUP"
echo "Skip init: $SKIP_INIT"
echo ""

# Create backup if requested
if [ "$BACKUP" = true ] && [ "$DRY_RUN" = false ]; then
    create_backup || exit 1
    echo ""
fi

# Drop and recreate if requested
if [ "$FRESH" = true ] && [ "$DRY_RUN" = false ]; then
    drop_and_recreate
    echo ""
fi

# Migration execution order
echo "================================================"
echo "  Executing Migrations"
echo "================================================"
echo ""

MIGRATION_COUNT=0

# Step 1: Base schema (init.sql)
if [ "$SKIP_INIT" = false ]; then
    if [ -f "$PROJECT_ROOT/init.sql" ]; then
        execute_sql "$PROJECT_ROOT/init.sql" "Base Schema (init.sql)" || exit 1
        ((MIGRATION_COUNT++))
        echo ""
    else
        echo -e "${YELLOW}⚠ init.sql not found, skipping${NC}"
        echo ""
    fi
fi

# Step 2: User roles and quotas (must come early for user table modifications)
if [ -f "$PROJECT_ROOT/migrations/001_add_user_roles_and_quotas.sql" ]; then
    execute_sql "$PROJECT_ROOT/migrations/001_add_user_roles_and_quotas.sql" "User Roles & Quotas" || exit 1
    ((MIGRATION_COUNT++))
    echo ""
fi

# Step 3: Progress fields (extends tasks table)
if [ -f "$PROJECT_ROOT/backend/migrations/001_add_progress_fields.sql" ]; then
    execute_sql "$PROJECT_ROOT/backend/migrations/001_add_progress_fields.sql" "Task Progress Fields" || exit 1
    ((MIGRATION_COUNT++))
    echo ""
fi

# Step 4: Webhooks (independent feature)
if [ -f "$PROJECT_ROOT/backend/migrations/001_add_webhooks_table.sql" ]; then
    execute_sql "$PROJECT_ROOT/backend/migrations/001_add_webhooks_table.sql" "Webhooks System" || exit 1
    ((MIGRATION_COUNT++))
    echo ""
fi

# Step 5: Channel name (extends sources table)
if [ -f "$PROJECT_ROOT/backend/migrations/001_add_channel_name_to_sources.sql" ]; then
    execute_sql "$PROJECT_ROOT/backend/migrations/001_add_channel_name_to_sources.sql" "Source Channel Names" || exit 1
    ((MIGRATION_COUNT++))
    echo ""
fi

# Step 6: Analytics tables (independent feature)
if [ -f "$PROJECT_ROOT/backend/migrations/001_add_analytics_tables.sql" ]; then
    execute_sql "$PROJECT_ROOT/backend/migrations/001_add_analytics_tables.sql" "Analytics System" || exit 1
    ((MIGRATION_COUNT++))
    echo ""
fi

# Step 7: Calendar integration (independent feature)
if [ -f "$PROJECT_ROOT/backend/migrations/001_add_calendar_tables.sql" ]; then
    execute_sql "$PROJECT_ROOT/backend/migrations/001_add_calendar_tables.sql" "Calendar Integration" || exit 1
    ((MIGRATION_COUNT++))
    echo ""
fi

# Step 8: CDN URL (extends generated_clips table)
if [ -f "$PROJECT_ROOT/backend/migrations/add_cdn_url_to_clips.sql" ]; then
    execute_sql "$PROJECT_ROOT/backend/migrations/add_cdn_url_to_clips.sql" "CDN URL Support" || exit 1
    ((MIGRATION_COUNT++))
    echo ""
fi

# Step 9: Fix scheduled_posts conflict (CRITICAL - must run before social media migration)
if [ -f "$PROJECT_ROOT/migrations/003_fix_scheduled_posts_conflict.sql" ]; then
    execute_sql "$PROJECT_ROOT/migrations/003_fix_scheduled_posts_conflict.sql" "Fix Scheduled Posts Conflict" || exit 1
    ((MIGRATION_COUNT++))
    echo ""
fi

# Step 10: Social media integration (depends on conflict fix)
if [ -f "$PROJECT_ROOT/migrations/002_social_media_integrations.sql" ]; then
    # Modify the SQL file to use social_scheduled_posts instead of scheduled_posts
    # We'll create a temporary modified version
    TEMP_SOCIAL_MIGRATION="/tmp/002_social_media_integrations_fixed.sql"

    sed 's/CREATE TABLE scheduled_posts/CREATE TABLE IF NOT EXISTS social_scheduled_posts/g' \
        "$PROJECT_ROOT/migrations/002_social_media_integrations.sql" | \
    sed 's/ON scheduled_posts(/ON social_scheduled_posts(/g' | \
    sed 's/REFERENCES scheduled_posts(/REFERENCES social_scheduled_posts(/g' | \
    sed 's/update_scheduled_posts_updated_at/update_social_scheduled_posts_updated_at/g' \
        > "$TEMP_SOCIAL_MIGRATION"

    execute_sql "$TEMP_SOCIAL_MIGRATION" "Social Media Integration (FIXED)" || exit 1
    rm -f "$TEMP_SOCIAL_MIGRATION"
    ((MIGRATION_COUNT++))
    echo ""
else
    echo -e "${YELLOW}⚠ Social media migration not found at migrations/002_social_media_integrations.sql${NC}"
    echo ""
fi

# Summary
echo "================================================"
echo "  Migration Summary"
echo "================================================"
echo ""
echo -e "${GREEN}✓ Successfully executed $MIGRATION_COUNT migrations${NC}"
echo ""

# Verify tables
echo "================================================"
echo "  Verifying Tables"
echo "================================================"
echo ""

if [ "$DRY_RUN" = false ]; then
    echo "Tables in database:"
    psql "$DATABASE_URL" -c "\dt" || true
    echo ""

    echo "Table counts:"
    psql "$DATABASE_URL" -c "
        SELECT
            schemaname,
            COUNT(*) as table_count
        FROM pg_tables
        WHERE schemaname = 'public'
        GROUP BY schemaname;
    " || true
    echo ""

    echo "Expected tables:"
    cat <<EOF
  ✓ users
  ✓ tasks
  ✓ sources
  ✓ generated_clips
  ✓ webhooks
  ✓ webhook_deliveries
  ✓ session
  ✓ account
  ✓ verification
  ✓ experiments
  ✓ experiment_results
  ✓ usage_tracking
  ✓ clip_views
  ✓ clip_performance
  ✓ calendar_credentials
  ✓ scheduled_posts (calendar version)
  ✓ social_scheduled_posts (social media version)
  ✓ social_media_accounts
  ✓ post_attempts
EOF
    echo ""
fi

echo -e "${GREEN}Migration complete!${NC}"
echo ""

# Warn about manual steps
echo "================================================"
echo "  ⚠️  Manual Steps Required"
echo "================================================"
echo ""
echo "1. Add missing SQLAlchemy models to backend/src/models.py"
echo "   See: backend/migrations/MISSING_MODELS.py"
echo ""
echo "2. Update Prisma schema at frontend/prisma/schema.prisma"
echo "   Add: generated_clips, webhooks, experiments, analytics tables"
echo ""
echo "3. Run Prisma generate:"
echo "   cd frontend && npx prisma generate"
echo ""
echo "4. Test the application:"
echo "   - Backend: cd backend && uvicorn src.main:app --reload"
echo "   - Frontend: cd frontend && npm run dev"
echo ""
echo "5. Review the full audit report:"
echo "   cat DATABASE_SCHEMA_AUDIT_REPORT.md"
echo ""
