import docker
import pytest
import time

from chaosswarm import actions
from chaoslib.exceptions import FailedActivity
from hamcrest import *

def await_task(client, service, timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if len(service.tasks()) == 0:
            continue
        if 'ContainerStatus' not in service.tasks()[0]['Status']:
            continue
        return
    raise AssertionError('Timeout waiting for tasks on %s' % service.name)

def await_container_status(client, id, status, timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        container = client.containers.get(id)
        if container is not None and container.status == status:
            return
    raise AssertionError(
        'Timeout awaiting status %s on %s: %s' % (status, id, container.attrs)
    )

@pytest.fixture(scope='module')
def client():
    return docker.from_env()

@pytest.fixture()
def test_service(client):
    service = client.services.create(name='redis', image='redis')
    await_task(client, service)
    first_container_id = service.tasks()[0]['Status']['ContainerStatus']['ContainerID']
    await_container_status(client, first_container_id, 'running')
    yield service
    service.remove()

def test_kill_task_successful(client, test_service):
    first_container_id = test_service.tasks()[0]['Status']['ContainerStatus']['ContainerID']
    actions.kill_task('redis')
    await_container_status(client, first_container_id, 'exited')

def test_kill_task_fails():
    assert_that(calling(actions.kill_task).with_args('no-such-container'), raises(FailedActivity))
