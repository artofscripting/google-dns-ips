"""Simple JSON-only Flask server using google_dns_ips."""

from __future__ import annotations

from flask import Flask, jsonify, request

from google_dns_ips import GoogleIPQuery, get_google_ip_cidrs, get_google_ip_networks

app = Flask(__name__)

# Resolve once at startup for a simple demo server.
resolution = get_google_ip_cidrs()
query = GoogleIPQuery.from_cidrs(resolution.cidrs)


@app.get("/health")
def health() -> tuple[dict, int]:
    return {"ok": True}, 200


@app.get("/metadata")
def metadata() -> tuple[dict, int]:
    return {
        "txt_sources_visited": len(resolution.visited_records),
        "cidr_count": len(resolution.cidrs),
        "first_10_cidrs": list(resolution.cidrs[:10]),
    }, 200


@app.get("/cidrs")
def cidrs() -> tuple[dict, int]:
    return {"cidrs": list(resolution.cidrs)}, 200


@app.get("/networks")
def networks() -> tuple[dict, int]:
    # Uses the get_google_ip_networks helper explicitly.
    networks = get_google_ip_networks()
    return {"networks": [str(net) for net in networks]}, 200


@app.get("/check")
def check() -> tuple[dict, int]:
    value = request.args.get("value", "").strip()
    if not value:
        return {"error": "Missing required query param: value"}, 400

    try:
        return {
            "value": value,
            "contains": query.contains(value),
            "collides": query.collides(value),
        }, 200
    except ValueError as exc:
        return {"error": str(exc), "value": value}, 400


@app.get("/check/range")
def check_range() -> tuple[dict, int]:
    start = request.args.get("start", "").strip()
    end = request.args.get("end", "").strip()
    if not start or not end:
        return {"error": "Missing required query params: start and end"}, 400

    try:
        return {
            "start": start,
            "end": end,
            "contains": query.contains_range(start, end),
            "collides": query.collides_range(start, end),
        }, 200
    except ValueError as exc:
        return {"error": str(exc), "start": start, "end": end}, 400


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Not found"}), 404


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)
