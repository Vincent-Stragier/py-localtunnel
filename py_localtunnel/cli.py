import argparse
import sys
from py_localtunnel.lt import run_localtunnel

__version__ = "1.0.2"
PACKAGE_NAME = "pylt"

TYPICAL_USAGE = """example:
   pylt --port {port_number}
   pylt -p {port_number} -s {your_custom_subdomain}
   pylt -p {port_number} -u {your_custom_remote_server}"""


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=PACKAGE_NAME,
        description="localtunnel alternative in python",
        epilog=TYPICAL_USAGE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Positional arguments
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="Internal HTTP server port (0 - 65535)",
        required=True,
    )

    # Optional arguments
    parser.add_argument(
        "-s",
        "--subdomain",
        type=str,
        default="",
        help="Request this subdomain",
    )
    parser.add_argument(
        "-u",
        "--url",
        type=str,
        default="http://localtunnel.me",
        help="Remote server, by default, localtunnel's one (http://localtunnel.me)",
    )

    # Version
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"{PACKAGE_NAME} version {__version__}",
        help="Check version of this package",
    )

    # Parse arguments
    args = parser.parse_args(argv)

    if args.port < 0 or args.port > 65535:
        print(
            "Invalid port number, must be between 0 and 65535 inclusive,"
            f" got: {args.port}"
        )
        sys.exit(1)

    run_localtunnel(args.port, args.subdomain, args.url)


if __name__ == "__main__":
    raise SystemExit(main())
