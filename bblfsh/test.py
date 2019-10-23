import resource
import typing as t
import unittest
import gc
import bblfsh
import docker

from bblfsh import (BblfshClient, iterator, TreeOrder,
                    Modes, role_id, role_name)
from bblfsh.launcher import ensure_bblfsh_is_running
from bblfsh.client import NonUTF8ContentException
from bblfsh.node import NodeTypedGetException
from bblfsh.result_context import (Node, NodeIterator, ResultContext)
from bblfsh.pyuast import uast, decode
from functools import cmp_to_key


class BblfshTests(unittest.TestCase):
    BBLFSH_SERVER_EXISTED = None
    fixtures_pyfile = "fixtures/test.py"
    fixtures_cfile = "fixtures/test.c"

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
        self.client = BblfshClient("localhost:9432")

    def _parse_fixture(self) -> ResultContext:
        ctx = self.client.parse(self.fixtures_pyfile)
        self._validate_ctx(ctx)
        return ctx

    def testVersion(self) -> None:
        version = self.client.version()

        self.assertTrue(hasattr(version, "version"))
        self.assertTrue(version.version)
        self.assertTrue(hasattr(version, "build"))
        self.assertTrue(version.build)

    def testServerVersion(self) -> None:
        version = self.client.server_version().version

        self.assertTrue(hasattr(version, "version"))
        self.assertTrue(version.version)
        self.assertTrue(hasattr(version, "build"))

    def testNativeParse(self) -> None:
        ctx = self.client.parse(self.fixtures_pyfile, mode=Modes.NATIVE)
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
        ctx = self.client.parse(self.fixtures_pyfile, language="Python")
        self._validate_ctx(ctx)
        self.assertEqual(ctx.language, "python")

    def testUASTWithLanguageAlias(self) -> None:
        ctx = self.client.parse(self.fixtures_cfile)
        self._validate_ctx(ctx)
        self.assertEqual(ctx.language, "c")

        it = ctx.filter("//uast:FunctionGroup/Nodes/uast:Alias/Name/uast:Identifier/Name")
        self.assertIsInstance(it, NodeIterator)

        self.assertEqual(next(it).get(), "main")
        self.assertEqual(next(it).get(), "fib")


    def testUASTFileContents(self) -> None:
        with open(self.fixtures_pyfile, "r") as fin:
            contents = fin.read()

        ctx = self.client.parse("file.py", contents=contents)
        self._validate_ctx(ctx)

        def assert_strnode(n: Node, expected: str) -> None:
            self.assertEqual(n.get(), expected)
            self.assertIsInstance(n.get_str(), str)
            self.assertEqual(n.get_str(), expected)

        it = ctx.filter("//uast:RuntimeImport/Path/uast:Identifier/Name")
        self.assertIsInstance(it, NodeIterator)

        assert_strnode(next(it), "os")
        assert_strnode(next(it), "resource")
        assert_strnode(next(it), "unittest")
        assert_strnode(next(it), "docker")
        assert_strnode(next(it), "bblfsh")
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

    @staticmethod
    def _get_nodes(iterator: NodeIterator) -> t.List[dict]:
        return [n.get() for n in iterator]

    @staticmethod
    def _get_positions(iterator: NodeIterator):
        startPositions = [ n["@pos"]["start"] for n in
                           filter(lambda x: isinstance(x, dict) and
                                  "@pos" in x.keys() and
                                  "start" in x["@pos"].keys(), iterator) ]
        return [ (int(n["offset"]), int(n["line"]), int(n["col"])) for n in startPositions ]

    def decrefAndGC(self, obj) -> None:
        del obj
        gc.collect()

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
        # Check first our homemade tree
        root = self._itTestTree()
        it = iterator(root, TreeOrder.POSITION_ORDER)
        self.assertIsNotNone(it)
        expanded = self._get_nodetypes(it)
        self.assertListEqual(expanded, ['root', 'son1', 'son2_1', 'son1_1',
                                        'son1_2', 'son2_2', 'son2'])
        # Check that when using the positional order the positions we get are
        # in fact sorted by (offset, line, col)
        it = iterator(root, TreeOrder.POSITION_ORDER)
        positions = self._get_positions(it)
        self.assertListEqual(positions, [(0,1,1), (2,2,2), (5,5,1), (10,10,1),
                                         (10,10,1), (15,15,1), (100,100,1)])

    def testAnyOrder(self) -> None:
        root = self._itTestTree()
        it = iterator(root, TreeOrder.ANY_ORDER)
        self.assertIsNotNone(it)
        expanded = self._get_nodetypes(it)
        # We only can test that the order gives us all the nodes
        self.assertEqual(set(expanded), {'root', 'son1', 'son2', 'son1_1',
                                         'son1_2', 'son2_1', 'son2_2'})

    def testChildrenOrder(self) -> None:
        root = self._itTestTree()
        it = iterator(root, TreeOrder.CHILDREN_ORDER)
        self.assertIsNotNone(it)
        expanded = self._get_nodetypes(it)
        # We only can test that the order gives us all the nodes
        self.assertEqual(expanded, ['son1', 'son2'])

    # Iterating from the root node should give the same result as
    # iterating from the tree, for every available node
    def testNodeIteratorEqualsCtxIterator(self) -> None:
        ctx = self._parse_fixture()
        root = ctx.root

        for order in TreeOrder:
            itCtx  = ctx.iterate(order)
            itRoot = root.iterate(order)
            self.assertListEqual(self._get_nodes(itCtx), self._get_nodes(itRoot))

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
        next(it); next(it); next(it); next(it)

        it2 = it.iterate(TreeOrder.PRE_ORDER)
        next(it2)

        a = next(it).get()
        b = next(it2).get()
        self.assertEqual(a, b)

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
            self.client.parse(self.fixtures_pyfile)

        after = resource.getrusage(resource.RUSAGE_SELF)

        # Check that memory usage has not doubled
        self.assertLess(after[2] / before[2], 2.0)

    def testManyParsesAndFilters(self) -> None:
        before = resource.getrusage(resource.RUSAGE_SELF)
        for _ in range(100):
            ctx = self.client.parse(self.fixtures_pyfile)
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

    def testSupportedLanguageManifests(self) -> None:
        langs_with_aliases = {'csharp', 'cpp', 'javascript', 'bash'}
        res = self.client.supported_language_manifests()
        self.assertGreater(len(res), 0)
        for l in res:
            for key in ('name', 'language', 'version', 'status', 'features'):
                self.assertTrue(hasattr(l, key))
                self.assertIsNotNone(getattr(l, key))
            if getattr(l, 'language') in langs_with_aliases:
                self.assertTrue(hasattr(l, 'aliases'))
                self.assertGreater(len(getattr(l, 'aliases')), 0)

    def testEncode(self) -> None:
        ctx = self._parse_fixture()
        # This test is here for backward compatibility purposes,
        # in case someone was relying on encoding contexts this way
        self.assertEqual(ctx.ctx.encode(None, 0), ctx._response.uast)
        self.assertEqual(ctx.encode(), ctx._response.uast)

    def testEncodeWithEmptyContext(self) -> None:
        ctx = ResultContext()
        obj = {"k1": "v1", "k2": "v2"}
        fmt = 1 # YAML

        # This test is here for backward compatibility purposes,
        # in case someone was relying on encoding contexts this way
        data = ctx.ctx.encode(obj, fmt)
        other_data = ctx.encode(obj, fmt)
        self.assertDictEqual(obj, decode(data, format = fmt).load())
        self.assertDictEqual(obj, decode(other_data, format = fmt).load())

    def testGetAll(self) -> None:
        ctx = self._parse_fixture()

        expected = ["os", "resource", "unittest", "docker", "bblfsh"]
        actual = []
        for k in ctx.get_all()["body"]:
            if "@type" in k and k["@type"] == "uast:RuntimeImport" and "Path" in k:
                path = k["Path"]
                if "Name" in path:
                    actual.append(k["Path"]["Name"])

        self.assertListEqual(expected, actual)

    def testLoad(self) -> None:
        ctx = self._parse_fixture()

        it = ctx.iterate(TreeOrder.PRE_ORDER)
        next(it); next(it); next(it); next(it)

        it2 = it.iterate(TreeOrder.PRE_ORDER)
        n = next(it2)
        node_ext = n.node_ext

        obj = node_ext.load()
        typ = obj["@type"]
        self.assertEqual("uast:RuntimeImport", typ)

        path = obj["Path"]
        self.assertEqual("uast:Identifier", path["@type"])
        self.assertEqual("os", path["Name"])

    # The following testOrphan{x} methods verifies that iterators and nodes work
    # correctly once the context they come from has been DECREFed. Loading an
    # (external) node and filtering it after the context / iterators have been
    # DECREFed are also checked. As an example, the following code should work
    # in Python:
    #
    # its = []
    # for file in files:
    #    ctx = client.parse(file)
    #    it = ctx.filter("blablablah")
    #    its.append(it)
    #
    # it = pick a it from its
    # node = next(it)
    #
    # Instead of testing with a while, we can just delete ctx before doing
    # something with the iterator
    def testOrphanFilter(self) -> None:
        ctx = self._parse_fixture()
        it = ctx.filter("//uast:RuntimeImport")
        self.decrefAndGC(ctx)
        # We should be able to retrieve values from the iterator
        # after the context has been DECREFed but the iterator
        # still exists
        obj = next(it).get()
        typ = obj["@type"]
        self.assertEqual("uast:RuntimeImport", typ)

        # Chaining calls has the same effect as splitting
        # the effect across different lines as above
        self.decrefAndGC(it)
        it = self._parse_fixture().filter("//uast:RuntimeImport")
        next(it)
        obj = next(it).get()
        typ = obj["@type"]
        self.assertEqual("uast:RuntimeImport", typ)

    def testOrphanIterator(self) -> None:
        ctx = self._parse_fixture()
        it = ctx.iterate(TreeOrder.PRE_ORDER)
        self.decrefAndGC(ctx)
        # We should be able to retrieve values from the iterator
        # after the context has been DECREFed but the iterator
        # still exists
        obj = next(it).get()
        self.assertIsInstance(obj, dict)

        # Chaining calls has the same effect as splitting
        # the effect across different lines as above
        self.decrefAndGC(it)
        it = self._parse_fixture().iterate(TreeOrder.POST_ORDER)
        obj = next(it)
        self.assertIsInstance(obj, Node)

    def testLoadOrphanNode(self) -> None:
        ctx = self._parse_fixture()
        it = ctx.iterate(TreeOrder.PRE_ORDER)
        # The underlying ctx should not be deallocated even if ctx goes
        # out of scope because the iterator is still alive
        self.decrefAndGC(ctx)
        next(it); next(it); next(it);
        node = next(it)
        self.decrefAndGC(it)
        # Context should not have been deallocated yet because we
        # want to iterate from the node onwards
        it2 = node.iterate(TreeOrder.PRE_ORDER)
        node_ext = node.node_ext
        # node could be deallocated here also, if we by, any chance,
        # we happen to be storing only the external nodes
        self.decrefAndGC(node)
        obj = node_ext.load()
        typ = obj["@type"]
        self.assertEqual("uast:RuntimeImport", typ)

    def testFilterOrphanNode(self) -> None:
        ctx = self._parse_fixture()
        root = ctx.root
        self.decrefAndGC(ctx)
        # filter should work here over the tree even if we ctx has
        # been DECREFed by the interpreter (it has gone out of scope)
        it = root.filter("//uast:RuntimeImport")
        obj = next(it).get()
        typ = obj["@type"]
        self.assertEqual("uast:RuntimeImport", typ)

    def testPythonContextIterate(self) -> None:
        # C++ memory context
        ctxC = self._parse_fixture()
        # Python memory context
        pyDict = ctxC.root.get()
        ctxPy = bblfsh.context(pyDict)

        for treeOrder in TreeOrder:
            itC = ctxC.iterate(treeOrder)
            itPy = ctxPy.iterate(treeOrder)

            for nodeC, nodePy in zip(itC, itPy):
                self.assertEqual(nodeC.get(), nodePy)

    def testPythonContextFilter(self) -> None:
        # C++ memory context
        ctxC = self._parse_fixture()
        # Python memory context
        pyDict = ctxC.root.get()
        ctxPy = bblfsh.context(pyDict)

        itC = ctxC.filter("//*[@role='Identifier']")
        itPy = ctxPy.filter("//*[@role='Identifier']")

        for nodeC, nodePy in zip(itC, itPy):
            self.assertEqual(nodeC.get(), nodePy)

    def testBinaryEncodeDecodePythonContext(self) -> None:
        # Binary encoding should be invertible
        # C++ memory context
        ctxC = self._parse_fixture()
        # Python memory context
        pyDict = ctxC.root.get()
        ctxPy = bblfsh.context(pyDict)
        encoded = ctxPy.encode(fmt = 0) # Binary encoding
        decoded = decode(encoded, format = 0)

        self.assertEqual(pyDict, decoded.load())

    def testInvalidDecodeBytes(self) -> None:
        with self.assertRaises(RuntimeError):
            decode(b'', format = 0)
        with self.assertRaises(RuntimeError):
            decode(b'abcdef', format = 0)

if __name__ == "__main__":
    unittest.main()
