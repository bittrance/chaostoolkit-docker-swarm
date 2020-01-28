# -*- coding: utf-8 -*-
import docker
import json
import time

from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

def create_helper_service(client, image):
    return client.services.create(
        name='chaos-swarm-helper',
        image=image,
        mounts=['/var/run/docker.sock:/var/run/docker.sock:rw'],
        labels={'chaos-swarm-helper': 'v1'},
        endpoint_spec=docker.types.EndpointSpec(mode='dnsrr'), # ports={8080: (8080, 'tcp', 'host')}),
        mode=docker.types.ServiceMode('global')
    )

def ensure_helpers(client, image='bittrance/chaostoolkit-docker-swarm-helper:latest'):
    filters = {
      "label": "chaos-swarm-helper=v1"
    }
    installed = client.services.list(filters=filters)
    if len(installed) == 1:
        helpers = installed[0]
    elif len(installed) > 1:
        raise RuntimeError("more than one helper service")
    else:
        helpers = create_helper_service(client, image)
    deadline = time.time() + 60
    while time.time() < deadline:
        unhealthy_helpers = [helper for helper in helpers.tasks()
            if helper['DesiredState'] == 'running' and helper['Status']['State'] != 'running']
        if len(unhealthy_helpers) == 0:
            break
        time.sleep(1)
    else:
        raise RuntimeError('At least one helper not ready: %s' % helper['Status'])
    return helpers

def local_container(client, helpers):
    local_node = client.info()['Swarm']['NodeID']
    for helper in helpers.tasks():
        if helper['NodeID'] == local_node and helper['Status']['State'] == 'running':
            helper_container_id = helper['Status']['ContainerStatus']['ContainerID']
            return client.containers.get(helper_container_id)
    raise RuntimeError('There seems not to be a local helper service on (node %s)' % local_node)

def call_helpers(local_helper, payload):
    cmd = [
        "wget", "-q", "--content-on-error", "-O", "-",
        "--tries", "5", "--waitretry", "1", "--retry-connrefused",
        "--header", "Content-type: application/json",
        "--post-data", json.dumps(payload),
        "http://localhost:8080/submit"
    ]
    code, out = local_helper.exec_run(cmd)
    if code != 0:
        raise FailedActivity("wget exit code %d: %s" % (code, out))
    reply = json.loads(out)
    if reply['status'] != 'success':
        raise FailedActivity(reply['error'])

def kill_task(service, docker_client = None, configuration: Configuration = {}, secrets: Secrets = None):
    """
    Kill one task in the service, selected at random.

    Raises :exc:`chaoslib.exceptions.ActivityFailed` when the state is not as expected.
    """
    client = docker_client or docker.from_env()
    try:
        local_helper = client.containers.get(configuration['helper_container_id'])
    except KeyError:
        helpers_service = ensure_helpers(client)
        local_helper = local_container(client, helpers_service)
    call_helpers(local_helper, {
        "selector": {"services": {"name": service}},
        "targets": 1,
        "action": ["pumba", "kill", "containers"],
    })
