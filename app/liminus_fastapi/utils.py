import binascii
import ipaddress
import logging
import math
import re
import socket
from datetime import timedelta
from os import getenv
from typing import Optional, Pattern, Union

compiled_path_regexes = {}


def _get_compiled_prefix_regex(prefix_regex: str) -> Pattern:
    # ensure this regex is "starts with"
    if prefix_regex[0] != '^':
        prefix_regex = '^' + prefix_regex

    # keep a cache of compiled regexes
    if prefix_regex not in compiled_path_regexes:
        compiled_path_regexes[prefix_regex] = re.compile(prefix_regex)

    return compiled_path_regexes[prefix_regex]


def get_env_var(name: str, default: str = None):
    value = getenv(name, default)

    if value is None:
        raise EnvironmentError(f'Environment variable {name} is not set.')

    return value


def to_seconds(**kwargs):
    return int(timedelta(**kwargs).total_seconds())


def path_matches(
    request_path: str, path: Optional[str] = None, path_regex: Optional[str] = None, match_prefix: bool = False
) -> bool:
    if path is not None:
        if match_prefix and request_path.startswith(path):
            return True
        elif request_path == path:
            return True

    if path_regex is not None:
        regex = _get_compiled_prefix_regex(path_regex)
        if regex.match(request_path):
            return True

    return False


def strip_path_prefix(request_path: str, path: Optional[str] = None, path_regex: Optional[str] = None) -> str:
    if path is not None and request_path.startswith(path):
        offset = len(path)
        return request_path[offset:]

    if path_regex is not None:
        regex = _get_compiled_prefix_regex(path_regex)

        return re.sub(regex, '', request_path)

    return request_path


def ensure_bytes(input: Union[str, bytes, bytearray]) -> bytes:
    if isinstance(input, (bytes, bytearray)):
        return input

    return input.encode()


def normalize_ip_address(ip_address_string: str) -> Optional[str]:
    """
    Normalizes IPv4 and IPv6 addresses to a 32 character hexidecimal representation
    """
    if not ip_address_string:
        return None

    try:
        ip_address = ipaddress.ip_address(ip_address_string)
        flag = socket.AF_INET6 if isinstance(ip_address, ipaddress.IPv6Address) else socket.AF_INET
        bin_hex_string = socket.inet_pton(flag, str(ip_address))
        prefix = 'FFFF' if isinstance(ip_address, ipaddress.IPv4Address) else ''
        hex_string = prefix + binascii.b2a_hex(bin_hex_string).decode()
        return f'{hex_string.upper():0>32}'
    except Exception:
        return None


def denormalize_ip_address(normalized_ip_address: str) -> str:
    if not normalized_ip_address:
        return ''

    packed = bytes.fromhex(normalized_ip_address)
    ip = socket.inet_ntop(socket.AF_INET6, packed)

    if ip.startswith('::ffff:'):
        # is an IPv4
        ip = ip[7:]

    return ip


def loggable_string(val: str, maxlen: int = 0, head: int = 0, tail: int = 0, describe_chars_removed=False) -> str:
    if not maxlen:
        maxlen = head + tail
    if not head and not tail:
        head = math.floor(maxlen * 0.5)
        tail = maxlen - head

    if len(val) <= maxlen:
        return val

    start = val[:head] if head else ''
    end = val[-tail:] if tail else ''

    middle = '...'
    if describe_chars_removed:
        middle = f'... ({len(val) - maxlen} chars removed) ...'

    return f'{start}{middle}{end}'


def loggable_url(url):
    return re.sub(r'//.*@', '//<redacted>@', url)
