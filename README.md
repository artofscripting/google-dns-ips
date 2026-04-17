# google-dns-ips

Python library that resolves Google-published IP ranges from DNS TXT records.

It parses SPF-style TXT records (including nested `include:` records) and extracts
all `ip4:` and `ip6:` CIDRs.

## Why DNS TXT?

Google publishes network ranges in DNS TXT records such as:

- `_netblocks.google.com`
- `_netblocks2.google.com`
- `_netblocks3.google.com`
- `_spf.google.com`
- `_cloud-netblocks.googleusercontent.com`

This package also resolves host records (A/AAAA), by default `dns.google`,
and includes those addresses as `/32` or `/128` networks.

This library recursively walks those records and returns normalized ranges.

## Install

From the project root:

```bash
pip install -e .
```

## Library Usage

```python
from google_dns_ips import GoogleIPQuery, get_google_ip_cidrs

result = get_google_ip_cidrs()
query = GoogleIPQuery.from_cidrs(result.cidrs)

print(query.contains("8.8.8.8"))
print(query.collides("8.8.8.0/24"))
print(query.contains("8.8.0.0-8.8.255.255"))
```

`result` is a `ResolutionResult` with:

- `cidrs`: sorted tuple of unique CIDR strings
- `visited_records`: sorted tuple of DNS names visited during recursion

`GoogleIPQuery` supports:

- `contains(value)`: full containment for IP, CIDR, or range string (`start-end`)
- `collides(value)`: any overlap for IP, CIDR, or range string (`start-end`)
- Specific methods: `contains_ip`, `contains_cidr`, `contains_range`, `collides_ip`, `collides_cidr`, `collides_range`

## Example Script

Run:

```bash
python examples/print_google_ips.py
```

## Flask JSON Server Example

Run:

```bash
python examples/flask_server.py
```

All endpoints return JSON.

Examples:

```bash
curl "http://127.0.0.1:5001/health"
curl "http://127.0.0.1:5001/metadata"
curl "http://127.0.0.1:5001/cidrs"
curl "http://127.0.0.1:5001/networks"
curl "http://127.0.0.1:5001/check?value=8.8.8.8"
curl "http://127.0.0.1:5001/check?value=8.8.8.0/24"
curl "http://127.0.0.1:5001/check?value=8.8.0.0-8.8.255.255"
curl "http://127.0.0.1:5001/check/range?start=8.8.8.0&end=8.8.8.255"
```

### Full Endpoint List (127.0.0.1)

Base URL:

```text
http://127.0.0.1:5001
```

1. `GET /health`

```bash
curl "http://127.0.0.1:5001/health"
```

2. `GET /metadata`

```bash
curl "http://127.0.0.1:5001/metadata"
```

3. `GET /cidrs`

```bash
curl "http://127.0.0.1:5001/cidrs"
```

4. `GET /networks`

```bash
curl "http://127.0.0.1:5001/networks"
```

5. `GET /check` with required query param `value`

IP examples:

```bash
curl "http://127.0.0.1:5001/check?value=8.8.8.8"
curl "http://127.0.0.1:5001/check?value=2001:4860:4860::8888"
```

CIDR examples:

```bash
curl "http://127.0.0.1:5001/check?value=8.8.8.0/24"
curl "http://127.0.0.1:5001/check?value=2001:4860:4860::/48"
```

Range examples (`start-end`):

```bash
curl "http://127.0.0.1:5001/check?value=8.8.0.0-8.8.255.255"
curl "http://127.0.0.1:5001/check?value=2001:4860:4860::8888-2001:4860:4860::8899"
```

Error examples:

```bash
curl "http://127.0.0.1:5001/check"
curl "http://127.0.0.1:5001/check?value=not-an-ip"
curl "http://127.0.0.1:5001/check?value=1.1.1.1-2001:4860:4860::8888"
```

6. `GET /check/range` with required query params `start` and `end`

IPv4 range examples:

```bash
curl "http://127.0.0.1:5001/check/range?start=8.8.8.0&end=8.8.8.255"
curl "http://127.0.0.1:5001/check/range?start=8.8.8.255&end=8.8.8.0"
```

IPv6 range example:

```bash
curl "http://127.0.0.1:5001/check/range?start=2001:4860:4860::8888&end=2001:4860:4860::8899"
```

Error examples:

```bash
curl "http://127.0.0.1:5001/check/range"
curl "http://127.0.0.1:5001/check/range?start=8.8.8.8"
curl "http://127.0.0.1:5001/check/range?start=8.8.8.8&end=2001:4860:4860::8888"
curl "http://127.0.0.1:5001/check/range?start=bad&end=input"
```

7. `GET` unknown route (JSON 404)

```bash
curl "http://127.0.0.1:5001/not-found"
```



