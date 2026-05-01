import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.db.models import User
from app.db.session import get_db

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate the Bearer token and return the authenticated User.

    Raises HTTP 401 if the token is missing, expired, invalid, or the
    user no longer exists in the database.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = security.decode_token(credentials.credentials)
    except JWTError:
        raise credentials_exc

    # Reject refresh tokens being presented as access tokens
    if payload.get("type") != "access":
        raise credentials_exc

    sub: str | None = payload.get("sub")
    if sub is None:
        raise credentials_exc

    try:
        user_id = uuid.UUID(sub)
    except ValueError:
        raise credentials_exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exc

    return user
