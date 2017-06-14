import argparse
import sys

from bblfsh.client import BblfshClient


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
    args = parser.parse_args()
    return args


def main():
    args = setup()
    client = BblfshClient(args.endpoint)
    print(client.fetch_uast(args.file, args.language))


if __name__ == "__main__":
    sys.exit(main())
