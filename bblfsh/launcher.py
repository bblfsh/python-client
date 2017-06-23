import socket
import sys
import time

import docker


def ensure_bblfsh_is_running():
    client = docker.from_env(version="auto")
    try:
        container = client.containers.get("bblfsh")
        if container.status != "running":
            raise docker.errors.NotFound()
        return True
    except docker.errors.NotFound:
        container = client.containers.run(
            "bblfsh/server", name="bblfsh", detach=True, privileged=True,
            ports={9432: 9432}
        )
        sys.stderr.write(
            "Launched the Babelfish server (name bblfsh, id %s).\nStop it "
            "with: docker rm -f bblfsh\n" % container.id)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = -1
        while result != 0:
            time.sleep(0.1)
            result = sock.connect_ex(("0.0.0.0", 9432))
        sock.close()
        sys.stderr.write("Babelfish server is up and running.\n")
        return False
    finally:
        client.api.close()
