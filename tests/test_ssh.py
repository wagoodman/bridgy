import pytest
import shlex
import re

from bridgy.command import Ssh
from bridgy.inventory import Instance
from bridgy.command import BadInstanceError, BadConfigError, MissingBastionHost
from bridgy.config import Config

instance = Instance('name', 'address.com')

whitespace_pattern = re.compile(r'\W+')

def assert_command_results(result1, result2):
    result1 = shlex.split(result1)
    result2 = shlex.split(result2)

    assert len(result1) == len(result2)

    for item1, item2 in zip(result1, result2):
        item1 = whitespace_pattern.sub(' ', item1)
        item2 = whitespace_pattern.sub(' ', item2)
        assert item1 == item2

def test_ssh_command_go_case():
    config = Config({
        'ssh': {}
    })
    sshObj = Ssh(config, instance)
    assert_command_results(sshObj.command, 'ssh address.com')

def test_ssh_command_go_case_no_options():
    config = Config({})
    sshObj = Ssh(config, instance)
    assert_command_results(sshObj.command, 'ssh address.com')

def test_ssh_command_user():
    config = Config({
        'ssh': {
            'user': 'username'
        }
    })
    sshObj = Ssh(config, instance)
    assert_command_results(sshObj.command, 'ssh username@address.com')

def test_ssh_command_options():
    config = Config({
        'ssh': {
            'user': 'username',
            'options': '-C -o ServerAliveInterval=255'
        }
    })
    sshObj = Ssh(config, instance)
    assert_command_results(sshObj.command, 'ssh -C -o ServerAliveInterval=255 username@address.com')

def test_ssh_command_no_user():
    config = Config({
        'ssh': {
            'options': '-C -o ServerAliveInterval=255'
        }
    })
    sshObj = Ssh(config, instance)
    assert_command_results(sshObj.command, 'ssh -C -o ServerAliveInterval=255 address.com')

def test_ssh_command_bastion_options():
    config = Config({
        'bastion': {
            'address': 'bastion.com',
            'options': '-C -o ServerAliveInterval=255'
        }
    })
    sshObj = Ssh(config, instance)
    assert_command_results(sshObj.command, "ssh -o ProxyCommand='ssh -C -o ServerAliveInterval=255 -W %h:%p bastion.com' address.com")

def test_ssh_command_bastion_user():
    config = Config({
        'bastion': {
            'address': 'bastion.com',
            'user': 'bastionuser'
        }
    })
    sshObj = Ssh(config, instance)
    assert_command_results(sshObj.command, "ssh -o ProxyCommand='ssh -W %h:%p bastionuser@bastion.com' address.com")

def test_ssh_command_bastion_missing_address():
    config = Config({
        'bastion': {}
    })
    with pytest.raises(MissingBastionHost):
        sshObj = Ssh(config, instance)
        sshObj.command

def test_ssh_command_null_instance():
    config = Config({})
    with pytest.raises(BadInstanceError):
        sshObj = Ssh(config, None)
        sshObj.command

def test_ssh_command_null_config():
    with pytest.raises(BadConfigError):
        sshObj = Ssh(None, instance)
        sshObj.command
