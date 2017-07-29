import os
import abc
import sys
import posix
import getpass
import logging

logger = logging.getLogger(__name__)


class BaseCommand:
    __metaclass__ = abc.ABCMeta

    def __init__(self, config, instance):
        self.config = config
        self.instance = instance

    @property
    def options(self):
        bastion = ''
        template = ''

        if 'bastion' in self.config:
            bastion = '-o ProxyCommand=\'ssh %s -W %%h:%%p %s@%s\' ' % (
                                            self.config['bastion']['template'],
                                            self.config['bastion']['user'],
                                            self.config['bastion']['address'])

        if 'ssh' in self.config and 'template' in self.config['ssh']:
            template = self.config['ssh']['template']

        return '{} {}'.format(bastion, template)

    @abc.abstractproperty
    def command(self): pass


class Ssh(BaseCommand):
    @property
    def command(self):
        cmd = '{app} {options} {user}@{host}'
        return cmd.format(app='ssh',
                          user=self.config['ssh']['user'],
                          host=self.instance.address,
                          options=self.options )

class Sshfs(BaseCommand):
    def __init__(self, config, instance, remotedir=None):
        super(self.__class__, self).__init__(config, instance)
        self.remotedir = remotedir

    @property
    def command(self):
        cmd = '{app} {options} {user}@{host}:{remotedir} {mountpoint}'
        return cmd.format(app='sshfs',
                          user=self.config['ssh']['user'],
                          host=self.instance.address,
                          remotedir=self.remotedir,
                          mountpoint=self.mountpoint,
                          options=self.options )

    @classmethod
    def mounts(cls, config):
        lines = [line.strip("\n").split(" ") for line in open("/etc/mtab", "r").readlines()]
        system_mounts = set([mp for src, mp, fs, opt, p1, p2 in lines if fs == "fuse.sshfs"])
        possible_owned_mounts = set([os.path.join(config.mountRootDir, d) for d in os.listdir(config.mountRootDir)])
        owned_mounts = system_mounts & possible_owned_mounts
        return list(owned_mounts)

    @property
    def is_mounted(self):
        return self.mountpoint in Sshfs.mounts(self.config)

    @property
    def mountpoint(self):
        return os.path.join(self.config.mountRootDir, '%s@%s' % (self.instance.name, self.instance.address))

    def mount(self):
        if not self.remotedir:
            raise RuntimeError("No remotedir specified")

        if not os.path.exists(self.mountpoint):
            os.mkdir(self.mountpoint)

        if self.is_mounted:
            logger.warn("Already mounted at %s" % self.mountpoint)
            sys.exit(1)

        rc = os.system(self.command)
        if rc == 0:
            return True

        logger.error("Failed to mount instance {} at {}".format(self.instance, self.mountpoint))
        os.rmdir(mountpoint)
        return False

    def unmount(self, mountpoint=None):
        if not mountpoint:
            mountpoint = self.mountpoint

        if os.path.exists(mountpoint) and os.system("fusermount -u %s" % mountpoint) == 0:
            os.rmdir(mountpoint)
            return True
        return False
