
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core.config import Settings
from app.api.v1.routes import router as api_router

settings = Settings()

app = FastAPI(title="Hearo API", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(api_router, prefix=settings.API_V1_STR)
