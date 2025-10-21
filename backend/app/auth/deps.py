from fastapi import Depends, HTTPException, status, Header, Query
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import Settings
from app.db.session import get_db
from app.models.user import User

settings = Settings()

def _strip_bearer(value: str) -> str:
    """Remove 'Bearer ' prefix if present"""
    v = value.strip()
    if v.lower().startswith("bearer "):
        return v.split(" ", 1)[1].strip()
    return v

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization_header: str | None = Header(None, alias="Authorization"),
    authorization_query: str | None = Query(None, alias="authorization"),
):
    """
    Extract token from either:
      - Header: Authorization: Bearer <token>
      - Query:  ?authorization=Bearer <token> (for Swagger)
    """
    raw = authorization_header or authorization_query
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = _strip_bearer(raw)

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
