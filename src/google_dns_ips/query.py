"""Membership and overlap checks against Google IP ranges."""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import (
    IPv4Address,
    IPv4Network,
    IPv6Address,
    IPv6Network,
    ip_address,
    ip_network,
    summarize_address_range,
)
from typing import Iterable

from .resolver import get_google_ip_cidrs

IPAddress = IPv4Address | IPv6Address
IPNetwork = IPv4Network | IPv6Network


@dataclass(frozen=True)
class GoogleIPQuery:
    """Contains Google CIDRs and query helpers for contains/overlap checks."""

    cidrs: tuple[str, ...]
    networks: tuple[IPNetwork, ...]

    @classmethod
    def from_cidrs(cls, cidrs: Iterable[str]) -> "GoogleIPQuery":
        normalized_networks = tuple(sorted((ip_network(c, strict=False) for c in cidrs), key=str))
        return cls(
            cidrs=tuple(str(net) for net in normalized_networks),
            networks=normalized_networks,
        )

    @classmethod
    def from_dns(cls, **kwargs) -> "GoogleIPQuery":
        """Build a query index by resolving Google's DNS-published CIDRs."""
        result = get_google_ip_cidrs(**kwargs)
        return cls.from_cidrs(result.cidrs)

    def contains_ip(self, ip_value: str | IPAddress) -> bool:
        """Return True if an IP is inside any Google network."""
        ip_obj = ip_value if isinstance(ip_value, (IPv4Address, IPv6Address)) else ip_address(ip_value)
        return any(ip_obj.version == net.version and ip_obj in net for net in self.networks)

    def collides_ip(self, ip_value: str | IPAddress) -> bool:
        """Alias of contains_ip for symmetry with CIDR/range collision checks."""
        return self.contains_ip(ip_value)

    def contains_cidr(self, cidr_value: str | IPNetwork) -> bool:
        """Return True if a CIDR is fully contained in Google's networks."""
        network = cidr_value if isinstance(cidr_value, (IPv4Network, IPv6Network)) else ip_network(cidr_value, strict=False)
        return any(network.version == google_net.version and network.subnet_of(google_net) for google_net in self.networks)

    def collides_cidr(self, cidr_value: str | IPNetwork) -> bool:
        """Return True if a CIDR overlaps any Google network."""
        network = cidr_value if isinstance(cidr_value, (IPv4Network, IPv6Network)) else ip_network(cidr_value, strict=False)
        return any(network.version == google_net.version and network.overlaps(google_net) for google_net in self.networks)

    def contains_range(self, start_ip: str | IPAddress, end_ip: str | IPAddress) -> bool:
        """Return True if the entire inclusive IP range is covered by Google networks."""
        range_networks = self._range_to_networks(start_ip, end_ip)
        return all(self.contains_cidr(net) for net in range_networks)

    def collides_range(self, start_ip: str | IPAddress, end_ip: str | IPAddress) -> bool:
        """Return True if any part of an inclusive IP range overlaps Google networks."""
        range_networks = self._range_to_networks(start_ip, end_ip)
        return any(self.collides_cidr(net) for net in range_networks)

    def contains(self, value: str) -> bool:
        """Generic contains check for IP, CIDR, or range like 'a.b.c.d-e.f.g.h'."""
        value = value.strip()
        if "-" in value:
            start_ip, end_ip = self._parse_range(value)
            return self.contains_range(start_ip, end_ip)
        if "/" in value:
            return self.contains_cidr(value)
        return self.contains_ip(value)

    def collides(self, value: str) -> bool:
        """Generic overlap check for IP, CIDR, or range like 'a.b.c.d-e.f.g.h'."""
        value = value.strip()
        if "-" in value:
            start_ip, end_ip = self._parse_range(value)
            return self.collides_range(start_ip, end_ip)
        if "/" in value:
            return self.collides_cidr(value)
        return self.collides_ip(value)

    @staticmethod
    def _parse_range(range_value: str) -> tuple[IPAddress, IPAddress]:
        parts = [part.strip() for part in range_value.split("-", 1)]
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(f"Invalid range format: {range_value!r}")
        return ip_address(parts[0]), ip_address(parts[1])

    @staticmethod
    def _range_to_networks(start_ip: str | IPAddress, end_ip: str | IPAddress) -> tuple[IPNetwork, ...]:
        start_obj = start_ip if isinstance(start_ip, (IPv4Address, IPv6Address)) else ip_address(start_ip)
        end_obj = end_ip if isinstance(end_ip, (IPv4Address, IPv6Address)) else ip_address(end_ip)

        if start_obj.version != end_obj.version:
            raise ValueError("IP range start/end must use the same IP version")

        if int(start_obj) > int(end_obj):
            start_obj, end_obj = end_obj, start_obj

        return tuple(summarize_address_range(start_obj, end_obj))
