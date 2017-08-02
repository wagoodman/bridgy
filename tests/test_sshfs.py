from StringIO import StringIO
import mock
import pytest
import shlex
import re

from bridgy.command import Sshfs
from bridgy.inventory import Instance
from bridgy.command import BadInstanceError, BadConfigError, MissingBastionHost, BadRemoteDir
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

### Mounting / Unmounting ######################################################

def test_mount_remotedir_missing():
    config = Config({})
    sshObj = Sshfs(config, instance)
    with pytest.raises(BadRemoteDir):
        sshObj.mount()

@mock.patch('os.rmdir', side_effect=lambda x: True)
@mock.patch('os.system', side_effect=lambda x: 0)
@mock.patch('os.mkdir', side_effect=lambda x: True)
@mock.patch('os.path.exists', side_effect=lambda x: False)
def test_mount_remotedir_dne(mock_exists, mock_mkdir, mock_system, mock_rmdir):
    config = Config({})
    sshObj = Sshfs(config, instance, remotedir='/tmp/test')
    sshObj.mount()
    assert mock_exists.called
    assert mock_mkdir.called
    assert mock_system.called
    assert not mock_rmdir.called

@mock.patch('os.rmdir', side_effect=lambda x: True)
@mock.patch('os.system', side_effect=lambda x: 1)
@mock.patch('os.mkdir', side_effect=lambda x: True)
@mock.patch('os.path.exists', side_effect=lambda x: False)
def test_mount_failed(mock_exists, mock_mkdir, mock_system, mock_rmdir):
    config = Config({})
    sshObj = Sshfs(config, instance, remotedir='/tmp/test')
    sshObj.mount()
    assert mock_exists.called
    assert mock_mkdir.called
    assert mock_system.called
    assert mock_rmdir.called

### Command Formatting #########################################################

def test_go_case():
    config = Config({
        'ssh': {}
    })
    remotedir = '/tmp'
    sshObj = Sshfs(config, instance, remotedir)
    mount_arg = '%s/%s@%s'%(config.mount_root_dir, instance.name, instance.address)
    assert_command_results(sshObj.command, 'sshfs address.com:/tmp %s' % mount_arg)

def test_go_case_no_options():
    config = Config({})
    remotedir = '/tmp'
    sshObj = Sshfs(config, instance, remotedir)
    mount_arg = '%s/%s@%s'%(config.mount_root_dir, instance.name, instance.address)
    assert_command_results(sshObj.command, 'sshfs address.com:/tmp %s' % mount_arg)

def test_user():
    config = Config({
        'ssh': {
            'user': 'username'
        }
    })
    remotedir = '/tmp'
    sshObj = Sshfs(config, instance, remotedir)
    mount_arg = '%s/%s@%s'%(config.mount_root_dir, instance.name, instance.address)
    assert_command_results(sshObj.command, 'sshfs username@address.com:/tmp %s' % mount_arg)

def test_options():
    config = Config({
        'ssh': {
            'user': 'username',
            'options': '-C -o ServerAliveInterval=255'
        }
    })
    remotedir = '/tmp'
    sshObj = Sshfs(config, instance, remotedir)
    mount_arg = '%s/%s@%s'%(config.mount_root_dir, instance.name, instance.address)
    assert_command_results(sshObj.command, 'sshfs -C -o ServerAliveInterval=255 username@address.com:/tmp %s' % mount_arg)

def test_no_user():
    config = Config({
        'ssh': {
            'options': '-C -o ServerAliveInterval=255'
        }
    })
    remotedir = '/tmp'
    sshObj = Sshfs(config, instance, remotedir)
    mount_arg = '%s/%s@%s'%(config.mount_root_dir, instance.name, instance.address)
    assert_command_results(sshObj.command, 'sshfs -C -o ServerAliveInterval=255 address.com:/tmp %s' % mount_arg)

def test_bastion_options():
    config = Config({
        'bastion': {
            'address': 'bastion.com',
            'options': '-C -o ServerAliveInterval=255'
        }
    })
    remotedir = '/tmp'
    sshObj = Sshfs(config, instance, remotedir)
    mount_arg = '%s/%s@%s'%(config.mount_root_dir, instance.name, instance.address)
    assert_command_results(sshObj.command, "sshfs -o ProxyCommand='ssh -C -o ServerAliveInterval=255 -W %%h:%%p bastion.com' address.com:/tmp %s" % mount_arg)

def test_bastion_user():
    config = Config({
        'bastion': {
            'address': 'bastion.com',
            'user': 'bastionuser'
        }
    })
    remotedir = '/tmp'
    sshObj = Sshfs(config, instance, remotedir)
    mount_arg = '%s/%s@%s'%(config.mount_root_dir, instance.name, instance.address)
    assert_command_results(sshObj.command, "sshfs -o ProxyCommand='ssh -W %%h:%%p bastionuser@bastion.com' address.com:/tmp %s" % mount_arg)

def test_bastion_missing_address():
    config = Config({
        'bastion': {}
    })
    remotedir = '/tmp'
    with pytest.raises(MissingBastionHost):
        sshObj = Sshfs(config, instance, remotedir)
        sshObj.command

def test_null_instance():
    config = Config({})
    remotedir = '/tmp'
    with pytest.raises(BadInstanceError):
        sshObj = Sshfs(config, None)
        sshObj.command

def test_null_config():
    remotedir = '/tmp'
    with pytest.raises(BadConfigError):
        sshObj = Sshfs(None, instance, remotedir)
        sshObj.command
