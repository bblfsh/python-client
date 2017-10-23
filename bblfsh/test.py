import unittest
import importlib

import docker

from bblfsh import BblfshClient, filter
from bblfsh.launcher import ensure_bblfsh_is_running
from bblfsh.sdkversion import VERSION

# "in" is a reserved keyword in Python thus can't be used as package name, so
# we import by string
ParseResponse = importlib.import_module(
    "bblfsh.gopkg.in.bblfsh.sdk.%s.protocol.generated_pb2" % VERSION).ParseResponse
Node = importlib.import_module(
    "bblfsh.gopkg.in.bblfsh.sdk.%s.uast.generated_pb2" % VERSION).Node


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

    def testUASTDefaultLanguage(self):
        uast = self.client.parse(__file__)
        self._validate_uast(uast)

    def testUASTPython(self):
        uast = self.client.parse(__file__, language="Python")
        self._validate_uast(uast)

    def testUASTFileContents(self):
        with open(__file__, "rb") as fin:
            contents = fin.read()
        uast = self.client.parse("file.py", contents=contents)
        self._validate_uast(uast)
        self._validate_filter(uast)

    def testBrokenFilter(self):
        from sys import version_info
        if version_info[0:2] != (3, 4):
            # Skip test 3.4: cant capture SystemException from binary modules
            self.assertRaises(SystemError, filter, 0, "foo")

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

    def _validate_uast(self, uast):
        self.assertIsNotNone(uast)
        # self.assertIsInstance() does not work - must be some metaclass magic
        self.assertEqual(type(uast).DESCRIPTOR.full_name,
                         ParseResponse.DESCRIPTOR.full_name)
        self.assertEqual(len(uast.errors), 0)
        self.assertIsInstance(uast.uast, Node)

    def _validate_filter(self, uast):
        results = filter(uast.uast, "//Import[@roleImport and @roleDeclaration]//alias")
        self.assertEqual(next(results).token, "unittest")
        self.assertEqual(next(results).token, "importlib")


if __name__ == "__main__":
    unittest.main()
