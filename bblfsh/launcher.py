import logging
import socket
import time

import docker


def ensure_bblfsh_is_running():
    log = logging.getLogger("bblfsh")
    try:
        client = docker.from_env(version="auto")
    except docker.errors.DockerException as e:
        log.warning("Failed to connect to the Docker daemon and ensure "
                    "that the Babelfish server is running. %s", e)
        return False
    try:
        container = client.containers.get("bblfsh")
        if container.status != "running":
            raise docker.errors.NotFound(message="not running")
        return True
    except docker.errors.NotFound:
        container = client.containers.run(
            "bblfsh/server", name="bblfsh", detach=True, privileged=True,
            ports={9432: 9432}
        )
        log.warning(
            "Launched the Babelfish server (name bblfsh, id %s).\nStop it "
            "with: docker rm -f bblfsh", container.id)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = -1
            while result != 0:
                time.sleep(0.1)
                result = sock.connect_ex(("0.0.0.0", 9432))
        log.warning("Babelfish server is up and running.")
        return False
    finally:
        client.api.close()
