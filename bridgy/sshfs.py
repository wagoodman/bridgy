import sys
import os
import posix
import getpass
import logging

from config import Config
import ssh

logger = logging.getLogger(__name__)

def _getSystemMounts():
    lines = [line.strip("\n").split(" ") for line in open("/etc/mtab", "r").readlines()]
    sshfsMounts = [mp for src, mp, fs, opt, p1, p2 in lines if fs == "fuse.sshfs"]
    return sshfsMounts


def getMounts():
    systemMounts = set(_getSystemMounts())
    possibleOwnedMounts = set([os.path.join(Config.mountRootDir, d) for d in os.listdir(Config.mountRootDir)])

    ownedMounts = systemMounts & possibleOwnedMounts
    return list(ownedMounts)

def isMounted(instance):
    mp = getMountpoint(instance)
    return mp in getMounts()

def getMountpoint(instance):
    return os.path.join(Config.mountRootDir, '%s@%s'%(instance.name, instance.address))

def mount(instance, remotedir):
    mountpoint = getMountpoint(instance)
    if not os.path.exists(mountpoint):
        os.mkdir(mountpoint)

    if mountpoint in getMounts():
        logger.warn("Already mounted at %s" % mountpoint)
        sys.exit(1)

    rc = os.system(ssh.SshfsCommand(instance, remotedir, mountpoint))
    if rc == 0:
        return True

    logger.error("Failed to mount instance {} at {}".format(instance, mountpoint))
    os.rmdir(mountpoint)
    return False

def umount(mountpoint=None, instance=None):
    if mountpoint == None and instance == None or mountpoint != None and instance != None:
        raise RuntimeError("Provide exactly one of either 'mountpoint' or 'instance'")

    if instance:
        mountpoint = getMountpoint(instance)

    if os.path.exists(mountpoint) and os.system("fusermount -u %s" % mountpoint) == 0:
        os.rmdir(mountpoint)
        return True
    return False
