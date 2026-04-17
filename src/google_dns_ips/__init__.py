"""Public API for google_dns_ips."""

from .resolver import (
    DEFAULT_HOST_SOURCES,
    DEFAULT_TXT_SOURCES,
    ResolutionResult,
    get_google_ip_cidrs,
    get_google_ip_networks,
)
from .query import GoogleIPQuery

__all__ = [
    "DEFAULT_HOST_SOURCES",
    "DEFAULT_TXT_SOURCES",
    "GoogleIPQuery",
    "ResolutionResult",
    "get_google_ip_cidrs",
    "get_google_ip_networks",
]
