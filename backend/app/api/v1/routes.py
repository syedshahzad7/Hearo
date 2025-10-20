from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.auth.routes import router as auth_router

router = APIRouter()

@router.get("/ping")
def ping():
    return {"message": "pong"}

@router.get("/db-check")
async def db_check(db: AsyncSession = Depends(get_db)):
    # simple roundtrip query
    result = await db.execute(text("SELECT now()"))
    now = result.scalar()
    return {"db": "ok", "now": str(now)}


router.include_router(auth_router)