#!/bin/bash
#
# Database Migration Testing Script
# Tests migrations for idempotency and correctness
#
# Usage:
#   ./scripts/test_migrations.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test database URL
TEST_DB_URL="${TEST_DATABASE_URL:-postgresql://localhost:5432/supoclip_test}"

echo ""
echo "================================================"
echo "  Database Migration Test Suite"
echo "================================================"
echo ""
echo "Test Database: $TEST_DB_URL"
echo ""

# Extract test database name
TEST_DB_NAME=$(echo "$TEST_DB_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')
BASE_URL=$(echo "$TEST_DB_URL" | sed 's/\/[^/]*$/\/postgres/')

# Function to run test
run_test() {
    local test_name=$1
    local test_function=$2

    echo -e "${BLUE}TEST: $test_name${NC}"

    if $test_function; then
        echo -e "${GREEN}✓ PASS${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo ""
        return 1
    fi
}

# Function to create test database
create_test_db() {
    echo "Creating test database..."
    psql "$BASE_URL" -c "DROP DATABASE IF EXISTS $TEST_DB_NAME;" || true
    psql "$BASE_URL" -c "CREATE DATABASE $TEST_DB_NAME;"
}

# Function to drop test database
drop_test_db() {
    echo "Dropping test database..."
    psql "$BASE_URL" -c "DROP DATABASE IF EXISTS $TEST_DB_NAME;" || true
}

# Test 1: Fresh install
test_fresh_install() {
    create_test_db
    DATABASE_URL="$TEST_DB_URL" ./scripts/run_migrations.sh --skip-init=false > /dev/null 2>&1
    return $?
}

# Test 2: Idempotency (run migrations twice)
test_idempotency() {
    create_test_db
    DATABASE_URL="$TEST_DB_URL" ./scripts/run_migrations.sh > /dev/null 2>&1 || return 1
    DATABASE_URL="$TEST_DB_URL" ./scripts/run_migrations.sh --skip-init > /dev/null 2>&1
    return $?
}

# Test 3: Table count
test_table_count() {
    create_test_db
    DATABASE_URL="$TEST_DB_URL" ./scripts/run_migrations.sh > /dev/null 2>&1

    local count=$(psql "$TEST_DB_URL" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)

    # Expected: 19 tables (may vary based on which migrations are applied)
    # users, tasks, sources, generated_clips, webhooks, webhook_deliveries,
    # session, account, verification, experiments, experiment_results,
    # usage_tracking, clip_views, clip_performance, calendar_credentials,
    # scheduled_posts, social_scheduled_posts, social_media_accounts, post_attempts

    if [ "$count" -ge 18 ]; then
        echo "  Found $count tables (expected >= 18)"
        return 0
    else
        echo "  Found $count tables (expected >= 18)"
        return 1
    fi
}

# Test 4: No duplicate table names
test_no_duplicate_tables() {
    create_test_db
    DATABASE_URL="$TEST_DB_URL" ./scripts/run_migrations.sh > /dev/null 2>&1

    # Check for scheduled_posts conflict
    local calendar_scheduled=$(psql "$TEST_DB_URL" -t -c "
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = 'scheduled_posts' AND column_name = 'calendar_event_id';
    " | xargs)

    local social_scheduled=$(psql "$TEST_DB_URL" -t -c "
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = 'social_scheduled_posts' AND column_name = 'platforms';
    " | xargs)

    if [ "$calendar_scheduled" -eq 1 ] && [ "$social_scheduled" -eq 1 ]; then
        echo "  ✓ scheduled_posts (calendar) exists"
        echo "  ✓ social_scheduled_posts (social) exists"
        return 0
    else
        echo "  ✗ Table conflict not resolved"
        return 1
    fi
}

# Test 5: Foreign key constraints
test_foreign_keys() {
    create_test_db
    DATABASE_URL="$TEST_DB_URL" ./scripts/run_migrations.sh > /dev/null 2>&1

    local fk_count=$(psql "$TEST_DB_URL" -t -c "
        SELECT COUNT(*)
        FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY';
    " | xargs)

    # Expected: ~30+ foreign keys
    if [ "$fk_count" -ge 25 ]; then
        echo "  Found $fk_count foreign keys (expected >= 25)"
        return 0
    else
        echo "  Found $fk_count foreign keys (expected >= 25)"
        return 1
    fi
}

# Test 6: Indexes
test_indexes() {
    create_test_db
    DATABASE_URL="$TEST_DB_URL" ./scripts/run_migrations.sh > /dev/null 2>&1

    local idx_count=$(psql "$TEST_DB_URL" -t -c "
        SELECT COUNT(*)
        FROM pg_indexes
        WHERE schemaname = 'public';
    " | xargs)

    # Expected: 50+ indexes (including primary keys)
    if [ "$idx_count" -ge 40 ]; then
        echo "  Found $idx_count indexes (expected >= 40)"
        return 0
    else
        echo "  Found $idx_count indexes (expected >= 40)"
        return 1
    fi
}

# Test 7: Triggers
test_triggers() {
    create_test_db
    DATABASE_URL="$TEST_DB_URL" ./scripts/run_migrations.sh > /dev/null 2>&1

    local trigger_count=$(psql "$TEST_DB_URL" -t -c "
        SELECT COUNT(*)
        FROM information_schema.triggers
        WHERE trigger_schema = 'public';
    " | xargs)

    # Expected: ~18 triggers (one per table with updated_at/updatedAt)
    if [ "$trigger_count" -ge 15 ]; then
        echo "  Found $trigger_count triggers (expected >= 15)"
        return 0
    else
        echo "  Found $trigger_count triggers (expected >= 15)"
        return 1
    fi
}

# Test 8: Check constraints
test_check_constraints() {
    create_test_db
    DATABASE_URL="$TEST_DB_URL" ./scripts/run_migrations.sh > /dev/null 2>&1

    local check_count=$(psql "$TEST_DB_URL" -t -c "
        SELECT COUNT(*)
        FROM information_schema.table_constraints
        WHERE constraint_type = 'CHECK';
    " | xargs)

    # Expected: 30+ check constraints
    if [ "$check_count" -ge 25 ]; then
        echo "  Found $check_count check constraints (expected >= 25)"
        return 0
    else
        echo "  Found $check_count check constraints (expected >= 25)"
        return 1
    fi
}

# Test 9: Insert test data
test_insert_data() {
    create_test_db
    DATABASE_URL="$TEST_DB_URL" ./scripts/run_migrations.sh > /dev/null 2>&1

    # Insert a test user
    psql "$TEST_DB_URL" -c "
        INSERT INTO users (id, name, email, \"emailVerified\", \"createdAt\", \"updatedAt\")
        VALUES ('test-user-1', 'Test User', 'test@example.com', false, NOW(), NOW());
    " > /dev/null 2>&1 || return 1

    # Insert a test task
    psql "$TEST_DB_URL" -c "
        INSERT INTO tasks (id, user_id, status, created_at, updated_at)
        VALUES ('test-task-1', 'test-user-1', 'pending', NOW(), NOW());
    " > /dev/null 2>&1 || return 1

    # Verify cascade delete works
    psql "$TEST_DB_URL" -c "DELETE FROM users WHERE id = 'test-user-1';" > /dev/null 2>&1 || return 1

    local task_count=$(psql "$TEST_DB_URL" -t -c "SELECT COUNT(*) FROM tasks WHERE id = 'test-task-1';" | xargs)

    if [ "$task_count" -eq 0 ]; then
        echo "  ✓ Cascade delete works"
        return 0
    else
        echo "  ✗ Cascade delete failed"
        return 1
    fi
}

# Test 10: Check for missing tables
test_required_tables() {
    create_test_db
    DATABASE_URL="$TEST_DB_URL" ./scripts/run_migrations.sh > /dev/null 2>&1

    local required_tables=(
        "users"
        "tasks"
        "sources"
        "generated_clips"
        "webhooks"
        "webhook_deliveries"
        "experiments"
        "experiment_results"
        "usage_tracking"
        "clip_views"
        "clip_performance"
        "calendar_credentials"
        "scheduled_posts"
        "social_media_accounts"
        "post_attempts"
    )

    local missing=()

    for table in "${required_tables[@]}"; do
        local exists=$(psql "$TEST_DB_URL" -t -c "
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = '$table'
            );
        " | xargs)

        if [ "$exists" != "t" ]; then
            missing+=("$table")
        fi
    done

    if [ ${#missing[@]} -eq 0 ]; then
        echo "  ✓ All required tables exist"
        return 0
    else
        echo "  ✗ Missing tables: ${missing[*]}"
        return 1
    fi
}

# Run all tests
TESTS_PASSED=0
TESTS_FAILED=0

run_test "Fresh installation" test_fresh_install && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
run_test "Idempotency (run twice)" test_idempotency && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
run_test "Table count" test_table_count && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
run_test "No duplicate tables" test_no_duplicate_tables && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
run_test "Foreign key constraints" test_foreign_keys && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
run_test "Indexes" test_indexes && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
run_test "Triggers" test_triggers && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
run_test "Check constraints" test_check_constraints && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
run_test "Insert and cascade delete" test_insert_data && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
run_test "Required tables exist" test_required_tables && ((TESTS_PASSED++)) || ((TESTS_FAILED++))

# Clean up
drop_test_db

# Summary
echo "================================================"
echo "  Test Results"
echo "================================================"
echo ""
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""
    exit 1
fi
