"""
Quota and Billing Management Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
from pydantic import BaseModel

from ...database import get_db
from ...middleware.quota_check import QuotaChecker, QuotaExceededError

router = APIRouter(prefix="/quota", tags=["Quota & Usage"])


class QuotaResponse(BaseModel):
    """Response model for quota information"""
    has_quota: bool
    current_usage: int
    quota_limit: int
    remaining: int
    role: str
    percentage_used: float


class UsageStatsResponse(BaseModel):
    """Response model for detailed usage statistics"""
    current_month: dict
    history: list


class UpdateRoleRequest(BaseModel):
    """Request model for updating user role"""
    role: str


@router.get(
    "/check",
    response_model=QuotaResponse,
    summary="Check User Quota",
    description="Check current user's quota status and remaining clips for the month"
)
async def check_quota(
    user_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Check if the current user has available quota

    Returns:
        - has_quota: Whether user has quota available
        - current_usage: Number of clips generated this month
        - quota_limit: Maximum clips allowed per month (-1 for unlimited)
        - remaining: Clips remaining this month
        - role: User's current role (free, pro, admin)
        - percentage_used: Percentage of quota used
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="user_id header required")

    try:
        quota_info = await QuotaChecker.check_user_quota(user_id, db)

        # Calculate percentage used
        if quota_info["quota_limit"] == -1:
            percentage_used = 0.0  # Unlimited
        else:
            percentage_used = (quota_info["current_usage"] / quota_info["quota_limit"]) * 100 if quota_info["quota_limit"] > 0 else 0.0

        return QuotaResponse(
            **quota_info,
            percentage_used=round(percentage_used, 2)
        )
    except QuotaExceededError as e:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Quota exceeded",
                "message": e.message,
                "current_usage": e.current_usage,
                "quota_limit": e.quota_limit,
                "remaining": e.remaining
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check quota: {str(e)}")


@router.get(
    "/stats",
    response_model=UsageStatsResponse,
    summary="Get Usage Statistics",
    description="Get detailed usage statistics including current month and historical data"
)
async def get_usage_stats(
    user_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive usage statistics for the user

    Returns:
        - current_month: Current month's quota information
        - history: Last 6 months of usage data
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="user_id header required")

    try:
        stats = await QuotaChecker.get_usage_stats(user_id, db)
        return UsageStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get usage stats: {str(e)}")


@router.get(
    "/limits",
    summary="Get Quota Limits",
    description="Get quota limits for all user roles"
)
async def get_quota_limits():
    """
    Get quota limits for all roles

    Returns:
        Dictionary mapping role names to their clip limits
    """
    return {
        "quotas": QuotaChecker.ROLE_QUOTAS,
        "descriptions": {
            "free": "10 clips per month - Perfect for trying out SupoClip",
            "pro": "500 clips per month - For serious content creators",
            "admin": "Unlimited clips - Full access to all features"
        },
        "pricing": {
            "free": "$0/month",
            "pro": "$29/month",
            "admin": "Contact sales"
        }
    }


@router.post(
    "/admin/update-role",
    summary="Update User Role (Admin Only)",
    description="Update a user's role - admin endpoint only"
)
async def update_user_role(
    request: UpdateRoleRequest,
    target_user_id: str,
    user_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a user's role (admin only)

    Args:
        target_user_id: ID of user to update
        request: New role information

    Returns:
        Success message with updated role
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="user_id header required")

    # Check if current user is admin
    admin_check = await db.execute(
        text("SELECT role FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    )
    admin_role = admin_check.scalar()

    if admin_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Validate role
    valid_roles = ["free", "pro", "admin"]
    if request.role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )

    try:
        # Update user role
        await db.execute(
            text("UPDATE users SET role = :role, updatedAt = CURRENT_TIMESTAMP WHERE id = :user_id"),
            {"role": request.role, "user_id": target_user_id}
        )
        await db.commit()

        return {
            "success": True,
            "message": f"User role updated to {request.role}",
            "user_id": target_user_id,
            "new_role": request.role,
            "new_quota": QuotaChecker.get_quota_for_role(request.role)
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update role: {str(e)}")


@router.get(
    "/user/{user_id}/info",
    summary="Get User Quota Info (Admin)",
    description="Get quota information for any user - admin endpoint only"
)
async def get_user_quota_info(
    user_id_param: str,
    user_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get quota information for any user (admin only)
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="user_id header required")

    # Check if current user is admin
    admin_check = await db.execute(
        text("SELECT role FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    )
    admin_role = admin_check.scalar()

    if admin_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Get user info
        user_info = await db.execute(
            text("""
                SELECT id, name, email, role, subscription_status, createdAt
                FROM users
                WHERE id = :user_id
            """),
            {"user_id": user_id_param}
        )
        user_row = user_info.fetchone()

        if not user_row:
            raise HTTPException(status_code=404, detail="User not found")

        # Get quota info
        quota_info = await QuotaChecker.check_user_quota(user_id_param, db)

        return {
            "user": {
                "id": user_row[0],
                "name": user_row[1],
                "email": user_row[2],
                "role": user_row[3],
                "subscription_status": user_row[4],
                "created_at": user_row[5].isoformat()
            },
            "quota": quota_info
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user info: {str(e)}")
