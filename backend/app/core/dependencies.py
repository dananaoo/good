from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db import get_db
from app.models.user import User, UserRole
from app.core.security import get_user_from_token
from app.schemas.user import TokenData

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = get_user_from_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception
    
    result = await db.execute(
        select(User).where(User.id == token_data["user_id"])
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    return current_user


def require_role(allowed_roles: list[UserRole]):
    """Dependency to require specific user roles."""
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker


# Common role dependencies
require_admin = require_role([UserRole.ADMIN])
require_employer = require_role([UserRole.EMPLOYER, UserRole.ADMIN])
require_candidate = require_role([UserRole.CANDIDATE, UserRole.ADMIN])
require_employer_or_candidate = require_role([UserRole.EMPLOYER, UserRole.CANDIDATE, UserRole.ADMIN])
