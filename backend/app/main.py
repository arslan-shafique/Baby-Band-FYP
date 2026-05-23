"""
Smart Baby Band - FastAPI Backend Entry Point

This is the main file that starts everything. It:
1. Creates the FastAPI application
2. Configures CORS (so Flutter app can call the API)
3. Initializes Firebase connection
4. Registers all route modules (auth, sensors, cry events, etc.)
5. Provides a health check endpoint

TO RUN (from the backend/ directory):
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.firebase_client import initialize_firebase
from app.mqtt_client import start_mqtt_client, stop_mqtt_client

# Global variable to hold the MQTT client
_mqtt_client = None

# Import route modules
from app.routes import (
    auth,
    baby_profile,
    sensor_data,
    cry_events,
    sleep,
    notifications,
    reports,
)


# ── Lifespan (runs on startup and shutdown) ───────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs when the server starts and stops.
    - Startup: Initialize Firebase, load ML models, etc.
    - Shutdown: Clean up resources
    """
    global _mqtt_client
    # ── STARTUP ──
    print("🚀 Starting Smart Baby Band API...")
    initialize_firebase()
    _mqtt_client = start_mqtt_client()
    print("✅ All systems ready!")

    yield  # App runs here

    # ── SHUTDOWN ──
    print("👋 Shutting down Smart Baby Band API...")
    stop_mqtt_client(_mqtt_client)


# ── Create FastAPI App ────────────────────────────────────────
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for the Smart Baby Band IoT wearable — "
                "Cry classification, sleep tracking, and health monitoring.",
    lifespan=lifespan,
)


# ── CORS Middleware ───────────────────────────────────────────
# This allows your Flutter app (running on a different domain/port)
# to make requests to this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Which domains can call the API
    allow_credentials=True,
    allow_methods=["*"],      # Allow all HTTP methods (GET, POST, PUT, DELETE)
    allow_headers=["*"],      # Allow all headers (including Authorization)
)


# ── Register Route Modules ───────────────────────────────────
# Each router handles a group of related endpoints
# The prefix means: auth routes start with /api/auth/*, etc.
app.include_router(auth.router,         prefix="/api/auth",          tags=["Authentication"])
app.include_router(baby_profile.router, prefix="/api/baby",          tags=["Baby Profile"])
app.include_router(sensor_data.router,  prefix="/api/sensor",        tags=["Sensor Data"])
app.include_router(cry_events.router,   prefix="/api/cry",           tags=["Cry Events"])
app.include_router(sleep.router,        prefix="/api/sleep",         tags=["Sleep Tracking"])
app.include_router(notifications.router,prefix="/api/notifications", tags=["Notifications"])
app.include_router(reports.router,      prefix="/api/reports",       tags=["Reports"])


# ── Health Check Endpoint ─────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint — confirms the API is running."""
    return {
        "status": "ok",
        "message": "🍼 Smart Baby Band API is running!",
        "version": settings.APP_VERSION,
    }


# ── Top-level /predict alias ─────────────────────────────────
# The ESP32 firmware POSTs raw PCM bytes to /predict (not /api/cry/predict).
# This top-level route delegates to the same handler so both paths work.
from app.routes.cry_events import predict_cry_audio
app.post("/predict", tags=["Cry Events"])(predict_cry_audio)


@app.get("/api/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Use this to verify the API and Firebase connection are working.
    """
    from app.firebase_client import get_firestore_client

    try:
        # Quick test: try to access Firestore
        db = get_firestore_client()
        # Attempt a simple read to verify connection
        db.collection("_health_check").limit(1).get()
        firebase_status = "connected"
    except Exception as e:
        firebase_status = f"error: {str(e)}"

    return {
        "status": "ok",
        "firebase": firebase_status,
        "version": settings.APP_VERSION,
    }


# ── Run directly (alternative to uvicorn CLI) ────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
