"""Print safe request metadata from a HAR; never print headers or query strings."""
import json
import sys
from urllib.parse import urlsplit


def main(path: str):
    with open(path, encoding="utf-8") as handle:
        har = json.load(handle)
    for entry in har.get("log", {}).get("entries", []):
        request = entry.get("request", {})
        parsed = urlsplit(request.get("url", ""))
        if entry.get("_resourceType") in {"fetch", "xhr"}:
            print(f"{request.get('method', '?')} {parsed.netloc}{parsed.path} -> {entry.get('response', {}).get('status', '?')}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/inspect_portal.py path/to/export.har")
    main(sys.argv[1])
