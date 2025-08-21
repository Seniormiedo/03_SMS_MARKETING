"""
Common Dependencies
"""

from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user

async def get_current_active_user(
    current_user: str = Depends(get_current_user)
) -> str:
    """Get current active user (placeholder for user status check)"""
    # In a real application, you would check if user is active in database
    return current_user

async def get_admin_user(
    current_user: str = Depends(get_current_user)
) -> str:
    """Require admin privileges"""
    # In a real application, check user role in database
    if current_user != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user