from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from app.config import settings
from app.portal import PortalClient, PortalError


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.portal = PortalClient()
    yield
    await app.state.portal.close()


app = FastAPI(title="Urja Meter API", version="1.0.0", description="Read-only facade over Urja Meter Ops.", lifespan=lifespan)


@app.exception_handler(PortalError)
async def portal_error_handler(request: Request, exc: PortalError):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


def portal(request: Request):
    return request.app.state.portal


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "upstream_configured": bool(settings.portal_cookie)}


@app.get("/api/v1/meters", tags=["meters"])
async def list_meters(request: Request, q: str = Query(default=""), page: int = Query(default=1, ge=1)):
    return await portal(request).meters(q=q, page=page)


@app.get("/api/v1/meters/{meter_id}", tags=["meters"])
async def get_meter(meter_id: str, request: Request):
    return await portal(request).meter_detail(meter_id)


@app.get("/api/v1/meters/{meter_id}/energy", tags=["energy"])
async def get_energy(meter_id: str, request: Request):
    return await portal(request).energy(meter_id)


@app.get("/api/v1/transformers", tags=["network"])
async def list_transformers(request: Request, page: int = Query(default=1, ge=1)):
    return await portal(request).transformers(page=page)
