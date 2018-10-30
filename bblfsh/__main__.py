import argparse
import sys

import bblfsh
from bblfsh.pyuast import filter

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

    parser.add_argument("-q", "--query", default="", help="xpath query")
    parser.add_argument("-m", "--mapn", default="", help="transform function of the results (n)")
    parser.add_argument("-a", "--array", help='print results as an array', action='store_true')

    args = parser.parse_args()
    return args

def run_query(root: bblfsh.Node, query: str, mapn: str, as_array: bool) -> None:
    result = list(filter(root, query))

    if not result:
        print("Nothing found")

    else:
        if mapn:
            result = [eval(mapn) for n in result]

        if as_array:
            print("results[{}] = {}".format(len(result), result))
        else:
            print("Running xpath query: {}".format(query))
            print("FOUND {} roots".format(len(result)))

            for i, node in enumerate(result):
                print("== {} ==================================".format(i+1))
                print(node)

def main():
    args = setup()
    if not args.disable_bblfsh_autorun:
        ensure_bblfsh_is_running()

    client = BblfshClient(args.endpoint)
    response = client.parse(args.file, args.language)
    root = response.uast
    if len(response.errors):
        sys.stderr.write("\n".join(response.errors) + "\n")
    query = args.query
    if query:
        run_query(root, query, args.mapn, args.array)
    else:
        print(root)

if __name__ == "__main__":
    sys.exit(main())
