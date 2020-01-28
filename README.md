# Chaos Toolkit extension for Docker Swarm

This is a Chaos Toolkit extension package with probes and actions for Docker Swarm. Its main motivation is that in a multinode Swarm cluster, Docker provides no method to act on **containers** on remote nodes, e.g. to kill it. Thus, in order to harass a random container in a service, you would have to log in to a Swarm node and perform the command there.

This extension solves this shortcoming by launching a global-mode helper service in your swarm which mounts the Docker socket on all nodes and thus allows you to perform specific commands on any node. For more information, see [chaostoolkit-docker-swarm-helper][].

[chaostoolkit-docker-swarm-helper]: https://github.com/bittrance/chaostoolkit-docker-swarm-helper/

## Install

This package requires Python 3.5+

To be used from your experiment, this package must be installed in the Python environment where [chaostoolkit][] already lives. A fresh setup may look like this:

```bash
virtualenv chaosenv -p /usr/bin/python3
. ./chaosenv/bin/activate
pip install chaostoolkit chaostoolkit-docker-swarm
```

[chaostoolkit]: https://github.com/chaostoolkit/chaostoolkit

## Usage

```yaml
version: 1.0.0
title: Redis Docker service should survive container death
description: Docker Swarm should recreate the Redis container
steady-state-hypothesis:
  title: Redis service with running container exists
  probes:
    - name: Redis container must exist
      type: probe
      tolerance: 1
      provider:
        type: python
        module: chaosswarm.probes
        func: running_tasks
        arguments:
          service: redis
method:
  - name: Kill a Redis task
    type: action
    provider:
      type: python
      module: chaosswarm.actions
      func: kill_task
      arguments:
        service: redis
    pauses:
      after: 7
```

```bash
docker service create --name redis redis:latest
chaos run ./swarm-experiment.yaml
```
```
[2020-01-27 20:34:51 INFO] Validating the experiment's syntax
[2020-01-27 20:34:51 INFO] Experiment looks valid
[2020-01-27 20:34:51 INFO] Running experiment: Redis Docker service should survive container death
[2020-01-27 20:34:51 INFO] Steady state hypothesis: Redis service with running container exists
[2020-01-27 20:34:51 INFO] Probe: Redis container must exist
[2020-01-27 20:34:51 INFO] Steady state hypothesis is met!
[2020-01-27 20:34:51 INFO] Action: Kill a Redis task
[2020-01-27 20:34:51 INFO] Pausing after activity for 5s...
[2020-01-27 20:34:56 INFO] Steady state hypothesis: Redis service with running container exists
[2020-01-27 20:34:56 INFO] Probe: Redis container must exist
[2020-01-27 20:34:56 INFO] Steady state hypothesis is met!
[2020-01-27 20:34:56 INFO] Let's rollback...
[2020-01-27 20:34:56 INFO] No declared rollbacks, let's move on.
[2020-01-27 20:34:56 INFO] Experiment ended with status: completed
```

## Configuration

This extension assumes your environment is set up for Docker access, e.g. using Docker environment variables.

## Test

To run the tests for the project execute the following:

```bash
python3 setup.py test
```

There are integration tests which assume you have a Docker Swarm cluster available. You can promote your local dev Docker to a 1-node Swarm cluster with:
```bash
docker swarm init
```

## Contribute

If you wish to contribute more functions to this package, you are more than welcome to do so. Please, fork this project, make your changes following the usual [PEP 8][pep8] code style, sprinkling with tests and submit a PR for review.

[pep8]: https://pycodestyle.readthedocs.io/en/latest/
