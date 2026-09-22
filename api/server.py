# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                  ║
# ║   ░█▀▀░█▀█░█▀▄░█▀▀░█░█   ░█▀▄░█▀▀░█░█░█▀▀                     ║
# ║   ░█░░░█░█░█░█░█▀▀░▄▀▄   ░█░█░█▀▀░▀▄▀░▀▀█                     ║
# ║   ░▀▀▀░▀▀▀░▀▀░░▀▀▀░▀░▀   ░▀▀░░▀▀▀░░▀░░▀▀▀                     ║
# ║                                                                  ║
# ║            © 2026 Vinay Kumar (!Alone💔) — All Rights Reserved              ║
# ║                                                                  ║
# ║   discord  ──  https://discord.com/users/731390792567881739                      ║
# ║   youtube  ──  https://discord.com/users/731390792567881739                   ║
# ║   github   ──  https://github.com/kumar_vinay                        ║
# ║                                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import time
import json
import logging
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from utils.config import *


from api.routes import bot, guilds, admin
from api.dependencies import verify_api_key, limiter
from api.db_manager import db_manager

# Configure logging
logger = logging.getLogger("api_request_logs")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup: Nothing special needed for now
    yield
    # Shutdown: Close all shared database connections
    await db_manager.close_all()

def create_app() -> FastAPI:
    """
    Initializes the FastAPI application for the CodeX Bot Dashboard.
    The bot instance will be attached to app.state.bot in CodeX.py at runtime.
    """
    app = FastAPI(
        title=f"{BRAND_NAME} Bot API",
        description=f"REST API and Healthcheck Server for {BRAND_NAME} Discord Bot",
        version="1.0",
        lifespan=lifespan
    )

    # Structured Logging Middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        log_data = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(process_time * 1000, 2),
            "client_ip": request.client.host if request.client else "unknown"
        }
        
        logger.info(json.dumps(log_data))
        return response

    # Attach limiter and handler
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # Build allowed origins from env + hardcoded fallbacks
    _extra_origins = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "").split(",")
        if o.strip()
    ]
    _allowed_origins = list(dict.fromkeys([
        "http://localhost:3000",
        "https://localhost:3000",
        *_extra_origins,
    ]))

    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Routers with API key security
    app.include_router(bot.router, prefix="/api/v1/bot", tags=["Bot"], dependencies=[Depends(verify_api_key)])
    app.include_router(guilds.router, prefix="/api/v1/guilds", tags=["Guilds"], dependencies=[Depends(verify_api_key)])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"], dependencies=[Depends(verify_api_key)])

    @app.get("/", summary="API Root", description="Returns basic bot information and online status.")
    async def root():
        return {
            "status": "online",
            "bot_name": BRAND_NAME,
            "api_version": "1.0",
            "service": "24/7 Discord Bot on Render"
        }

    @app.get("/health", summary="Health Check", description="Health check for Render container orchestration and uptime monitoring.")
    async def health():
        return {"status": "ok", "bot": BRAND_NAME}

    return app
