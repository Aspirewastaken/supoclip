"""
Quota Check Middleware
Enforces usage quotas based on user roles
"""
from datetime import datetime
from typing import Dict, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User
from ..database import AsyncSessionLocal


class QuotaExceededError(Exception):
    """Raised when user exceeds their quota"""
    def __init__(self, message: str, current_usage: int, quota_limit: int, remaining: int):
        self.message = message
        self.current_usage = current_usage
        self.quota_limit = quota_limit
        self.remaining = remaining
        super().__init__(self.message)


class QuotaChecker:
    """Handle quota checking and usage tracking"""

    ROLE_QUOTAS = {
        "free": 10,
        "pro": 500,
        "admin": -1,  # -1 means unlimited
    }

    @staticmethod
    def get_quota_for_role(role: str) -> int:
        """Get quota limit for a given role"""
        return QuotaChecker.ROLE_QUOTAS.get(role, 0)

    @staticmethod
    async def check_user_quota(
        user_id: str,
        db: Optional[AsyncSession] = None,
        clips_to_generate: int = 1
    ) -> Dict[str, any]:
        """
        Check if user has available quota

        Args:
            user_id: User ID to check
            db: Optional database session (creates new one if not provided)
            clips_to_generate: Number of clips about to be generated

        Returns:
            Dict with quota information:
            {
                "has_quota": bool,
                "current_usage": int,
                "quota_limit": int,
                "remaining": int,
                "role": str
            }

        Raises:
            QuotaExceededError: If user exceeds quota
        """
        close_db = False
        if db is None:
            db = AsyncSessionLocal()
            close_db = True

        try:
            now = datetime.now()
            month = now.month
            year = now.year

            # Call PostgreSQL function to check quota
            query = text("""
                SELECT * FROM check_user_quota(:user_id, :month, :year)
            """)

            result = await db.execute(
                query,
                {"user_id": user_id, "month": month, "year": year}
            )
            quota_info = result.fetchone()

            if not quota_info:
                raise Exception("Failed to check user quota")

            has_quota, current_usage, quota_limit, remaining = quota_info

            # Get user role for response
            user_query = text("SELECT role FROM users WHERE id = :user_id")
            user_result = await db.execute(user_query, {"user_id": user_id})
            user_row = user_result.fetchone()
            role = user_row[0] if user_row else "free"

            quota_data = {
                "has_quota": bool(has_quota),
                "current_usage": int(current_usage),
                "quota_limit": int(quota_limit),
                "remaining": int(remaining),
                "role": role
            }

            # Check if user has enough quota for the number of clips to generate
            if quota_limit != -1 and remaining < clips_to_generate:
                raise QuotaExceededError(
                    f"Quota exceeded. You have {remaining} clips remaining, but need {clips_to_generate}.",
                    current_usage=current_usage,
                    quota_limit=quota_limit,
                    remaining=remaining
                )

            return quota_data

        finally:
            if close_db:
                await db.close()

    @staticmethod
    async def increment_usage(
        user_id: str,
        clips_count: int = 1,
        db: Optional[AsyncSession] = None
    ) -> int:
        """
        Increment user's usage count

        Args:
            user_id: User ID
            clips_count: Number of clips to add to usage
            db: Optional database session

        Returns:
            New usage count
        """
        close_db = False
        if db is None:
            db = AsyncSessionLocal()
            close_db = True

        try:
            now = datetime.now()
            month = now.month
            year = now.year

            # Call PostgreSQL function to increment usage
            query = text("""
                SELECT increment_usage(:user_id, :month, :year, :increment)
            """)

            result = await db.execute(
                query,
                {
                    "user_id": user_id,
                    "month": month,
                    "year": year,
                    "increment": clips_count
                }
            )
            new_usage = result.scalar()
            await db.commit()

            return int(new_usage)

        finally:
            if close_db:
                await db.close()

    @staticmethod
    async def get_usage_stats(
        user_id: str,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, any]:
        """
        Get detailed usage statistics for a user

        Returns:
            Dict with usage stats including current month and historical data
        """
        close_db = False
        if db is None:
            db = AsyncSessionLocal()
            close_db = True

        try:
            now = datetime.now()
            month = now.month
            year = now.year

            # Get current month quota info
            quota_info = await QuotaChecker.check_user_quota(user_id, db)

            # Get historical usage (last 6 months)
            history_query = text("""
                SELECT month, year, clips_generated, created_at
                FROM usage_tracking
                WHERE user_id = :user_id
                ORDER BY year DESC, month DESC
                LIMIT 6
            """)

            result = await db.execute(history_query, {"user_id": user_id})
            history = [
                {
                    "month": row[0],
                    "year": row[1],
                    "clips_generated": row[2],
                    "created_at": row[3].isoformat() if row[3] else None
                }
                for row in result.fetchall()
            ]

            return {
                "current_month": {
                    "month": month,
                    "year": year,
                    **quota_info
                },
                "history": history
            }

        finally:
            if close_db:
                await db.close()


async def check_quota_middleware(user_id: str, clips_to_generate: int = 1):
    """
    Middleware function to check quota before processing

    Usage in FastAPI:
        quota_info = await check_quota_middleware(user_id, clips_count)
        # Continue with processing if no exception raised

    Raises:
        QuotaExceededError: If quota exceeded
    """
    return await QuotaChecker.check_user_quota(user_id, clips_to_generate=clips_to_generate)
