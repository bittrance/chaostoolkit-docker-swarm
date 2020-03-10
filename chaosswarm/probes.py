# -*- coding: utf-8 -*-
import docker

from chaoslib.exceptions import FailedActivity

def running_tasks(service: str, docker_client: docker.DockerClient = None):
    """
    Returns the number of running tasks for a service. In order to count as
    running a task must have desired state 'running' and its container must
    also be considered running. This means that a task whose actual state is
    'starting' will be counted as running because its container is already
    marked as running.
    """
    client = docker_client or docker.from_env()
    try:
        service_o = client.services.get(service)
    except docker.errors.NotFound:
        raise FailedActivity('No service named %s found' % service)
    actual_running = 0
    for task in service_o.tasks():
        if task['DesiredState'] == 'running' and task['Status']['State'] == 'running':
            actual_running += 1
    return actual_running
