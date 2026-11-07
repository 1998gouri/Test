# Urja Meter Ops protocol notes

## Evidence

Read-only browser inspection on 7 November 2026. Five successful GET requests were captured in the HAR; transformer response bodies and meter hierarchy/energy samples were copied from Chrome DevTools → Network → Fetch/XHR → Response. No portal writes were performed. A session cookie value was accidentally pasted during troubleshooting; the user logged out immediately. The value is not reproduced and must never be committed.

## Observed routes

| Purpose | Method and path | Evidence |
|---|---|---|
| Meter search | `GET /portal/meters/search?q=&page=1` | JSON `data`, `total`, `page`, `pageSize` |
| Meter detail | `GET /meters/{meter_id}/__data.json?x-sveltekit-invalidated=001` | SvelteKit page-data payload |
| Meter coordinates | `GET /portal/meters/{meter_id}/geo` | `data.latitude`, `data.longitude` |
| Energy | `GET /portal/meters/{meter_id}/energy` | `data` array of readings |
| Transformers | `GET /portal/dts?page={page}` | JSON `data`, `total`, `page`, `pageSize` |

All captured requests were GET and returned HTTP 200.

## Data observed

Meter search returned `meterId`, `serialNo`, `make`, `phaseType`, `installStatus`, and `dtCode`; the sample reported 40 records and page size 20. The hierarchy observed on meter details was `zone → circle → division → subdivision → substation → feeder → dt`.

Sample meters: `J100000` was HPL, single phase, Decommissioned, Whole Current, in Jaipur Zone 1 / Circle 1 / Division 1 / Subdivision 1 / Substation 1 / Feeder 1 / Malviya Nagar DT 1. `J100001` was L&T, single phase, Installed, CT Operated, in the corresponding Zone 2 hierarchy at Mansarovar DT 2. Sample J100000 coordinates: latitude 26.938961002479868, longitude 75.83095696146852.

Transformer pages 1 and 2 each returned 20 records (40 total), with `code`, `name`, `feederCode`, `capacityKva`. Feeder codes are reused; for example DT-029 uses F-001, so a transformer must not be assumed to have a unique feeder.

Energy readings contain `timestamp`, `kwh`, `kvah`, and `voltR`, represented as strings. The sample had 30-minute spacing over 23–25 June 2026. This does not prove universal cadence, units, or timezone semantics.

## Authentication

Requests used an authenticated browser session. Cookie name `__Secure-better-auth.session_token` was observed. The exact login/renewal exchange was not reverse-engineered. Configure a fresh browser session cookie locally in `PORTAL_COOKIE`; do not commit `.env`, HAR files containing secrets, or session tokens. The service does not automate login.

## Quirks and unknowns

- Meter detail uses an internal SvelteKit `__data.json` route and compact serialized data, not a stable documented API.
- Coordinates are fetched separately.
- Search and transformers use page-based pagination.
- Energy values and timestamps are preserved without coercion.
- Unknowns: session renewal, extra search filters, missing coordinates/hierarchy cases, energy date filters/timezone/units, rate limits, and other SvelteKit payload variants.
