import logging
import os
import random
import string
import time

import pytest
from funcy import decorator

logger = logging.getLogger(__name__)


def wait_until(pred, timeout: float, pause: float = 0.1):
    start = time.perf_counter()
    while (time.perf_counter() - start) < timeout:
        value = pred()
        if value:
            return value
        time.sleep(pause)
    raise TimeoutError("timed out waiting")


def random_string(n: int = 6):
    return "".join(random.choices(string.ascii_lowercase, k=n))


@pytest.fixture(scope="session")
def monkeypatch_session():
    """Session-scoped monkeypatch"""
    from _pytest.monkeypatch import MonkeyPatch

    m = MonkeyPatch()
    yield m
    m.undo()


@pytest.fixture(scope="session")
def docker_client():
    """Run docker commands using the python API"""
    if os.environ.get("CI") and os.name == "nt":
        # docker-py currently fails to pull images on windows (?)
        yield None
        return

    try:
        import docker
    except ImportError:
        logger.warning("docker is not installed, run pip install docker")
        yield None
        return

    try:
        yield docker.from_env()
    except docker.errors.DockerException as exc:
        logging.exception(f"Failed to get docker client: {exc}")
        yield None


def is_pytest_session() -> bool:
    """returns true if currently running a pytest session"""
    return "PYTEST_CURRENT_TEST" in os.environ


@decorator
def skip_or_raise_on(call, *exceptions):
    """If in a pytest session, skips the current test when the given exceptions are raised"""  # noqa: E501
    try:
        return call()
    except exceptions as exc:
        if is_pytest_session():
            # just get the test name
            current_test = os.environ["PYTEST_CURRENT_TEST"].split()[0]
            pytest.skip(f"{current_test}: {exc}")
        raise
