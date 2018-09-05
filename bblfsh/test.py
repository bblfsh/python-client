import os
import resource
import unittest

import docker

from bblfsh import (BblfshClient, filter, iterator, role_id,
        role_name, Node, ParseResponse, TreeOrder, filter_bool,
        filter_number, filter_string)
from bblfsh.launcher import ensure_bblfsh_is_running
from bblfsh.client import NonUTF8ContentException


class BblfshTests(unittest.TestCase):
    BBLFSH_SERVER_EXISTED = None

    @classmethod
    def setUpClass(cls):
        cls.BBLFSH_SERVER_EXISTED = ensure_bblfsh_is_running()

    @classmethod
    def tearDownClass(cls):
        if not cls.BBLFSH_SERVER_EXISTED:
            client = docker.from_env(version="auto")
            client.containers.get("bblfshd").remove(force=True)
            client.api.close()

    def setUp(self):
        self.client = BblfshClient("0.0.0.0:9432")

    def testVersion(self):
        version = self.client.version()
        self.assertTrue(hasattr(version, "version"))
        self.assertTrue(version.version)
        self.assertTrue(hasattr(version, "build"))
        self.assertTrue(version.build)

    def testNativeParse(self):
        reply = self.client.native_parse(__file__)
        assert(reply.ast)

    def testNonUTF8ParseError(self):
        self.assertRaises(NonUTF8ContentException,
                          self.client.parse, "", "Python", b"a = '\x80abc'")

    def testUASTDefaultLanguage(self):
        res = self.client.parse(__file__)
        print(res)
        self._validate_resp(self.client.parse(__file__))

    def testUASTPython(self):
        self._validate_resp(self.client.parse(__file__, language="Python"))

    def testUASTFileContents(self):
        with open(__file__, "rb") as fin:
            contents = fin.read()
        resp = self.client.parse("file.py", contents=contents)
        self._validate_resp(resp)
        self._validate_filter(resp)

    def testBrokenFilter(self):
        self.assertRaises(RuntimeError, filter, 0, "foo")

    def testFilterInternalType(self):
        node = Node()
        node.internal_type = 'a'
        self.assertTrue(any(filter(node, "//a")))
        self.assertFalse(any(filter(node, "//b")))

    def testFilterToken(self):
        node = Node()
        node.token = 'a'
        self.assertTrue(any(filter(node, "//*[@token='a']")))
        self.assertFalse(any(filter(node, "//*[@token='b']")))

    def testFilterRoles(self):
        node = Node()
        node.roles.append(1)
        self.assertTrue(any(filter(node, "//*[@roleIdentifier]")))
        self.assertFalse(any(filter(node, "//*[@roleQualified]")))

    def testFilterProperties(self):
        node = Node()
        node.properties['k1'] = 'v2'
        node.properties['k2'] = 'v1'
        self.assertTrue(any(filter(node, "//*[@k2='v1']")))
        self.assertTrue(any(filter(node, "//*[@k1='v2']")))
        self.assertFalse(any(filter(node, "//*[@k1='v1']")))

    def testFilterStartOffset(self):
        node = Node()
        node.start_position.offset = 100
        self.assertTrue(any(filter(node, "//*[@startOffset=100]")))
        self.assertFalse(any(filter(node, "//*[@startOffset=10]")))

    def testFilterStartLine(self):
        node = Node()
        node.start_position.line = 10
        self.assertTrue(any(filter(node, "//*[@startLine=10]")))
        self.assertFalse(any(filter(node, "//*[@startLine=100]")))

    def testFilterStartCol(self):
        node = Node()
        node.start_position.col = 50
        self.assertTrue(any(filter(node, "//*[@startCol=50]")))
        self.assertFalse(any(filter(node, "//*[@startCol=5]")))

    def testFilterEndOffset(self):
        node = Node()
        node.end_position.offset = 100
        self.assertTrue(any(filter(node, "//*[@endOffset=100]")))
        self.assertFalse(any(filter(node, "//*[@endOffset=10]")))

    def testFilterEndLine(self):
        node = Node()
        node.end_position.line = 10
        self.assertTrue(any(filter(node, "//*[@endLine=10]")))
        self.assertFalse(any(filter(node, "//*[@endLine=100]")))

    def testFilterEndCol(self):
        node = Node()
        node.end_position.col = 50
        self.assertTrue(any(filter(node, "//*[@endCol=50]")))
        self.assertFalse(any(filter(node, "//*[@endCol=5]")))

    def testFilterBool(self):
        node = Node()
        self.assertTrue(filter_bool(node, "boolean(//*[@startOffset or @endOffset])"))
        self.assertFalse(filter_bool(node, "boolean(//*[@blah])"))

    def testFilterNumber(self):
        node = Node()
        node.children.extend([Node(), Node(), Node()])
        self.assertEqual(int(filter_number(node, "count(//*)")), 4)

    def testFilterString(self):
        node = Node()
        node.internal_type = "test"
        self.assertEqual(filter_string(node, "name(//*[1])"), "test")

    def testFilterBadQuery(self):
        node = Node()
        self.assertRaises(RuntimeError, filter, node, "//*roleModule")

    def testFilterBadType(self):
        node = Node()
        node.end_position.col = 50
        self.assertRaises(RuntimeError, filter, node, "boolean(//*[@startPosition or @endPosition])")

    def testRoleIdName(self):
        self.assertEqual(role_id(role_name(1)), 1)
        self.assertEqual(role_name(role_id("IDENTIFIER")),  "IDENTIFIER")

    def _itTestTree(self):
        root = Node()
        root.internal_type = 'root'
        root.start_position.offset = 0
        root.start_position.line = 0
        root.start_position.col = 1

        son1 = Node()
        son1.internal_type = 'son1'
        son1.start_position.offset = 1

        son1_1 = Node()
        son1_1.internal_type = 'son1_1'
        son1_1.start_position.offset = 10

        son1_2 = Node()
        son1_2.internal_type = 'son1_2'
        son1_2.start_position.offset = 10

        son1.children.extend([son1_1, son1_2])

        son2 = Node()
        son2.internal_type = 'son2'
        son2.start_position.offset = 100

        son2_1 = Node()
        son2_1.internal_type = 'son2_1'
        son2_1.start_position.offset = 5

        son2_2 = Node()
        son2_2.internal_type = 'son2_2'
        son2_2.start_position.offset = 15

        son2.children.extend([son2_1, son2_2])
        root.children.extend([son1, son2])

        return root

    def testIteratorPreOrder(self):
        root = self._itTestTree()
        it = iterator(root, TreeOrder.PRE_ORDER)
        self.assertIsNotNone(it)
        expanded = [node.internal_type for node in it]
        self.assertListEqual(expanded, ['root', 'son1', 'son1_1', 'son1_2',
                                        'son2', 'son2_1', 'son2_2'])

    def testIteratorPostOrder(self):
        root = self._itTestTree()
        it = iterator(root, TreeOrder.POST_ORDER)
        self.assertIsNotNone(it)
        expanded = [node.internal_type for node in it]
        self.assertListEqual(expanded, ['son1_1', 'son1_2', 'son1', 'son2_1',
                                        'son2_2', 'son2', 'root'])

    def testIteratorLevelOrder(self):
        root = self._itTestTree()
        it = iterator(root, TreeOrder.LEVEL_ORDER)
        self.assertIsNotNone(it)
        expanded = [node.internal_type for node in it]
        self.assertListEqual(expanded, ['root', 'son1', 'son2', 'son1_1',
                                        'son1_2', 'son2_1', 'son2_2'])

    def testIteratorPositionOrder(self):
        root = self._itTestTree()
        it = iterator(root, TreeOrder.POSITION_ORDER)
        self.assertIsNotNone(it)
        expanded = [node.internal_type for node in it]
        self.assertListEqual(expanded, ['root', 'son1', 'son2_1', 'son1_1',
                                        'son1_2', 'son2_2', 'son2'])

    def _validate_resp(self, resp):
        self.assertIsNotNone(resp)
        self.assertEqual(type(resp).DESCRIPTOR.full_name,
                         ParseResponse.DESCRIPTOR.full_name)
        self.assertEqual(len(resp.errors), 0)
        # self.assertIsInstance() does not work - must be some metaclass magic
        # self.assertIsInstance(resp.uast, Node)

        # Sometimes its fully qualified, sometimes is just "Node"... ditto
        self.assertTrue(resp.uast.__class__.__name__.endswith('Node'))

    def testFilterInsideIter(self):
        root = self.client.parse(__file__).uast
        it = iterator(root, TreeOrder.PRE_ORDER)
        self.assertIsNotNone(it)
        for n in it:
            filter(n, "//*[@roleIdentifier]")

    def testItersMixingIterations(self):
        root = self.client.parse(__file__).uast
        it = iterator(root, TreeOrder.PRE_ORDER)
        next(it); next(it); next(it)
        n = next(it)
        it2 = iterator(n, TreeOrder.PRE_ORDER)
        next(it2)
        assert(next(it) == next(it2))

    def testManyFilters(self):
        root = self.client.parse(__file__).uast
        root.properties['k1'] = 'v2'
        root.properties['k2'] = 'v1'

        before = resource.getrusage(resource.RUSAGE_SELF)
        for _ in range(500):
            filter(root, "//*[@roleIdentifier]")

        after = resource.getrusage(resource.RUSAGE_SELF)

        # Check that memory usage has not doubled after running the filter
        self.assertLess(after[2] / before[2], 2.0)

    def testManyParses(self):
        before = resource.getrusage(resource.RUSAGE_SELF)
        for _ in range(100):
            root = self.client.parse(__file__).uast
            root.properties['k1'] = 'v2'
            root.properties['k2'] = 'v1'

        after = resource.getrusage(resource.RUSAGE_SELF)

        # Check that memory usage has not doubled after running the parse+filter
        self.assertLess(after[2] / before[2], 2.0)

    def testManyParsersAndFilters(self):
        before = resource.getrusage(resource.RUSAGE_SELF)
        for _ in range(100):
            root = self.client.parse(__file__).uast
            root.properties['k1'] = 'v2'
            root.properties['k2'] = 'v1'

            filter(root, "//*[@roleIdentifier]")

        after = resource.getrusage(resource.RUSAGE_SELF)

        # Check that memory usage has not doubled after running the parse+filter
        self.assertLess(after[2] / before[2], 2.0)

    def testSupportedLanguages(self):
        res = self.client.supported_languages()
        self.assertGreater(len(res), 0)
        for l in res:
            for key in ('language', 'version', 'status', 'features'):
                print(key)
                self.assertTrue(hasattr(l, key))
                self.assertIsNotNone(getattr(l, key))

    def _validate_filter(self, resp):
        results = filter(resp.uast, "//Num")
        self.assertIsInstance(resp.uast, Node)
        self.assertEqual(next(results).token, "0")
        self.assertEqual(next(results).token, "1")
        self.assertEqual(next(results).token, "100")
        self.assertEqual(next(results).token, "10")


if __name__ == "__main__":
    unittest.main()
