from py_localtunnel.tunnel import Tunnel


def run_localtunnel(port: int, subdomain: str):
    tunnel = Tunnel()
    url = tunnel.get_url(subdomain)
    print(f" your url is: {url}")

    try:
        tunnel.create_tunnel(port)
    except KeyboardInterrupt:
        print("\n KeyboardInterrupt: stopping tunnel")

    tunnel.stop_tunnel()
    exit(0)
