from fastapi import Header, Query, HTTPException, status
from typing import Optional

def _strip_bearer(value: str) -> str:
    v = value.strip()
    if v.lower().startswith("bearer "):
        return v.split(" ", 1)[1].strip()
    return v

def get_bearer_token(
    authorization_header: Optional[str] = Header(None, alias="Authorization"),
    authorization_query: Optional[str] = Query(None, alias="authorization"),
) -> str:
    """
    Accept token from either:
      - Authorization: Bearer <token>   (header)
      - ?authorization=Bearer <token>   (query)  <-- useful in Swagger when no Authorize button
    """
    raw = authorization_header or authorization_query
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization")
    return _strip_bearer(raw)
