"""This module is used to create a tunnel between the local server and the remote server."""
import os
import queue
import socket
import threading
import traceback
from urllib.parse import urlparse, urlsplit

from requests.exceptions import HTTPError

from py_localtunnel.get_assigned_url import get_assigned_url


class TunnelConn:
    """Tunnel connection."""

    def __init__(
        self, remote_host: str, remote_port: int, local_port: int, debug: bool = False
    ):
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.local_port = local_port
        self.remote_conn = None
        self.local_conn = None
        self.error_channel = None
        self.debug = debug

    def tunnel(self, reply_ch: queue.Queue):
        """Create tunnel between local server and remote server.

        Args:
            reply_ch (queue.Queue): Reply channel.
        """
        # Clear previous channel's message
        self.error_channel = []

        try:
            # Connect to remote server and local server
            self.remote_conn = self.connect_remote()
            self.local_conn = self.connect_local()

            # Create two threads to copy data between the two connections
            receiving_thread = threading.Thread(
                target=self.copy_data, args=(self.remote_conn, self.local_conn)
            )
            sending_thread = threading.Thread(
                target=self.copy_data, args=(self.local_conn, self.remote_conn)
            )

            # Start new threads
            receiving_thread.start()
            sending_thread.start()

            # Wait for threads to finish
            receiving_thread.join()
            sending_thread.join()

        except (ConnectionRefusedError,):
            if self.debug:
                traceback.print_exc()

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
        proxy = os.getenv("HTTP_PROXY", os.getenv("http_proxy"))

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
        try:
            while True:
                data = source.recv(4096)
                if not data:
                    break
                destination.sendall(data)

        except (OSError,) as exception:
            if self.debug:
                traceback.print_exc()

            if self.error_channel is not None:
                self.error_channel.append(exception)


class Tunnel:
    """Tunnel."""

    def __init__(self, debug: bool = False):
        self.assigned_url_info = None
        self.local_port = None
        self.tunnel_conns = []
        self.cmd_chan = queue.Queue()
        self.debug = debug

    def start_tunnel(self, remote_server: str = "http://localtunnel.me/") -> None:
        """Start tunnel."""
        self.check_local_port()
        max_conn_count = self.assigned_url_info.max_conn_count
        reply_ch = queue.Queue(maxsize=max_conn_count)
        remote_host = urlsplit(remote_server).netloc

        for _ in range(max_conn_count):
            # print(f'Start tunnel connection {connection_index}.')
            tunnel_conn = TunnelConn(
                remote_host, self.assigned_url_info.port, self.local_port, self.debug
            )
            self.tunnel_conns.append(tunnel_conn)

            thread = threading.Thread(target=tunnel_conn.tunnel, args=(reply_ch,))

            thread.start()

        while reply_ch.qsize() < max_conn_count:
            if self.cmd_chan.get() == "STOP":
                break

    def stop_tunnel(self) -> None:
        """Stop tunnel."""
        if self.debug:
            print(f" Info: Stop tunnel for localPort[{self.local_port}]!")
        self.cmd_chan.put("STOP")

        # Wait for all tunnel connections to stop
        for tunnel_conn in self.tunnel_conns:
            tunnel_conn.stop_tunnel(self.debug)

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
        self.assigned_url_info = get_assigned_url(assigned_domain, remote_server)
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
            raise ConnectionRefusedError(
                " Error: Cannot connect to local port"
            ) from exception
