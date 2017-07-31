from StringIO import StringIO
from mock import MagicMock, patch
import pytest
import shlex
import re

from bridgy.command import Sshfs
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

### Mounting / Unmounting ######################################################

# def mock_open(mock=None, data=None):
#     if mock is None:
#         mock = MagicMock(spec=file)
#
#     handle = MagicMock(spec=file)
#     handle.write.return_value = None
#     if data is None:
#         handle.__enter__.return_value = handle
#     else:
#         handle.__enter__.return_value = data
#     mock.return_value = handle
#     return mock
#
# TODO: mock ls dir with results, make more dry
#
# def test_mount():
#     data="""\
# ysfs /sys sysfs rw,nosuid,nodev,noexec,relatime 0 0
# proc /proc proc rw,nosuid,nodev,noexec,relatime 0 0
# udev /dev devtmpfs rw,nosuid,relatime,size=16359216k,nr_inodes=4089804,mode=755 0 0
# devpts /dev/pts devpts rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000 0 0
# tmpfs /run tmpfs rw,nosuid,noexec,relatime,size=3276836k,mode=755 0 0
# tmpfs /dev/shm tmpfs rw,nosuid,nodev 0 0
# tmpfs /run/lock tmpfs rw,nosuid,nodev,noexec,relatime,size=5120k 0 0
# tmpfs /sys/fs/cgroup tmpfs ro,nosuid,nodev,noexec,mode=755 0 0
# cgroup /sys/fs/cgroup/systemd cgroup rw,nosuid,nodev,noexec,relatime,xattr,release_agent=/lib/systemd/systemd-cgroups-agent,name=systemd 0 0
# pstore /sys/fs/pstore pstore rw,nosuid,nodev,noexec,relatime 0 0
# efivarfs /sys/firmware/efi/efivars efivarfs rw,nosuid,nodev,noexec,relatime 0 0
# tmpfs /run/user/1000 tmpfs rw,nosuid,nodev,relatime,size=3276836k,mode=700,uid=1000,gid=1000 0 0
# gvfsd-fuse /run/user/1000/gvfs fuse.gvfsd-fuse rw,nosuid,nodev,relatime,user_id=1000,group_id=1000 0 0
# ubuntu@devbox:/tmp /home/dummy/.bridgy/mounts/awesomebox@devbox fuse.sshfs rw,nosuid,nodev,relatime,user_id=1000,group_id=1000 0 0"""
#     mocked_result = mock_open(data=StringIO(data))
#     filename = '/etc/mtab'
#     owned_mount = '/home/dummy/.bridgy/mounts/awesomebox@devbox'
#     config = Config({}
#     with patch('__main__.open', mocked_result, create=True):
#         result = Sshfs.mounts()
#     assert owned_mount in result
#     mocked_result.assert_called_once_with(filename)


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
