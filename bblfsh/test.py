import resource
import typing as t
import unittest

import docker

from bblfsh import (BblfshClient, iterator, TreeOrder,
                    Modes, role_id, role_name)
from bblfsh.launcher import ensure_bblfsh_is_running
from bblfsh.client import NonUTF8ContentException
from bblfsh.node import NodeTypedGetException
from bblfsh.result_context import (Node, NodeIterator, ResultContext)
from bblfsh.pyuast import uast


class BblfshTests(unittest.TestCase):
    BBLFSH_SERVER_EXISTED = None
    fixtures_file = "fixtures/test.py"

    @classmethod
    def setUpClass(cls: t.Any) -> None:
        cls.BBLFSH_SERVER_EXISTED = ensure_bblfsh_is_running()

    @classmethod
    def tearDownClass(cls: t.Any) -> None:
        if not cls.BBLFSH_SERVER_EXISTED:
            client = docker.from_env(version="auto")
            client.containers.get("bblfshd").remove(force=True)
            client.api.close()

    def setUp(self) -> None:
        self.client = BblfshClient("0.0.0.0:9432")

    def _parse_fixture(self) -> ResultContext:
        ctx = self.client.parse(self.fixtures_file)
        self._validate_ctx(ctx)
        return ctx

    def testVersion(self) -> None:
        version = self.client.version()
        self.assertTrue(hasattr(version, "version"))
        self.assertTrue(version.version)
        self.assertTrue(hasattr(version, "build"))
        self.assertTrue(version.build)

    def testNativeParse(self) -> None:
        ctx = self.client.parse(self.fixtures_file, mode=Modes.NATIVE)
        self._validate_ctx(ctx)
        self.assertIsNotNone(ctx)

        it = ctx.filter("//*[@ast_type='NoopLine']")
        self.assertIsNotNone(it)
        self.assertIsInstance(it, NodeIterator)
        res = list(it)
        self.assertGreater(len(res), 1)
        for i in res:
            t = i.get_dict().get("ast_type")
            self.assertIsNotNone(t)
            self.assertEqual(t, "NoopLine")

    def testNonUTF8ParseError(self) -> None:
        self.assertRaises(NonUTF8ContentException,
                          self.client.parse, "", "Python", b"a = '\x80abc'")

    def testUASTDefaultLanguage(self) -> None:
        ctx = self._parse_fixture()
        self.assertEqual(ctx.language, "python")

    def testUASTWithLanguage(self) -> None:
        ctx = self.client.parse(self.fixtures_file, language="Python")
        self._validate_ctx(ctx)
        self.assertEqual(ctx.language, "python")

    def testUASTFileContents(self) -> None:
        with open(self.fixtures_file, "r") as fin:
            contents = fin.read()

        ctx = self.client.parse("file.py", contents=contents)
        self._validate_ctx(ctx)

        def assert_strnode(n: Node, expected: str) -> None:
            self.assertEqual(n.get(), expected)
            self.assertIsInstance(n.get_str(), str)
            self.assertEqual(n.get_str(), expected)

        it = ctx.filter("//uast:RuntimeImport/Path/uast:Alias/Name/uast:Identifier/Name")
        self.assertIsInstance(it, NodeIterator)

        assert_strnode(next(it), "os")
        assert_strnode(next(it), "resource")
        assert_strnode(next(it), "unittest")
        assert_strnode(next(it), "docker")
        assert_strnode(next(it), "bblfsh")
        self.assertRaises(StopIteration, next, it)

    def testBrokenFilter(self) -> None:
        ctx = self._parse_fixture()

        self.assertRaises(RuntimeError, ctx.filter, "dsdfkj32423#$@#$")

    def testFilterToken(self):
        ctx = self._parse_fixture()
        it = ctx.filter("//*[@token='else']/text()")
        first = next(it).get_str()
        self.assertEqual(first, "else")

    def testFilterRoles(self) -> None:
        ctx = self._parse_fixture()
        it = ctx.filter("//*[@role='Identifier']")
        self.assertIsInstance(it, NodeIterator)

        l = list(it)
        self.assertGreater(len(l), 0)

        it = ctx.filter("//*[@role='Friend']")
        self.assertIsInstance(it, NodeIterator)
        l = list(it)
        self.assertEqual(len(l), 0)

    def testFilterProperties(self) -> None:
        ctx = uast()
        obj = {"k1": "v1", "k2": "v2"}
        self.assertTrue(any(ctx.filter("/*[@k1='v1']", obj)))
        self.assertTrue(any(ctx.filter("/*[@k2='v2']", obj)))
        self.assertFalse(any(ctx.filter("/*[@k2='v1']", obj)))
        self.assertFalse(any(ctx.filter("/*[@k1='v2']", obj)))

    def testFilterStartOffset(self) -> None:
        ctx = self._parse_fixture()
        self.assertTrue(any(ctx.filter("//uast:Positions/start/uast:Position[@offset=11749]")))
        self.assertFalse(any(ctx.filter("//uast:Positions/start/uast:Position[@offset=99999]")))

    def testFilterStartLine(self) -> None:
        ctx = self._parse_fixture()
        self.assertTrue(any(ctx.filter("//uast:Positions/start/uast:Position[@line=295]")))
        self.assertFalse(any(ctx.filter("//uast:Positions/start/uast:Position[@line=99999]")))

    def testFilterStartCol(self) -> None:
        ctx = self._parse_fixture()
        self.assertTrue(any(ctx.filter("//uast:Positions/start/uast:Position[@col=42]")))
        self.assertFalse(any(ctx.filter("//uast:Positions/start/uast:Position[@col=99999]")))

    def testFilterEndOffset(self) -> None:
        ctx = self._parse_fixture()
        self.assertTrue(any(ctx.filter("//uast:Positions/end/uast:Position[@offset=11757]")))
        self.assertFalse(any(ctx.filter("//uast:Positions/end/uast:Position[@offset=99999]")))

    def testFilterEndLine(self) -> None:
        ctx = self._parse_fixture()
        self.assertTrue(any(ctx.filter("//uast:Positions/end/uast:Position[@line=321]")))
        self.assertFalse(any(ctx.filter("//uast:Positions/end/uast:Position[@line=99999]")))

    def testFilterEndCol(self) -> None:
        ctx = self._parse_fixture()
        self.assertTrue(any(ctx.filter("//uast:Positions/end/uast:Position[@col=49]")))
        self.assertFalse(any(ctx.filter("//uast:Positions/end/uast:Position[@col=99999]")))

    def testFilterBool(self) -> None:
        ctx = self._parse_fixture()
        self.assertTrue(ctx.filter("boolean(//uast:Positions/end/uast:Position[@col=49])"))
        self.assertTrue(next(ctx.filter("boolean(//uast:Positions/end/uast:Position[@col=49])")).get())
        self.assertTrue(next(ctx.filter("boolean(//uast:Positions/end/uast:Position[@col=49])")).get_bool())

        self.assertFalse(next(ctx.filter("boolean(//uast:Positions/end/uast:Position[@col=9999])")).get())
        self.assertFalse(next(ctx.filter("boolean(//uast:Positions/end/uast:Position[@col=9999])")).get_bool())

    def testFilterNumber(self) -> None:
        ctx = self._parse_fixture()
        self.assertEqual(next(ctx.filter("count(//uast:Positions/end/uast:Position[@col=49])")).get(), 2)
        self.assertEqual(next(ctx.filter("count(//uast:Positions/end/uast:Position[@col=49])")).get_int(), 2)
        self.assertEqual(next(ctx.filter("count(//uast:Positions/end/uast:Position[@col=49])")).get_float(), 2.0)

    def testFilterString(self) -> None:
        ctx = self._parse_fixture()
        self.assertEqual(next(ctx.filter("name(//uast:Positions)")).get(), "uast:Positions")
        self.assertEqual(next(ctx.filter("name(//uast:Positions)")).get_str(), "uast:Positions")

    def testFilterBadQuery(self) -> None:
        ctx = uast()
        self.assertRaises(RuntimeError, ctx.filter, "//[@roleModule]", {})

    def testFilterBadType(self) -> None:
        ctx = self._parse_fixture()
        res = next(ctx.filter("count(//uast:Positions/end/uast:Position[@col=49])"))
        self.assertRaises(NodeTypedGetException, res.get_str)

    def testRoleIdName(self) -> None:
        self.assertEqual(role_id(role_name(1)), 1)
        self.assertEqual(role_name(role_id("IDENTIFIER")),  "IDENTIFIER")

    @staticmethod
    def _itTestTree() -> dict:
        def set_position(node: dict, start_offset: int, start_line: int, start_col: int,
                         end_offset: int, end_line: int, end_col: int) -> None:
            node["@pos"] = {
                "@type": "uast:Positions",
                "start": {
                    "@type": "uast:Position",
                    "offset": start_offset,
                    "line": start_line,
                    "col": start_col
                },
                "end": {
                    "@type": "uast:Position",
                    "offset": end_offset,
                    "line": end_line,
                    "col": end_col
                }
            }
        root = {"@type": "root"}
        set_position(root, 0,1,1, 1,1,2)

        son1 = {"@type": "son1"}
        set_position(son1, 2,2,2, 3,2,3)

        son1_1 = {"@type": "son1_1"}
        set_position(son1_1, 10,10,1, 12,2,2)

        son1_2 = {"@type": "son1_2"}
        set_position(son1_2, 10,10,1, 12,2,2)

        son1["children"] = [son1_1, son1_2]

        son2 = {"@type": "son2"}
        set_position(son2, 100,100,1,  101,100,2)

        son2_1 = {"@type": "son2_1"}
        set_position(son2_1, 5,5,1, 6,5,2)

        son2_2 = {"@type": "son2_2"}
        set_position(son2_2, 15,15,1, 16,15,2)

        son2["children"] = [son2_1, son2_2]
        root["children"] = [son1, son2]

        return root

    @staticmethod
    def _get_nodetypes(iterator: NodeIterator) -> t.List[str]:
        return [n["@type"] for n in
                filter(lambda x: isinstance(x, dict), iterator)]

    def testIteratorPreOrder(self) -> None:
        root = self._itTestTree()
        it = iterator(root, TreeOrder.PRE_ORDER)
        self.assertIsNotNone(it)
        expanded = self._get_nodetypes(it)
        self.assertListEqual(expanded, ['root', 'son1', 'son1_1', 'son1_2',
                                        'son2', 'son2_1', 'son2_2'])

    def testIteratorPostOrder(self) -> None:
        root = self._itTestTree()
        it = iterator(root, TreeOrder.POST_ORDER)
        self.assertIsNotNone(it)
        expanded = self._get_nodetypes(it)
        self.assertListEqual(expanded, ['son1_1', 'son1_2', 'son1', 'son2_1',
                                        'son2_2', 'son2', 'root'])

    def testIteratorLevelOrder(self) -> None:
        root = self._itTestTree()
        it = iterator(root, TreeOrder.LEVEL_ORDER)
        self.assertIsNotNone(it)
        expanded = self._get_nodetypes(it)
        self.assertListEqual(expanded, ['root', 'son1', 'son2', 'son1_1',
                                        'son1_2', 'son2_1', 'son2_2'])

    def testIteratorPositionOrder(self) -> None:
        root = self._itTestTree()
        it = iterator(root, TreeOrder.POSITION_ORDER)
        self.assertIsNotNone(it)
        expanded = self._get_nodetypes(it)
        self.assertListEqual(expanded, ['root', 'son1', 'son2_1', 'son1_1',
                                        'son1_2', 'son2_2', 'son2'])

    def _validate_ctx(self, ctx: ResultContext) -> None:
        self.assertIsNotNone(ctx)
        self.assertIsInstance(ctx, ResultContext)
        self.assertIsInstance(ctx.uast, Node)

    def testFilterInsideIter(self) -> None:
        ctx = self._parse_fixture()
        c2 = uast()
        for n in ctx.iterate(TreeOrder.PRE_ORDER):
            c2.filter("//uast:Positions", n)

    def testItersMixingIterations(self) -> None:
        ctx = self._parse_fixture()
        it = ctx.iterate(TreeOrder.PRE_ORDER)
        next(it); next(it); next(it)

        n = next(it)
        it2 = it.iterate(TreeOrder.PRE_ORDER)
        next(it2)
        a = next(it).get()
        b = next(it2).get()
        self.assertListEqual(a, b)

    def testManyFilters(self) -> None:
        ctx = self._parse_fixture()

        before = resource.getrusage(resource.RUSAGE_SELF)
        for _ in range(10000):
            ctx.filter("//*[@role='Identifier']")

        after = resource.getrusage(resource.RUSAGE_SELF)

        # Check that memory usage has not doubled
        self.assertLess(after[2] / before[2], 2.0)

    def testManyParses(self) -> None:
        before = resource.getrusage(resource.RUSAGE_SELF)
        for _ in range(100):
            self.client.parse(self.fixtures_file)

        after = resource.getrusage(resource.RUSAGE_SELF)

        # Check that memory usage has not doubled
        self.assertLess(after[2] / before[2], 2.0)

    def testManyParsesAndFilters(self) -> None:
        before = resource.getrusage(resource.RUSAGE_SELF)
        for _ in range(100):
            ctx = self.client.parse(self.fixtures_file)
            ctx.filter("//*[@role='Identifier']")

        after = resource.getrusage(resource.RUSAGE_SELF)

        # Check that memory usage has not doubled
        self.assertLess(after[2] / before[2], 2.0)

    def testSupportedLanguages(self) -> None:
        res = self.client.supported_languages()
        self.assertGreater(len(res), 0)
        for l in res:
            for key in ('language', 'version', 'status', 'features'):
                self.assertTrue(hasattr(l, key))
                self.assertIsNotNone(getattr(l, key))


if __name__ == "__main__":
    unittest.main()
