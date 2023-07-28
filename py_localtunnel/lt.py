"""LocalTunnel module."""
import sys
from py_localtunnel.tunnel import Tunnel


def run_localtunnel(port: int, subdomain: str, remote_server: str):
    """Run localtunnel.

    Args:
        port (int): Internal HTTP server port.
        subdomain (str): Request this subdomain.
        host (str): Remote server, by default, localtunnel's one.
    """
    try:
        # Create tunnel
        tunnel = Tunnel()

        # Get url
        url = tunnel.get_url(subdomain, remote_server)
        print(f" your url is: {url}")

        # Start tunnel
        tunnel.create_tunnel(port)

    except KeyboardInterrupt as keyboard_interrupt:
        raise KeyboardInterrupt(
            "\n KeyboardInterrupt: stopping tunnel"
        ) from keyboard_interrupt

    finally:
        tunnel.stop_tunnel()
        sys.exit(0)
