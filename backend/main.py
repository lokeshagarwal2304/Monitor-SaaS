from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from backend.database import init_db
from backend.routers import auth, websites, pagespeed, notifications, admin # ADDED NEW ROUTERS
from backend.services.scheduler_service import start_scheduler

app = FastAPI(
    title="MoniFy-Ping",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# INCLUDE NEW ROUTERS
app.include_router(auth.router)
app.include_router(websites.router)
app.include_router(pagespeed.router)
app.include_router(notifications.router)
app.include_router(admin.router) # ADMIN ROUTER

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")

@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print("🚀 Starting MoniFy-Ping...")
    init_db()
    start_scheduler()
    print("✅ Scheduler & DB Ready")
    print("=" * 60)

@app.get("/", tags=["Root"])
def root():
    return {
        "status": "online", 
        "service": "MoniFy-Ping", 
        "version": "1.0"
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "MoniFy-Ping",
        "version": "1.0.0"
    }