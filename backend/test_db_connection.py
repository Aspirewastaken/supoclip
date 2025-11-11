#!/usr/bin/env python3
"""
Test database connection for SupoClip backend.
Tests async PostgreSQL connection using asyncpg.
"""

import asyncio
import os
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv

load_dotenv()


async def test_database_connection():
    """Test async database connection to PostgreSQL."""
    try:
        import asyncpg

        # Get database URL from environment
        database_url = os.getenv('DATABASE_URL')

        if not database_url:
            print("❌ ERROR: DATABASE_URL not set in environment")
            return False

        # asyncpg doesn't recognize 'postgresql+asyncpg://', only 'postgresql://'
        if 'postgresql+asyncpg://' in database_url:
            database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')

        print(f"📡 Testing connection to: {database_url.split('@')[1] if '@' in database_url else 'database'}")

        # Create connection
        conn = await asyncpg.connect(database_url)

        print("✅ Connection established!")

        # Test query: count tables
        tables_query = """
            SELECT COUNT(*) as table_count
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """

        result = await conn.fetchrow(tables_query)
        table_count = result['table_count']

        print(f"✅ Database query successful! Found {table_count} tables")

        # List all tables
        list_tables_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """

        tables = await conn.fetch(list_tables_query)

        print(f"\n📋 Tables in supoclip database:")
        for idx, row in enumerate(tables, 1):
            print(f"   {idx}. {row['table_name']}")

        # Test insert and delete (to verify write permissions)
        print(f"\n🔧 Testing write permissions...")

        test_user_query = """
            INSERT INTO users (id, name, email, "emailVerified")
            VALUES ($1, $2, $3, $4)
            RETURNING id, name, email
        """

        import uuid
        test_id = str(uuid.uuid4())
        test_email = f"test_{test_id[:8]}@example.com"

        inserted = await conn.fetchrow(
            test_user_query,
            test_id,
            "Test User",
            test_email,
            False
        )

        print(f"✅ Write test passed! Inserted user: {inserted['name']} ({inserted['email']})")

        # Clean up test user
        delete_query = "DELETE FROM users WHERE id = $1"
        await conn.execute(delete_query, test_id)

        print(f"✅ Cleanup successful! Deleted test user.")

        # Close connection
        await conn.close()

        print(f"\n" + "="*60)
        print(f"🎉 DATABASE CONNECTION TEST PASSED!")
        print(f"="*60)

        return True

    except ImportError as e:
        print(f"❌ ERROR: Missing required module: {e}")
        print(f"   Run: uv sync")
        return False

    except Exception as e:
        print(f"❌ ERROR: Database connection failed")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        return False


if __name__ == "__main__":
    print("="*60)
    print(" SupoClip Database Connection Test")
    print("="*60)
    print()

    success = asyncio.run(test_database_connection())

    exit(0 if success else 1)
