import argparse
import sys

from bblfsh.client import BblfshClient
from bblfsh.launcher import ensure_bblfsh_is_running


def setup():
    parser = argparse.ArgumentParser(
        description="Query for a UAST to Babelfish and dump it to stdout."
    )
    parser.add_argument("-e", "--endpoint", default="0.0.0.0:9432",
                        help="bblfsh gRPC endpoint.")
    parser.add_argument("-f", "--file", required=True,
                        help="File to parse.")
    parser.add_argument("-l", "--language", default=None,
                        help="File's language. The default is to autodetect.")
    parser.add_argument("--disable-bblfsh-autorun", action="store_true",
                        help="Do not automatically launch Babelfish server "
                             "if it is not running.")
    args = parser.parse_args()
    return args


def main():
    args = setup()
    if not args.disable_bblfsh_autorun:
        ensure_bblfsh_is_running()
    client = BblfshClient(args.endpoint)
    print(client.parse(args.file, args.language))


if __name__ == "__main__":
    sys.exit(main())
