"""Helper module to get assigned URL from localtunnel.me server."""
import json
import traceback

import requests
from requests.exceptions import HTTPError


class DataError(Exception):
    """Raised when data is invalid."""


class AssignedUrlInfo:
    """Assigned URL information."""

    def __init__(self, assigned_id=None, url=None, port=None, max_conn_count=None):
        self.assigned_id = assigned_id
        self.url = url
        self.port = port
        self.max_conn_count = max_conn_count

    def __str__(self):
        return (
            f"AssignedUrlInfo(assigned_id={self.assigned_id}, "
            f"url={self.url}, port={self.port}, "
            f"max_conn_count={self.max_conn_count})"
        )

    def __repr__(self):
        return self.__str__()


def get_assigned_url(
    assigned_domain: str = "?new", localtunnel_server: str = "http://localtunnel.me/"
):
    """Get assigned URL from localtunnel.me server.

    Args:
        assigned_domain (str): Assigned domain name.
        localtunnel_server (str): Localtunnel server URL.

    Returns:
        AssignedUrlInfo: Assigned URL information.

    Raises:
        HTTPError: If HTTP request failed.
        DataError: If data is invalid.
    """
    url = localtunnel_server + assigned_domain

    response = requests.get(url, timeout=60)

    if response.status_code != 200:
        raise HTTPError(f"Failed to get assigned URL: {response.text}")

    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as json_decode_error:
        traceback.print_exc()
        raise DataError(
            f"Failed to get assigned URL: {json_decode_error}"
        ) from json_decode_error

    # Rename id to assigned_id, since id is a reserved keyword
    data["assigned_id"] = data.pop("id")

    if "error" in data:
        raise DataError(f"Failed to get assigned URL: {data['error']}")

    return AssignedUrlInfo(**data)
