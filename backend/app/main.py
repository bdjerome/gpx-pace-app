from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import auth, gpx, analyze

app = FastAPI(title="GPX Pace Planner API")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(gpx.router, prefix="/routes", tags=["gpx"])
app.include_router(analyze.router, prefix="/routes", tags=["analyze"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the GPX Pace App API!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
