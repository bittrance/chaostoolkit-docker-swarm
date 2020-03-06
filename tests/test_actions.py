# -*- coding: utf-8 -*-
import json
import pytest

from chaosswarm.actions import kill_task, restart_service
from hamcrest import *
from unittest.mock import Mock

def extract_post_data(cmd):
    post_data_pos = cmd.index('--post-data') + 1
    return cmd[post_data_pos]

@pytest.fixture()
def mock_with_exec():
    def func(status):
        exec_run = Mock(return_value = (0, '{"status": "%s"}' % status))
        client = Mock()
        client.containers.get = Mock(return_value = Mock(exec_run = exec_run))
        payload_func = lambda: json.loads(extract_post_data(exec_run.call_args.args[0]))
        return client, payload_func
    return func

def test_kill_task(mock_with_exec):
    client, payload_func = mock_with_exec('success')
    configuration = {'helper_container_id': 'ze-container'}
    kill_task('ze-service', docker_client = client, configuration = configuration)
    assert_that(payload_func(), has_entry('selector', {'services': {'name': 'ze-service'}}))
    assert_that(payload_func(), has_entry('action', ['pumba', 'kill', 'containers']))

def test_restart_service():
    client = Mock()
    service = Mock(force_update = Mock(return_value = lambda : True))
    client.services.get = Mock(return_value = service)
    restart_service('ze-service', docker_client = client)
    service.force_update.assert_called()
