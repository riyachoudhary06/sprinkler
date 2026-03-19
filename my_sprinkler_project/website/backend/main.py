"""
main.py — FastAPI application entrypoint
Intelligent Pesticide Sprinkling System — Backend Server
"""
import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from db.database import init_db
from services.mqtt_bridge import MQTTBridge
from api.routes_sensors import router as sensors_router
from api.routes_camera import router as camera_router
from api.routes_disease import router as disease_router
from api.routes_motor import router as motor_router
from api.routes_logs import router as logs_router
from api.routes_mode import router as mode_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

mqtt_bridge: MQTTBridge | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global mqtt_bridge
    log.info("Starting up Agri-Watch backend...")
    init_db()
    mqtt_bridge = MQTTBridge(settings)
    threading.Thread(target=mqtt_bridge.start, daemon=True, name="MQTT-Bridge").start()
    log.info("MQTT bridge started.")
    yield
    log.info("Shutting down...")
    if mqtt_bridge:
        mqtt_bridge.stop()


app = FastAPI(
    title="Agri-Watch — Pesticide Sprinkling System API",
    version="1.0.0",
    description="IoT backend for ERT-based field monitoring with Gemini AI disease detection.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── routers ──────────────────────────────────────────────────────────────────
app.include_router(sensors_router, prefix="/sensors",  tags=["Sensors"])
app.include_router(camera_router,  prefix="/camera",   tags=["Camera"])
app.include_router(disease_router, prefix="/disease",  tags=["Disease"])
app.include_router(motor_router,   prefix="/motor",    tags=["Motor"])
app.include_router(logs_router,    prefix="/logs",     tags=["Logs"])
app.include_router(mode_router,    prefix="/mode",     tags=["Mode"])


@app.get("/health", tags=["System"])
def health():
    return {
        "status": "ok",
        "mqtt_connected": mqtt_bridge.is_connected() if mqtt_bridge else False,
        "version": "1.0.0",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    log.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
