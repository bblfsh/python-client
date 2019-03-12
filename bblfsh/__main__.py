import argparse
import pprint
import sys

from bblfsh.client import BblfshClient
from bblfsh.launcher import ensure_bblfsh_is_running


def setup() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Query for a UAST to Babelfish and dump it to stdout."
    )
    parser.add_argument("-e", "--endpoint", default="0.0.0.0:9432",
                        help="bblfsh gRPC endpoint.", type=str)
    parser.add_argument("-f", "--file", required=True,
                        help="File to parse.", type=str)
    parser.add_argument("-l", "--language", default=None,
                        help="File's language. The default is to autodetect.", type=str)
    parser.add_argument("--disable-bblfsh-autorun", action="store_true",
                        help="Do not automatically launch Babelfish server "
                             "if it is not running.")

    parser.add_argument("-q", "--query", default="", help="xpath query", type=str)
    parser.add_argument("-a", "--array", help='print results as a parseable Python array', action='store_true')

    return parser.parse_args()


def run_query(uast, query: str, array: bool) -> None:
    result_iter = uast.filter(query)
    if not result_iter:
        print("Nothing found")

    result_list = [x.load() for x in result_iter]

    if array:
        pprint.pprint(result_list)
    else:
        print("%d Results:" % len(result_list))
        for i, node in enumerate(result_list):
            print("== {} ==================================".format(i+1))
            print(node)


def main() -> int:
    args = setup()
    if not args.disable_bblfsh_autorun:
        ensure_bblfsh_is_running()

    client = BblfshClient(args.endpoint)
    ctx = client.parse(args.file, args.language)

    if args.query:
        run_query(ctx, args.query, array=args.array)
    else:
        pprint.pprint(ctx.load())

    return 0


if __name__ == "__main__":
    sys.exit(main())
