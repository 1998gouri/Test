from typing import Any
from urllib.parse import quote
import httpx
from app.config import settings


class PortalError(RuntimeError):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class PortalClient:
    def __init__(self, client: httpx.AsyncClient | None = None):
        headers = {"User-Agent": settings.portal_user_agent, "Accept": "application/json"}
        if settings.portal_cookie:
            headers["Cookie"] = settings.portal_cookie
        self._client = client or httpx.AsyncClient(base_url=settings.portal_base_url.rstrip("/"), headers=headers, timeout=settings.portal_timeout_seconds, follow_redirects=True)
        self._owns_client = client is None

    async def close(self):
        if self._owns_client:
            await self._client.aclose()

    async def get_json(self, path: str, params: dict[str, Any] | None = None):
        try:
            response = await self._client.get(path, params=params)
        except httpx.TimeoutException as exc:
            raise PortalError("The portal request timed out.", 504) from exc
        except httpx.HTTPError as exc:
            raise PortalError("The portal could not be reached.", 502) from exc
        if response.status_code in (401, 403):
            raise PortalError("Portal authentication is missing or expired. Refresh PORTAL_COOKIE locally.")
        if response.status_code == 404:
            raise PortalError("The requested portal resource was not found.", 404)
        if response.status_code >= 400:
            raise PortalError(f"The portal returned HTTP {response.status_code}.")
        try:
            return response.json()
        except ValueError as exc:
            raise PortalError("The portal returned a non-JSON response.") from exc

    async def meters(self, q: str = "", page: int = 1):
        return await self.get_json("/portal/meters/search", {"q": q, "page": page})

    async def meter_detail(self, meter_id: str):
        path = f"/meters/{quote(meter_id, safe='')}/__data.json"
        payload = await self.get_json(path, {"x-sveltekit-invalidated": "001"})
        detail = decode_sveltekit_payload(payload)
        geo = await self.get_json(f"/portal/meters/{quote(meter_id, safe='')}/geo")
        coords = geo.get("data", geo) if isinstance(geo, dict) else {}
        if isinstance(coords, dict):
            detail["coordinates"] = {"latitude": coords.get("latitude"), "longitude": coords.get("longitude")}
        return detail

    async def energy(self, meter_id: str):
        return await self.get_json(f"/portal/meters/{quote(meter_id, safe='')}/energy")

    async def transformers(self, page: int = 1):
        return await self.get_json("/portal/dts", {"page": page})


def decode_sveltekit_payload(payload: Any) -> dict[str, Any]:
    # SvelteKit's internal serialization can change; retain unfamiliar shapes.
    if isinstance(payload, dict):
        nodes = payload.get("nodes")
        if isinstance(nodes, list):
            for node in nodes:
                if isinstance(node, dict) and isinstance(node.get("data"), list):
                    data = node["data"]
                    if len(data) > 1 and isinstance(data[1], dict):
                        return data[1]
        if isinstance(payload.get("data"), dict):
            return payload["data"]
        return payload
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                return item
    return {"raw": payload}
