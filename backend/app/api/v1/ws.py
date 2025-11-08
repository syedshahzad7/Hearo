from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import jwt, JWTError
import os

from app.core.config import Settings

router = APIRouter()
settings = Settings()


def _get_user_id_from_token(token: str) -> Optional[str]:
    """
    Minimal JWT verification for WebSockets.
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
    Connect with:
      ws://127.0.0.1:8000/api/v1/ws/transcribe?session_id=...&token=ACCESS_TOKEN

    The browser should send MediaRecorder binary chunks (webm/opus).
    We append them to uploads/<user_id>/<session_id>/live_capture.webm.
    """
    # Accept first so we can read query params and start receiving frames
    await websocket.accept()

    token = websocket.query_params.get("token")
    session_id = websocket.query_params.get("session_id")
    user_id = _get_user_id_from_token(token) if token else None

    if not user_id or not session_id:
        # Forbidden / unauthenticated
        await websocket.close(code=4403)
        return

    # Prepare output path
    user_dir = os.path.join(settings.UPLOAD_DIR, user_id, session_id)
    os.makedirs(user_dir, exist_ok=True)
    out_path = os.path.join(user_dir, "live_capture.webm")

    # Open once and append as frames arrive
    f = open(out_path, "wb")

    try:
        while True:
            message = await websocket.receive()

            # Browser sends binary audio chunks
            if "bytes" in message and message["bytes"] is not None:
                f.write(message["bytes"])
                f.flush()
                continue

            # Optional: handle small text control messages if you want
            if "text" in message and message["text"] is not None:
                # e.g., await websocket.send_text(f"ack:{message['text']}")
                continue

            # If client closed
            if message.get("type") == "websocket.disconnect":
                break

    except WebSocketDisconnect:
        # Normal client disconnect
        pass
    except Exception:
        # Swallow unexpected errors to ensure file is closed
        pass
    finally:
        try:
            f.close()
        except Exception:
            pass
        # Socket will be closed by FastAPI when we return
