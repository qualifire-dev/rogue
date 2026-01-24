from ipaddress import ip_address


def get_host_for_url(host: str) -> str:
    """
    Normalize a host string for use in a URL.

    - Converts 0.0.0.0/:: to 127.0.0.1 (for client connection)
    - Wraps IPv6 addresses in brackets: [::1]
    - Leaves hostnames unchanged
    """
    if host in ("0.0.0.0", "::"):  # nosec B104
        return "127.0.0.1"

    try:
        if ip_address(host).version == 6:
            return f"[{host}]"
    except ValueError:
        pass  # hostname

    return host
