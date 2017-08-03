import __builtin__

from StringIO import StringIO
import mock
import pytest
import shlex
import re
import os

from bridgy.command import Sshfs
from bridgy.inventory import Instance
from bridgy.command import BadInstanceError, BadConfigError, MissingBastionHost, BadRemoteDir
from bridgy.config import Config

MTAB = """\
ysfs /sys sysfs rw,nosuid,nodev,noexec,relatime 0 0
proc /proc proc rw,nosuid,nodev,noexec,relatime 0 0
udev /dev devtmpfs rw,nosuid,relatime,size=16359216k,nr_inodes=4089804,mode=755 0 0
devpts /dev/pts devpts rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000 0 0
tmpfs /run tmpfs rw,nosuid,noexec,relatime,size=3276836k,mode=755 0 0
tmpfs /dev/shm tmpfs rw,nosuid,nodev 0 0
tmpfs /run/lock tmpfs rw,nosuid,nodev,noexec,relatime,size=5120k 0 0
tmpfs /sys/fs/cgroup tmpfs ro,nosuid,nodev,noexec,mode=755 0 0
cgroup /sys/fs/cgroup/systemd cgroup rw,nosuid,nodev,noexec,relatime,xattr,release_agent=/lib/systemd/systemd-cgroups-agent,name=systemd 0 0
pstore /sys/fs/pstore pstore rw,nosuid,nodev,noexec,relatime 0 0
efivarfs /sys/firmware/efi/efivars efivarfs rw,nosuid,nodev,noexec,relatime 0 0
tmpfs /run/user/1000 tmpfs rw,nosuid,nodev,relatime,size=3276836k,mode=700,uid=1000,gid=1000 0 0
gvfsd-fuse /run/user/1000/gvfs fuse.gvfsd-fuse rw,nosuid,nodev,relatime,user_id=1000,group_id=1000 0 0
ubuntu@devbox:/tmp /home/dummy/.bridgy/mounts/awesomebox@devbox fuse.sshfs rw,nosuid,nodev,relatime,user_id=1000,group_id=1000 0 0
ubuntu@devbox:/tmp /home/dummy/someotherdir/awesomebox@devbox fuse.sshfs rw,nosuid,nodev,relatime,user_id=1000,group_id=1000 0 0"""

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

def test_sshfs_mount_remotedir_missing():
    config = Config({})
    sshObj = Sshfs(config, instance)
    with pytest.raises(BadRemoteDir):
        sshObj.mount()

@mock.patch.object(os, 'listdir')
@mock.patch('os.rmdir', side_effect=lambda x: True)
@mock.patch('os.system', side_effect=lambda x: 0)
@mock.patch('os.mkdir', side_effect=lambda x: True)
@mock.patch('os.path.exists', side_effect=lambda x: False)
def test_sshfs_mount_remotedir_dne(mock_exists, mock_mkdir, mock_system, mock_rmdir, mock_ls):
    mock_ls.return_value = ['/home/dummy/.bridgy/mounts/baddir', '/home/dummy/.bridgy/mounts/awesomebox@devbox']
    config = Config({})
    sshObj = Sshfs(config, instance, remotedir='/tmp/test')
    sshObj.mount()
    assert mock_exists.called
    assert mock_mkdir.called
    assert mock_system.called
    assert not mock_rmdir.called

@mock.patch.object(os, 'listdir')
@mock.patch('os.rmdir', side_effect=lambda x: True)
@mock.patch('os.system', side_effect=lambda x: 1)
@mock.patch('os.mkdir', side_effect=lambda x: True)
@mock.patch('os.path.exists', side_effect=lambda x: False)
def test_sshfs_mount_failed(mock_exists, mock_mkdir, mock_system, mock_rmdir, mock_ls):
    mock_ls.return_value = ['/home/dummy/.bridgy/mounts/baddir', '/home/dummy/.bridgy/mounts/awesomebox@devbox']
    config = Config({})
    sshObj = Sshfs(config, instance, remotedir='/tmp/test')
    sshObj.mount()
    assert mock_exists.called
    assert mock_mkdir.called
    assert mock_system.called
    assert mock_rmdir.called

@mock.patch.object(os, 'listdir')
@mock.patch.object(__builtin__, 'open')
def test_sshfs_mounts(mock_open, mock_ls):
    mock_open.return_value = StringIO(MTAB)
    mock_ls.return_value = ['/home/dummy/.bridgy/mounts/baddir', '/home/dummy/.bridgy/mounts/awesomebox@devbox']

    filename = '/etc/mtab'
    mounts_root_dir = '/home/dummy/.bridgy/mounts'
    owned_mount = os.path.join(mounts_root_dir, 'awesomebox@devbox')

    result = Sshfs.mounts(mounts_root_dir)
    assert len(result) == 1
    assert owned_mount in result

@mock.patch.object(os, 'rmdir')
@mock.patch.object(os, 'system')
@mock.patch.object(os.path, 'exists')
def test_sshfs_unmount_go_case(mock_exists, mock_system, mock_rmdir):
    mock_exists.return_value = True
    mock_system.return_value = 0
    mock_rmdir.return_value = True

    config = Config({})
    sshfsObj = Sshfs(config, instance, remotedir='/tmp/test')
    success = sshfsObj.unmount()

    assert mock_rmdir.call_count == 1
    assert success == True

@mock.patch.object(os, 'rmdir')
@mock.patch.object(os, 'system')
@mock.patch.object(os.path, 'exists')
def test_sshfs_unmount_mountpoint_dne(mock_exists, mock_system, mock_rmdir):
    mock_exists.return_value = False
    mock_system.return_value = 0
    mock_rmdir.return_value = True

    config = Config({})
    sshfsObj = Sshfs(config, instance, remotedir='/tmp/test')
    success = sshfsObj.unmount()

    assert mock_rmdir.call_count == 0
    assert success == False

@mock.patch.object(os, 'rmdir')
@mock.patch.object(os, 'system')
@mock.patch.object(os.path, 'exists')
def test_sshfs_unmount_fuse_failure(mock_exists, mock_system, mock_rmdir):
    mock_exists.return_value = True
    mock_system.return_value = 1
    mock_rmdir.return_value = True

    config = Config({})
    sshfsObj = Sshfs(config, instance, remotedir='/tmp/test')
    success = sshfsObj.unmount()

    assert mock_rmdir.call_count == 0
    assert success == False

### Command Formatting #########################################################

def test_sshfs_command_go_case():
    config = Config({
        'ssh': {}
    })
    remotedir = '/tmp'
    sshObj = Sshfs(config, instance, remotedir)
    mount_arg = '%s/%s@%s'%(config.mount_root_dir, instance.name, instance.address)
    assert_command_results(sshObj.command, 'sshfs address.com:/tmp %s' % mount_arg)

def test_sshfs_command_go_case_no_options():
    config = Config({})
    remotedir = '/tmp'
    sshObj = Sshfs(config, instance, remotedir)
    mount_arg = '%s/%s@%s'%(config.mount_root_dir, instance.name, instance.address)
    assert_command_results(sshObj.command, 'sshfs address.com:/tmp %s' % mount_arg)

def test_sshfs_command_user():
    config = Config({
        'ssh': {
            'user': 'username'
        }
    })
    remotedir = '/tmp'
    sshObj = Sshfs(config, instance, remotedir)
    mount_arg = '%s/%s@%s'%(config.mount_root_dir, instance.name, instance.address)
    assert_command_results(sshObj.command, 'sshfs username@address.com:/tmp %s' % mount_arg)

def test_sshfs_options():
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

def test_sshfs_command_no_user():
    config = Config({
        'ssh': {
            'options': '-C -o ServerAliveInterval=255'
        }
    })
    remotedir = '/tmp'
    sshObj = Sshfs(config, instance, remotedir)
    mount_arg = '%s/%s@%s'%(config.mount_root_dir, instance.name, instance.address)
    assert_command_results(sshObj.command, 'sshfs -C -o ServerAliveInterval=255 address.com:/tmp %s' % mount_arg)

def test_sshfs_command_bastion_options():
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

def test_sshfs_command_bastion_user():
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

def test_sshfs_command_bastion_missing_address():
    config = Config({
        'bastion': {}
    })
    remotedir = '/tmp'
    with pytest.raises(MissingBastionHost):
        sshObj = Sshfs(config, instance, remotedir)
        sshObj.command

def test_sshfs_command_null_instance():
    config = Config({})
    remotedir = '/tmp'
    with pytest.raises(BadInstanceError):
        sshObj = Sshfs(config, None)
        sshObj.command

def test_sshfs_command_null_config():
    remotedir = '/tmp'
    with pytest.raises(BadConfigError):
        sshObj = Sshfs(None, instance, remotedir)
        sshObj.command
