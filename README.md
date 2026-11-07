# Urja Meter API

A small, read-only FastAPI service that turns the Urja Meter Ops portal's observed browser endpoints into a versioned API for meter search, meter details and hierarchy, energy readings, and distribution transformers.

## What it does

- Searches meters using the portal's `q` and `page` parameters.
- Exposes meter details through the portal's SvelteKit page-data route and includes separately fetched coordinates.
- Retrieves energy readings without changing source values or timestamps.
- Lists distribution transformers with page-based pagination.
- Keeps the upstream session cookie outside source control.

See [`PROTOCOL.md`](PROTOCOL.md) for the observed portal behavior and [`openapi.json`](openapi.json) for the API contract. Interactive docs are served at `/docs`.

## Repository layout

```text
app/config.py       Environment-based configuration
app/main.py         FastAPI routes and error mapping
app/portal.py       Read-only upstream adapter and SvelteKit payload handling
tests/              Offline tests with mocked upstream responses
PROTOCOL.md         Observed portal routes, response shapes, auth and quirks
openapi.json        OpenAPI 3.1 contract
.env.example        Safe configuration template
```

## Requirements and setup

- Python 3.11+
- Network access to `https://urja-ops.flockenergy.tech`
- A valid session from a normal portal login for live requests

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e '.[dev]'
cp .env.example .env  # Windows PowerShell: Copy-Item .env.example .env
```

Sign in to the portal normally. In Chrome DevTools → Application → Cookies → portal origin, locate `__Secure-better-auth.session_token` and copy its `name=value` pair into `PORTAL_COOKIE` in your local `.env`. Never paste the value into chat, source code, screenshots, or GitHub. If it expires, sign in again and update the local value. The service does not automate login.

Start the API:

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`, `http://127.0.0.1:8000/openapi.json`, or `http://127.0.0.1:8000/health`.

## API examples

```bash
curl 'http://127.0.0.1:8000/api/v1/meters?q=J100000&page=1'
curl 'http://127.0.0.1:8000/api/v1/meters/J100000'
curl 'http://127.0.0.1:8000/api/v1/meters/J100000/energy'
curl 'http://127.0.0.1:8000/api/v1/transformers?page=2'
```

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `PORTAL_BASE_URL` | Portal origin | `https://urja-ops.flockenergy.tech` |
| `PORTAL_TIMEOUT_SECONDS` | Upstream timeout | `20` |
| `PORTAL_USER_AGENT` | Client user-agent | `UrjaMeterAPI/1.0` |
| `PORTAL_COOKIE` | Authenticated browser cookie (`name=value`) | empty |

`.env` is ignored by Git. Do not commit a real session cookie, password, or HAR export.

## Tests

Run `pytest -q`. Tests mock upstream HTTP responses and cover meter search parameters, energy pass-through, transformer pagination, a basic SvelteKit data wrapper, health output, and sanitized authentication errors. They do not require a live portal session.

## Assumptions, decisions and trade-offs

- This is a thin facade, not a second system of record; it fetches from the portal on demand and does not persist data.
- Page-based pagination is retained because it matches the portal. No offset/limit translation is introduced.
- Meter details use an internal SvelteKit `__data.json` route. This is more brittle than a supported API; the decoder is isolated so it can be adapted if the serialization changes.
- Coordinates are fetched separately from meter details.
- Energy values and timestamps remain strings/unchanged because units, precision and timezone semantics were not established.
- Authentication uses a locally configured browser session cookie. Session renewal is manual; production should use an approved service identity or supported auth flow.
- Only GET requests are issued. No portal mutation endpoint is implemented.

## Intentionally not included

Automated login, credential storage, database, long-lived cache, background synchronization, bulk export, offset pagination, arbitrary energy date filters, and a web dashboard. These were outside the core read-only API scope or would require additional evidence.

## Reflection

**Assumptions:** The observed browser GET routes are the read path for this exercise. The facade mirrors page pagination and preserves energy wire values. A valid browser session cookie authorizes requests while it remains active.

**Most difficult part:** Meter detail data was delivered through SvelteKit page data rather than a conventional JSON object. Inspecting the browser response and isolating payload handling helped make progress without hard-coding sample meter records.

**With another day:** Confirm the exact detail serialization for additional meters, investigate supported session renewal, establish energy units/timezone, and add controlled live integration tests and cache-freshness behavior.

**Mistake:** The initial implementation work started with assumptions about route shapes before the browser inspection was complete. The observed routes and response examples were then used to revise the adapter and protocol notes.

**Self-criticism:** The SvelteKit route is an internal implementation detail and may change. The payload decoder is intentionally conservative and should be verified against additional real payload variants. Live portal integration has not been re-run after the session was logged out; the automated tests are offline mocks.
