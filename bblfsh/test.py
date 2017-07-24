import unittest

import docker

from bblfsh import BblfshClient
from bblfsh.github.com.bblfsh.sdk.protocol.generated_pb2 import ParseResponse
from github.com.bblfsh.sdk.uast.generated_pb2 import Node
from bblfsh.launcher import ensure_bblfsh_is_running


from bblfsh import Node as NodeNative

class XpathTests(unittest.TestCase):
    def testXpath(self):
        NodeNative.initialize()

        root = NodeNative("compilation_unit")
        node1 = NodeNative("class")
        node2 = NodeNative("identifier")
        node2.token = "first"
        node2.add_role(1)
        node2.add_role(2)
        node2.add_role(3)
        node3 = NodeNative("block")
        node4 = NodeNative("method")
        node5 = NodeNative("identifier")
        node5.token = "second"
        node6 = NodeNative("block")
        node8 = NodeNative("loop")

        root.add_child(node1)
        node1.add_child(node2)
        node1.add_child(node3)
        node3.add_child(node4)
        node4.add_child(node5)
        node4.add_child(node6)
        node6.add_child(node8)

        results = root.find("/compilation_unit//identifier")
        self.assertEqual(results[0].token, 'first')
        self.assertEqual(results[1].token, 'second')

        # NodeNative.cleanup()


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
        with open(__file__) as fin:
            contents = fin.read()
        uast = self.client.parse("file.py", contents=contents)
        self._validate_uast(uast)

    def _validate_uast(self, uast):
        self.assertIsNotNone(uast)
        # self.assertIsInstance() does not work - must be some metaclass magic
        self.assertEqual(type(uast).DESCRIPTOR.full_name,
                         ParseResponse.DESCRIPTOR.full_name)
        self.assertEqual(len(uast.errors), 0)
        self.assertIsInstance(uast.uast, Node)


if __name__ == "__main__":
    unittest.main()
