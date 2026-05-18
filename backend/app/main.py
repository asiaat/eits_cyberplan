from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api.v2 import api_router as api_router_v2

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.init_db import init_db
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="E-ITS CyberPlan",
    version="1.0.0",
    docs_url=None,
    redoc_url="/redoc",
    openapi_url="/api/v2/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router_v2, prefix="/api/v2")


@app.get("/docs", include_in_schema=False)
async def custom_docs_url():
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(
        openapi_url=str(app.root_path) + "/api/v2/openapi.json",
        title="E-ITS CyberPlan",
        oauth2_redirect_url=app.root_path + "/docs/oauth2-redirect",
        swagger_ui_parameters={"persistAuthorization": True},
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME}


def custom_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    openapi_schema.setdefault("components", {})["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token",
        }
    }
    for path, methods in openapi_schema["paths"].items():
        for method, details in methods.items():
            if method.upper() not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                continue
            if path.startswith("/api/v2/auth/login") or path.startswith("/api/v2/auth/register"):
                continue
            details.setdefault("security", [{"Bearer": []}])
    app.openapi_schema = openapi_schema
    return openapi_schema


app.openapi = custom_openapi  # type: ignore