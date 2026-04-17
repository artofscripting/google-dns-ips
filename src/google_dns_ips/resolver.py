"""Resolve Google-published IP ranges from DNS TXT records.

Google publishes many network ranges in SPF-style TXT records such as:
- _netblocks.google.com
- _cloud-netblocks.googleusercontent.com

This module recursively follows include: directives and extracts ip4:/ip6: CIDRs.
"""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import IPv4Network, IPv6Network, ip_network
from typing import Iterable, Set

import dns.resolver

DEFAULT_TXT_SOURCES = (
    "_netblocks.google.com",
    "_netblocks2.google.com",
    "_netblocks3.google.com",
    "_netblocks4.google.com",
    "_spf.google.com",
    "_cloud-netblocks.googleusercontent.com",
    "_cloud-netblocks2.googleusercontent.com",
    "_cloud-netblocks3.googleusercontent.com",
)

DEFAULT_HOST_SOURCES = (
    "dns.google",
)


@dataclass(frozen=True)
class ResolutionResult:
    """Holds parsed CIDRs from DNS TXT sources."""

    cidrs: tuple[str, ...]
    visited_records: tuple[str, ...]


def _fetch_host_addresses(name: str, resolver: dns.resolver.Resolver) -> list[str]:
    """Return A/AAAA address strings for a DNS hostname."""
    addresses: list[str] = []
    for record_type in ("A", "AAAA"):
        try:
            answers = resolver.resolve(name, record_type)
        except (
            dns.resolver.NXDOMAIN,
            dns.resolver.NoAnswer,
            dns.resolver.NoNameservers,
            dns.resolver.LifetimeTimeout,
        ):
            continue

        for record in answers:
            addresses.append(record.address)
    return addresses


def _fetch_txt_strings(name: str, resolver: dns.resolver.Resolver) -> list[str]:
    """Return all TXT strings for a DNS name as decoded text lines."""
    try:
        answers = resolver.resolve(name, "TXT")
    except (
        dns.resolver.NXDOMAIN,
        dns.resolver.NoAnswer,
        dns.resolver.NoNameservers,
        dns.resolver.LifetimeTimeout,
    ):
        return []

    values: list[str] = []
    for record in answers:
        joined = "".join(part.decode("utf-8") for part in record.strings)
        values.append(joined)
    return values


def _collect_cidrs_from_spf(
    name: str,
    resolver: dns.resolver.Resolver,
    cidrs: Set[str],
    visited: Set[str],
    max_depth: int,
    depth: int,
) -> None:
    if depth > max_depth:
        return
    if name in visited:
        return

    visited.add(name)

    for txt in _fetch_txt_strings(name, resolver):
        for token in txt.split():
            if token.startswith("ip4:") or token.startswith("ip6:"):
                cidr = token.split(":", 1)[1]
                try:
                    normalized = str(ip_network(cidr, strict=False))
                except ValueError:
                    continue
                cidrs.add(normalized)
            elif token.startswith("include:"):
                included_name = token.split(":", 1)[1]
                _collect_cidrs_from_spf(
                    included_name,
                    resolver,
                    cidrs,
                    visited,
                    max_depth=max_depth,
                    depth=depth + 1,
                )


def get_google_ip_cidrs(
    sources: Iterable[str] = DEFAULT_TXT_SOURCES,
    host_sources: Iterable[str] = DEFAULT_HOST_SOURCES,
    *,
    timeout: float = 5.0,
    lifetime: float = 5.0,
    max_depth: int = 15,
) -> ResolutionResult:
    """Resolve and return sorted Google CIDR strings from DNS TXT sources.

    Args:
        sources: DNS TXT records to inspect.
        host_sources: DNS hostnames to resolve via A/AAAA and include as /32 or /128.
        timeout: Per-request timeout for the DNS resolver.
        lifetime: Total timeout for each resolver query.
        max_depth: Maximum include: recursion depth.

    Returns:
        ResolutionResult containing unique, sorted CIDRs and visited record names.
    """
    resolver = dns.resolver.Resolver(configure=True)
    resolver.timeout = timeout
    resolver.lifetime = lifetime

    cidrs: Set[str] = set()
    visited: Set[str] = set()

    for source in sources:
        _collect_cidrs_from_spf(
            source,
            resolver,
            cidrs,
            visited,
            max_depth=max_depth,
            depth=0,
        )

    for host in host_sources:
        visited.add(host)
        for address in _fetch_host_addresses(host, resolver):
            cidrs.add(str(ip_network(address, strict=False)))

    return ResolutionResult(
        cidrs=tuple(sorted(cidrs)),
        visited_records=tuple(sorted(visited)),
    )


def get_google_ip_networks(
    sources: Iterable[str] = DEFAULT_TXT_SOURCES,
    **kwargs,
) -> tuple[IPv4Network | IPv6Network, ...]:
    """Resolve Google ranges and return ipaddress network objects."""
    result = get_google_ip_cidrs(sources=sources, **kwargs)
    networks = tuple(ip_network(cidr) for cidr in result.cidrs)
    return networks
