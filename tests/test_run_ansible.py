try:
    import unittest.mock as mock
except ImportError:
    import mock

import pytest

from bridgy.inventory import Instance
from bridgy.command import RunAnsibleTask
from bridgy.config import Config


def test_hostfile_gocase(mocker):

    config = Config({
        'ansible': {
            'become_user': 'root',
            'become_method': 'sudo'
        },
        'bastion': {
            'address': 'bastion.com',
            'options': '-C -o ServerAliveInterval=255'
        }
    })

    instances = [Instance(name='devenv-pubsrv', address='13.14.15.16'),
                 Instance(name='testenv-pubsrv', address='1.2.3.4'),
                 Instance(name='testenv-formsvc', address='17.18.19.20')]

    task = RunAnsibleTask('name', 'playbook', config, instances)
    contents = task._build_host_file_contents()

    assert contents.strip() == """\
devenv-pubsrv ansible_host=13.14.15.16 ansible_ssh_common_args="-o ProxyCommand='ssh -C -o ServerAliveInterval=255 -W %h:%p bastion.com' "
testenv-pubsrv ansible_host=1.2.3.4 ansible_ssh_common_args="-o ProxyCommand='ssh -C -o ServerAliveInterval=255 -W %h:%p bastion.com' "
testenv-formsvc ansible_host=17.18.19.20 ansible_ssh_common_args="-o ProxyCommand='ssh -C -o ServerAliveInterval=255 -W %h:%p bastion.com' "\
""".strip()
