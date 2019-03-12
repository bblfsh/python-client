import logging
import socket
import time

import docker


def after_container_start(cont: docker.models.resource.Model, log: logging.Logger) -> None:
    log.warning(
        "Launched the Babelfish server (name bblfshd, id %s).\nStop it "
        "with: docker rm -f bblfshd", cont.id)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        result = -1
        while result != 0:
            time.sleep(0.1)
            result = sock.connect_ex(("0.0.0.0", 9432))

    log.warning("Babelfish server is up and running.")
    log.info("Installing Python driver")
    cont.exec_run("bblfshctl driver install python bblfsh/python-driver:latest")


def ensure_bblfsh_is_running() -> bool:
    log = logging.getLogger("bblfsh")
    try:
        client = docker.from_env(version="auto")
        container = client.containers.get("bblfshd")
        if container.status != "running":
            try:
                container.start()
            except Exception as e:
                log.warning("Failed to start the existing bblfshd container: "
                            "%s: %s", type(e).__name__, e)
            else:
                after_container_start(container, log)
                return False
    except docker.errors.DockerException as e:
        log.warning("Failed to connect to the Docker daemon and ensure "
                    "that the Babelfish server is running. %s", e)
        return False

    except AttributeError:
        log.error("You hit https://github.com/docker/docker-py/issues/1353\n"
                  "Uninstall docker-py and docker and install *only* docker.\n"
                  "Failed to ensure that the Babelfish server is running.")
        return False

    except docker.errors.NotFound:
        container = client.containers.run(
            "bblfsh/bblfshd", name="bblfshd", detach=True, privileged=True,
            ports={9432: 9432}
        )
        after_container_start(container, log)
        return False

    finally:
        client.api.close()

    return True
