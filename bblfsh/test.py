import socket
import subprocess
import time
import unittest

from bblfsh import BblfshClient
from bblfsh.github.com.bblfsh.sdk.protocol.generated_pb2 import ParseUASTResponse
from github.com.bblfsh.sdk.uast.generated_pb2 import Node


class BblfshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.check_call(
            "docker run --privileged -p 9432:9432 --name bblfsh -d "
            "bblfsh/server".split())
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = -1
        while result != 0:
            time.sleep(0.1)
            result = sock.connect_ex(("0.0.0.0", 9432))
        sock.close()

    @classmethod
    def tearDownClass(cls):
        subprocess.check_call("docker rm -f bblfsh".split())

    def setUp(self):
        self.client = BblfshClient("0.0.0.0:9432")

    def testUASTDefaultLanguage(self):
        uast = self.client.fetch_uast(__file__)
        self._validate_uast(uast)

    def testUASTPython(self):
        uast = self.client.fetch_uast(__file__, language="Python")
        self._validate_uast(uast)

    def testUASTFileContents(self):
        with open(__file__) as fin:
            contents = fin.read()
        uast = self.client.fetch_uast("file.py", contents=contents)
        self._validate_uast(uast)

    def _validate_uast(self, uast):
        self.assertIsNotNone(uast)
        # self.assertIsInstance() does not work - must be some metaclass magic
        self.assertEqual(type(uast).DESCRIPTOR.full_name,
                         ParseUASTResponse.DESCRIPTOR.full_name)
        self.assertEqual(len(uast.errors), 0)
        self.assertIsInstance(uast.uast, Node)


if __name__ == "__main__":
    unittest.main()
