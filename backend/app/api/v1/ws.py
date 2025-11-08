from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from typing import Optional

from app.core.config import Settings

router = APIRouter()
settings = Settings()

def _get_user_id_from_token(token: str) -> Optional[str]:
    """
    Minimal JWT verification for WebSockets.
    Matches your existing JWT settings (secret + algorithm).
    Returns the user id (sub) if valid, else None.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False},
        )
        sub = payload.get("sub")
        if not sub:
            return None
        return str(sub)
    except JWTError:
        return None

@router.websocket("/ws/transcribe")
async def ws_transcribe(websocket: WebSocket):
    """
    Placeholder WS endpoint we’ll wire to streaming STT in the next steps.
    Auth: expects ?token=ACCESS_TOKEN in the query string (or Sec-WebSocket-Protocol in later iterations).
    """
    # Accept early so we can read the query params
    await websocket.accept()

    # Pull token from query (?token=...)
    token = websocket.query_params.get("token")
    user_id = _get_user_id_from_token(token) if token else None
    if not user_id:
        # Close with policy violation if unauthenticated
        await websocket.close(code=4403)  # 4403 = forbidden (custom close code)
        return

    try:
        # For now just echo back messages; we’ll replace with streaming STT next.
        while True:
            msg = await websocket.receive_text()
            await websocket.send_text(f"echo: {msg}")
    except WebSocketDisconnect:
        # Client disconnected — normal flow
        return
