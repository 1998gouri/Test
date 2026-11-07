import httpx
import pytest
from app.portal import PortalClient, PortalError, decode_sveltekit_payload

BASE = "https://urja-ops.flockenergy.tech"


@pytest.mark.asyncio
async def test_meter_search_uses_q_and_page():
    def handler(request):
        assert request.url.path == "/portal/meters/search"
        assert request.url.params["q"] == "J100000"
        assert request.url.params["page"] == "1"
        return httpx.Response(200, json={"data": [{"meterId": "J100000"}], "total": 1})
    async with httpx.AsyncClient(base_url=BASE, transport=httpx.MockTransport(handler)) as http:
        result = await PortalClient(http).meters("J100000", 1)
    assert result["data"][0]["meterId"] == "J100000"


@pytest.mark.asyncio
async def test_energy_values_are_preserved():
    body = {"data": [{"timestamp": "23/06/2026 23:30", "kwh": "48438.74", "kvah": "52313.84", "voltR": "226"}]}
    async def handler(request):
        return httpx.Response(200, json=body)
    async with httpx.AsyncClient(base_url=BASE, transport=httpx.MockTransport(handler)) as http:
        assert await PortalClient(http).energy("J100000") == body


@pytest.mark.asyncio
async def test_transformer_page_is_forwarded():
    def handler(request):
        assert request.url.path == "/portal/dts"
        assert request.url.params["page"] == "2"
        return httpx.Response(200, json={"data": [{"code": "DT-001"}], "page": 2})
    async with httpx.AsyncClient(base_url=BASE, transport=httpx.MockTransport(handler)) as http:
        assert (await PortalClient(http).transformers(2))["page"] == 2


def test_sveltekit_data_wrapper():
    assert decode_sveltekit_payload({"data": {"meterId": "J100000"}}) == {"meterId": "J100000"}


@pytest.mark.asyncio
async def test_auth_error_does_not_leak_response_body():
    async def handler(request):
        return httpx.Response(401, json={"detail": "private"})
    async with httpx.AsyncClient(base_url=BASE, transport=httpx.MockTransport(handler)) as http:
        with pytest.raises(PortalError, match="authentication"):
            await PortalClient(http).meters()
