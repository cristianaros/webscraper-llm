"""Normalización de URL y límites de destino para fuentes autorizadas."""

from __future__ import annotations

import ipaddress
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from shared.contracts import SourceConfig

_TRACKING_KEYS = frozenset({"fbclid", "gclid"})


def normalize_url(url: str, base: str | None = None) -> str:
    value = urlsplit(urljoin(base, url) if base else url)
    if value.scheme.lower() not in {"http", "https"} or not value.hostname:
        raise ValueError("unsupported_url")
    if value.username or value.password:
        raise ValueError("credentials_in_url")
    host = value.hostname.encode("idna").decode("ascii").lower()
    try:
        port = value.port
    except ValueError as exc:
        raise ValueError("invalid_port") from exc
    if ":" in host:
        host = f"[{host}]"
    if port and (value.scheme.lower(), port) not in {("http", 80), ("https", 443)}:
        host += f":{port}"
    pairs = [
        (key, item)
        for key, item in parse_qsl(value.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in _TRACKING_KEYS
    ]
    return urlunsplit((value.scheme.lower(), host, value.path or "/", urlencode(pairs), ""))


def validate_destination(url: str, source: SourceConfig, resolved_ips: list[str]) -> None:
    """Reject destinations outside a source and private/reserved DNS answers."""
    normalized = normalize_url(url)
    hostname = urlsplit(normalized).hostname
    assert hostname is not None
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        raise ValueError("literal_ip_not_allowed")
    # Image CDN hosts are intentionally not valid article destinations.
    allowed = {host.rstrip(".").lower() for host in source.allowed_hosts}
    if hostname.rstrip(".").lower() not in allowed:
        raise ValueError("destination_host_not_allowed")
    if not resolved_ips:
        raise ValueError("destination_not_resolved")
    try:
        addresses = [ipaddress.ip_address(value) for value in resolved_ips]
    except ValueError as exc:
        raise ValueError("invalid_resolved_ip") from exc
    if not all(address.is_global for address in addresses):
        raise ValueError("private_destination")
