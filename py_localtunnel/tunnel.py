"""This module is used to create a tunnel between the local server and the remote server."""
import os
import socket
import queue
import threading
from py_localtunnel.get_assigned_url import get_assigned_url
from requests.exceptions import HTTPError
from urllib.parse import urlparse, urlsplit

DEBUG = True


class TunnelConn:
    """Tunnel connection."""

    def __init__(self, remote_host: str, remote_port: int, local_port: int):
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.local_port = local_port
        self.remote_conn = None
        self.local_conn = None
        self.error_channel = None

    def tunnel(self, reply_ch: queue.Queue):
        """Create tunnel between local server and remote server.

        Args:
            reply_ch (queue.Queue): Reply channel.
        """
        # Clear previous channel's message
        self.error_channel = []

        try:
            remote_conn = self.connect_remote()
            local_conn = self.connect_local()
            self.remote_conn = remote_conn
            self.local_conn = local_conn

            # Start two threads to copy data between the two connections
            thread_1 = threading.Thread(
                target=self.copy_data, args=(remote_conn, local_conn)
            )
            thread_2 = threading.Thread(
                target=self.copy_data, args=(local_conn, remote_conn)
            )

            # Start new Threads
            thread_1.start()
            thread_2.start()

            # Wait for threads to finish
            thread_1.join()
            thread_2.join()

        except Exception as e:
            if DEBUG:
                print(f"Stop copy data! error=[{e}]")

        finally:
            if self.remote_conn:
                self.remote_conn.close()

            if self.local_conn:
                self.local_conn.close()

            reply_ch.put(1)

    def stop_tunnel(self):
        """Stop tunnel connections."""
        if self.remote_conn:
            self.remote_conn.close()

        if self.local_conn:
            self.local_conn.close()

    def connect_remote(self):
        """Connect to remote server."""
        remote_addr = (self.remote_host, self.remote_port)
        proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")

        # If proxy is not set, connect directly to remote server
        if not proxy:
            return socket.create_connection(remote_addr)

        proxy_url = urlparse(proxy)
        remote_conn = socket.create_connection(proxy_url.netloc.split(":"))
        connect_request = (
            f"CONNECT {self.remote_host}:{self.remote_port}"
            f" HTTP/1.1\r\nHost: {self.remote_host}\r\n\r\n"
        )
        remote_conn.sendall(connect_request.encode())
        response = remote_conn.recv(4096)

        if not response.startswith(b"HTTP/1.1 200"):
            raise HTTPError(f"Failed to connect via proxy: {response}")

        return remote_conn

    def connect_local(self):
        """Connect to local server."""
        return socket.create_connection(("localhost", self.local_port))

    def copy_data(self, source: socket.socket, destination: socket.socket):
        """Copy data between two connections.

        Args:
            source (socket.socket): Source connection.
            destination (socket.socket): Destination connection.
        """
        e = None  # initialize e to None
        try:
            while True:
                data = source.recv(4096)
                if not data:
                    break
                destination.sendall(data)

        except Exception as ex:
            if DEBUG:
                print(f"Stop copy data! error=[{ex}]")
            e = ex  # assign the exception to e

        finally:
            if self.error_channel is not None and e is not None:
                self.error_channel.append(e)


class Tunnel:
    """Tunnel."""

    def __init__(self):
        self.assigned_url_info = None
        self.local_port = None
        self.tunnel_conns = []
        self.cmd_chan = queue.Queue()

    def start_tunnel(self, remote_server: str = "http://localtunnel.me/") -> None:
        """Start tunnel."""
        self.check_local_port()
        reply_ch = queue.Queue(maxsize=self.assigned_url_info.max_conn_count)
        remote_host = urlsplit(remote_server).netloc

        for _ in range(self.assigned_url_info.max_conn_count):
            tunnel_conn = TunnelConn(
                remote_host, self.assigned_url_info.port, self.local_port
            )
            self.tunnel_conns.append(tunnel_conn)
            thread = threading.Thread(
                target=tunnel_conn.tunnel, args=(reply_ch,))
            thread.start()

        while reply_ch.qsize() < self.assigned_url_info.max_conn_count:
            cmd = self.cmd_chan.get()
            if cmd == "STOP":
                break

    def stop_tunnel(self) -> None:
        """Stop tunnel."""
        if DEBUG:
            print(f" Info: Stop tunnel for localPort[{self.local_port}]!")
        self.cmd_chan.put("STOP")

        # Wait for all tunnel connections to stop
        for tunnel_conn in self.tunnel_conns:
            tunnel_conn.stop_tunnel()

    def get_url(
        self, assigned_domain: str, remote_server: str = "http://localtunnel.me/"
    ) -> str:
        """Get url.

        Args:
            assigned_domain (str): assigned domain.

        Returns:
            str: _description_
        """
        if not assigned_domain:
            assigned_domain = "?new"
        self.assigned_url_info = get_assigned_url(
            assigned_domain, remote_server)
        self.tunnel_conns = []
        return self.assigned_url_info.url

    def create_tunnel(self, local_port: int) -> None:
        """Create tunnel.

        Args:
            local_port (int): local port.
        """
        self.local_port = local_port
        self.start_tunnel()

    def check_local_port(self):
        """Check local port."""
        try:
            with socket.create_connection(("localhost", self.local_port)) as _:
                pass
        except ConnectionRefusedError as exception:
            # traceback.print_exc()
            raise ConnectionRefusedError(
                " Error: Cannot connect to local port"
            ) from exception
