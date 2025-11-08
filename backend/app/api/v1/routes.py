from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.auth.routes import router as auth_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.ws import router as ws_router

router = APIRouter()

@router.get("/ping")
def ping():
    return {"message": "pong"}

@router.get("/db-check")
async def db_check(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT now()"))
    now = result.scalar()
    return {"db": "ok", "now": str(now)}

# Sub-routers
router.include_router(auth_router)         # auth_router already has prefix="/auth"
router.include_router(sessions_router)     # sessions_router has prefix="/sessions"
router.include_router(ws_router)           # ws_router has prefix="/ws"
