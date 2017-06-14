import socket
import subprocess
import time
import unittest

from bblfsh import BblfshClient


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

    def testUAST(self):
        uast = self.client.fetch_uast(__file__, "Python")
        self.assertIsNotNone(uast)


if __name__ == "__main__":
    unittest.main()
