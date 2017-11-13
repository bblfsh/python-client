import unittest

import docker

from bblfsh import BblfshClient, filter, role_id, role_name, Node, ParseResponse
from bblfsh.launcher import ensure_bblfsh_is_running


class BblfshTests(unittest.TestCase):
    BBLFSH_SERVER_EXISTED = None

    @classmethod
    def setUpClass(cls):
        cls.BBLFSH_SERVER_EXISTED = ensure_bblfsh_is_running()

    @classmethod
    def tearDownClass(cls):
        if not cls.BBLFSH_SERVER_EXISTED:
            client = docker.from_env(version="auto")
            client.containers.get("bblfsh").remove(force=True)
            client.api.close()

    def setUp(self):
        self.client = BblfshClient("0.0.0.0:9432")

    def testVersion(self):
        version = self.client.version()
        assert(hasattr(version, "version"))
        assert(version.version)
        assert(hasattr(version, "build"))
        assert(version.build)

    def testNativeParse(self):
        reply = self.client.native_parse(__file__)
        assert(reply.ast)

    def testUASTDefaultLanguage(self):
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

    def testRoleIdName(sedlf):
        assert(role_id(role_name(1)) == 1)
        assert(role_name(role_id("IDENTIFIER")) == "IDENTIFIER")

    def _validate_resp(self, resp):
        self.assertIsNotNone(resp)
        self.assertEqual(type(resp).DESCRIPTOR.full_name,
                         ParseResponse.DESCRIPTOR.full_name)
        self.assertEqual(len(resp.errors), 0)
        # self.assertIsInstance() does not work - must be some metaclass magic
        # self.assertIsInstance(resp.uast, Node)

        # Sometimes its fully qualified, sometimes is just "Node"... ditto
        assert(resp.uast.__class__.__name__.endswith('Node'))

    def _validate_filter(self, resp):
        results = filter(resp.uast, "//Import[@roleImport and @roleDeclaration]//alias")
        self.assertEqual(next(results).token, "unittest")
        self.assertEqual(next(results).token, "docker")


if __name__ == "__main__":
    unittest.main()
