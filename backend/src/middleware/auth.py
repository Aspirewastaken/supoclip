"""
Authentication Middleware
Provides authentication dependency for FastAPI routes
"""
from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
import logging

from ..database import get_db

logger = logging.getLogger(__name__)


async def get_current_user(
    user_id: Optional[str] = Header(None, alias="user_id"),
    db: AsyncSession = Depends(get_db)
) -> str:
    """
    Authentication dependency that validates user_id from headers.

    This is a basic header-based authentication. In production, this should be
    replaced with proper JWT token validation or session-based authentication.

    Args:
        user_id: User ID from request header
        db: Database session

    Returns:
        Validated user_id string

    Raises:
        HTTPException: 401 if user_id missing or user not found
    """
    if not user_id:
        logger.warning("Authentication failed: Missing user_id header")
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide user_id header.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Validate user_id format
    if not user_id or len(user_id.strip()) == 0:
        logger.warning(f"Authentication failed: Invalid user_id format: {user_id}")
        raise HTTPException(
            status_code=401,
            detail="Invalid user_id format"
        )

    # Check if user exists in database
    try:
        user_exists = await db.execute(
            text("SELECT 1 FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        if not user_exists.fetchone():
            logger.warning(f"Authentication failed: User not found: {user_id}")
            raise HTTPException(
                status_code=401,
                detail="User not found. Invalid authentication credentials."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error during authentication: {e}")
        raise HTTPException(
            status_code=500,
            detail="Authentication system error"
        )

    logger.debug(f"User authenticated successfully: {user_id}")
    return user_id


async def get_current_user_optional(
    user_id: Optional[str] = Header(None, alias="user_id"),
    db: AsyncSession = Depends(get_db)
) -> Optional[str]:
    """
    Optional authentication dependency.
    Returns user_id if provided and valid, None otherwise.
    Does not raise exceptions.

    Args:
        user_id: User ID from request header
        db: Database session

    Returns:
        Validated user_id string or None
    """
    if not user_id:
        return None

    try:
        user_exists = await db.execute(
            text("SELECT 1 FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        if user_exists.fetchone():
            return user_id
    except Exception as e:
        logger.error(f"Error validating optional user: {e}")

    return None


async def verify_resource_ownership(
    resource_user_id: str,
    current_user_id: str
) -> bool:
    """
    Verify that the current user owns the resource.

    Args:
        resource_user_id: The user_id associated with the resource
        current_user_id: The authenticated user's ID

    Returns:
        True if user owns the resource

    Raises:
        HTTPException: 403 if user doesn't own the resource
    """
    if resource_user_id != current_user_id:
        logger.warning(
            f"Authorization failed: User {current_user_id} attempted to access "
            f"resource owned by {resource_user_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this resource"
        )
    return True
