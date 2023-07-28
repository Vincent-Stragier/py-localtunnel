"""LocalTunnel module."""
import sys
import traceback

from py_localtunnel.tunnel import Tunnel


def run_localtunnel(port: int, subdomain: str, remote_server: str, debug: bool = False):
    """Run localtunnel.

    Args:
        port (int): Internal HTTP server port.
        subdomain (str): Request this subdomain.
        host (str): Remote server, by default, localtunnel's one.
    """
    try:
        # Create tunnel
        tunnel = Tunnel(debug)

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
        if debug:
            traceback.print_exc()
        tunnel.stop_tunnel()
        sys.exit(0)
