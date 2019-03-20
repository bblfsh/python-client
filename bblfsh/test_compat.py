import os
import resource
import unittest


import docker

from bblfsh.compat import (
    filter as xpath_filter, role_id, iterator, role_name, Node, TreeOrder, filter_bool,
    filter_number, CompatNodeIterator
)
from bblfsh.compat import CompatBblfshClient as BblfshClient
from bblfsh.launcher import ensure_bblfsh_is_running
from bblfsh.client import NonUTF8ContentException


class BblfshTests(unittest.TestCase):
    BBLFSH_SERVER_EXISTED = None
    fixtures_file = "fixtures/test.py"

    @classmethod
    def setUpClass(cls):
        cls.BBLFSH_SERVER_EXISTED = ensure_bblfsh_is_running()

    @classmethod
    def tearDownClass(cls) -> None:
        if not cls.BBLFSH_SERVER_EXISTED:
            client = docker.from_env(version="auto")
            client.containers.get("bblfshd").remove(force=True)
            client.api.close()

    def _parse_fixture(self):
        return self.client.parse(self.fixtures_file)

    def setUp(self) -> None:
        self.client = BblfshClient("0.0.0.0:9432")

    def _validate_resp(self, resp):
        self.assertIsNotNone(resp)
        self.assertEqual(len(resp.errors), 0)

    def testVersion(self):
        version = self.client.version()
        self.assertTrue(hasattr(version, "version"))
        self.assertTrue(version.version)
        self.assertTrue(hasattr(version, "build"))
        self.assertTrue(version.build)

    def testNativeParse(self):
        reply = self.client.native_parse(__file__)
        assert reply.ast

    def testNonUTF8ParseError(self):
        with self.assertRaises(NonUTF8ContentException):
            self.client.parse("", "Python", b"a = '\x80abc'")

    def testUASTDefaultLanguage(self):
        self._validate_resp(self.client.parse(__file__))

    def testUASTPython(self):
        self._validate_resp(self.client.parse(__file__, language="Python"))

    def testUASTFileContents(self):
        resp = self._parse_fixture()
        self._validate_resp(resp)

    def testBrokenFilter(self):
        with self.assertRaises(AttributeError):
            xpath_filter(0, "foo")

    def testFilterInternalType(self):
        node = Node()
        node.internal_type = 'a'
        self.assertTrue(any(xpath_filter(node, "//a")))
        self.assertFalse(any(xpath_filter(node, "//b")))

    def testFilterToken(self):
        uast = self._parse_fixture().uast
        it = xpath_filter(uast, "//*[@token='else']/text()")
        first = next(it).get_str()
        self.assertEqual(first, "else")

    def testFilterRoles(self):
        uast = self._parse_fixture().uast
        it = xpath_filter(uast, "//*[@role='Identifier']")
        self.assertIsInstance(it, CompatNodeIterator)
        li = list(it)
        self.assertGreater(len(li), 0)

        it = xpath_filter(uast, "//*[@role='Friend']")
        self.assertIsInstance(it, CompatNodeIterator)
        li = list(it)
        self.assertEqual(len(li), 0)

        it = xpath_filter(uast, "//*[@role='Identifier' and not(@role='Friend')]")
        self.assertIsInstance(it, CompatNodeIterator)
        li = list(it)
        self.assertGreater(len(li), 0)

    def testFilterStartOffset(self):
        uast = self._parse_fixture().uast
        self.assertTrue(any(xpath_filter(uast, "//uast:Positions/start/uast:Position[@offset=11749]")))
        self.assertFalse(any(xpath_filter(uast, "//uast:Positions/start/uast:Position[@offset=99999]")))

    def testFilterStartLine(self):
        uast = self._parse_fixture().uast
        self.assertTrue(any(xpath_filter(uast, "//uast:Positions/start/uast:Position[@col=42]")))
        self.assertFalse(any(xpath_filter(uast, "//uast:Positions/start/uast:Position[@col=99999]")))

    def testFilterStartCol(self):
        uast = self._parse_fixture().uast
        self.assertTrue(any(xpath_filter(uast, "//uast:Positions/start/uast:Position[@col=42]")))
        self.assertFalse(any(xpath_filter(uast, "//uast:Positions/start/uast:Position[@col=99999]")))

    def testFilterEndOffset(self):
        uast = self._parse_fixture().uast
        self.assertTrue(any(xpath_filter(uast, "//uast:Positions/end/uast:Position[@offset=11757]")))
        self.assertFalse(any(xpath_filter(uast, "//uast:Positions/end/uast:Position[@offset=99999]")))

    def testFilterEndLine(self):
        uast = self._parse_fixture().uast
        self.assertTrue(any(xpath_filter(uast, "//uast:Positions/end/uast:Position[@line=321]")))
        self.assertFalse(any(xpath_filter(uast, "//uast:Positions/end/uast:Position[@line=99999]")))

    def testFilterEndCol(self):
        uast = self._parse_fixture().uast
        self.assertTrue(any(xpath_filter(uast, "//uast:Positions/end/uast:Position[@col=49]")))
        self.assertFalse(any(xpath_filter(uast, "//uast:Positions/end/uast:Position[@col=99999]")))

    def testFilterProperties(self):
        node = Node()
        node.properties['k1'] = 'v1'
        node.properties['k2'] = 'v2'
        self.assertTrue(any(xpath_filter(node, "/*[@k1='v1']")))
        self.assertTrue(any(xpath_filter(node, "/*[@k2='v2']")))
        self.assertFalse(any(xpath_filter(node, "/*[@k1='v2']")))

    def testFilterBool(self):
        uast = self._parse_fixture().uast
        self.assertTrue(filter_bool(uast, "boolean(//uast:Positions/end/uast:Position[@col=49])"))
        self.assertFalse(filter_bool(uast, "boolean(//uast:Positions/end/uast:Position[@col=9999])"))

    def testFilterNumber(self):
        res = filter_number(self._parse_fixture().uast,
                            "count(//uast:Positions/end/uast:Position[@col=49])")
        self.assertEqual(int(res), 2)

    # get_str() already tested by testFilterToken

    def testRoleIdName(self):
        self.assertEqual(role_id(role_name(1)), 1)
        self.assertEqual(role_name(role_id("IDENTIFIER")),  "IDENTIFIER")

    @staticmethod
    def _itTestTree():
        root = Node()
        root.internal_type = 'root'
        root.start_position.offset = 0

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

    def testAddToNode(self):
        n = Node()
        n.internal_node["foo"] = "bar"
        self.assertEqual(n.properties["foo"], "bar")

    def testIteratorPositionOrder(self):
        root = self._itTestTree()
        it = iterator(root, TreeOrder.POSITION_ORDER)
        self.assertIsNotNone(it)
        expanded = [node.internal_type for node in it]
        self.assertListEqual(expanded, ['root', 'son1', 'son2_1', 'son1_1',
                                        'son1_2', 'son2_2', 'son2'])

    def testFilterInsideIter(self):
        root = self._parse_fixture().uast
        it = iterator(root, TreeOrder.PRE_ORDER)
        self.assertIsNotNone(it)
        for n in it:
            xpath_filter(n, "//*[@roleIdentifier]")

    def testItersMixingIterations(self):
        root = self.client.parse(__file__).uast
        it = iterator(root, TreeOrder.PRE_ORDER)
        next(it)
        next(it)
        next(it)
        n = next(it)
        it2 = iterator(n, TreeOrder.PRE_ORDER)
        next(it2)
        val_it1 = next(it).get()
        val_it2 = next(it2).get()

        self.assertDictEqual(val_it1, val_it2)

    def testManyFilters(self):
        root = self._parse_fixture().uast
        root.properties['k1'] = 'v2'
        root.properties['k2'] = 'v1'

        before = resource.getrusage(resource.RUSAGE_SELF)
        for i in range(1000):
            xpath_filter(root, "//*[@roleIdentifier]")

        after = resource.getrusage(resource.RUSAGE_SELF)

        # Check that memory usage has not doubled after running the filter
        self.assertLess(after[2] / before[2], 2.0)

    def testManyParses(self):
        before = resource.getrusage(resource.RUSAGE_SELF)
        for _ in range(100):
            _ = self.client.parse(self.fixtures_file).uast

        after = resource.getrusage(resource.RUSAGE_SELF)
        self.assertLess(after[2] / before[2], 2.0)

    def testManyParsesAndFilters(self):
        before = resource.getrusage(resource.RUSAGE_SELF)
        for _ in range(100):
            root = self.client.parse(self.fixtures_file).uast
            xpath_filter(root, "//*[@role='Identifier']")

        after = resource.getrusage(resource.RUSAGE_SELF)
        self.assertLess(after[2] / before[2], 4.0)

    def testSupportedLanguages(self):
        res = self.client.supported_languages()
        self.assertGreater(len(res), 0)
        for l in res:
            for key in ('language', 'version', 'status', 'features'):
                self.assertTrue(hasattr(l, key))
                self.assertIsNotNone(getattr(l, key))

    def testChildren(self):
        n = Node()
        n.internal_type = 'root'
        c1 = {"@type": "child1"}
        n.properties["child1"] = c1
        self.assertDictEqual(n.children[0], c1)

        c2 = {"@type": "child2"}
        n.children.append(c2)
        self.assertDictEqual(n.children[1], c2)
        n.children.append(c2)
        self.assertDictEqual(n.children[2], c2)

        l = [{"@type": "list_child1"}, {"@type": "list_child2"}]
        n.properties["some_list"] = l
        self.assertDictEqual(n.children[3], l[0])
        self.assertDictEqual(n.children[4], l[1])

    def testChildrenFile(self):
        root = self._parse_fixture().uast
        self.assertEqual(len(root.children), 10)
        n = Node()
        n.internal_type = 'child_node'
        root.children.append(n)
        self.assertEqual(len(root.children), 11)
        last = root.children[-1]
        self.assertDictEqual(last, n.internal_node)



if __name__ == "__main__":
    unittest.main()
