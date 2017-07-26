import sys
import os
import posix
import getpass
import logging

from config import Config
import ssh


# [[source, mountpoint, filesystem, options, p1, p2],...]
def getMounts():
    try:
        lines = [line.strip("\n").split(" ")
                 for line in open("/etc/mtab", "r").readlines()]
        return [mount for mount in lines if mount[2] == "fuse.sshfs"]
    except:
        print "Could not read mtab"

def getMountpoint(instance):
    return os.path.join(Config.mountRootDir, '%s@%s'%(instance.name, instance.address))

def mount(instance, remotedir):
    mountpoint = getMountpoint(instance)
    if not os.path.exists(mountpoint):
        os.mkdir(mountpoint)

    currentMounts = [mp for src, mp, fs, opts, p1, p2 in getMounts()]
    if mountpoint in currentMounts:
        print "Already mounted at %s" % mountpoint
        sys.exit(1)

    rc = os.system(ssh.SshfsCommand(instance, remotedir, mountpoint))
    if rc == 0:
        print "%s mounted as %s" % (instance, mountpoint)
    else:
        logging.getLogger().error("Failed to mount instance {} at {}".format(instance, mountpoint))
        os.rmdir(mountpoint)

def umountAll():
    for src, mp, fs, opts, p1, p2 in getMounts():
        umount(mountpoint=mp)

def umount(mountpoint=None, instance=None):
    if mountpoint == None and instance == None or mountpoint != None and instance != None:
        raise RuntimeError("Provide exactly one of either 'mountpoint' or 'instance'")

    if instance:
        mountpoint = getMountpoint(instance)

    if os.path.exists(mountpoint):
        os.system("fusermount -u %s" % mountpoint)
        os.rmdir(mountpoint)
        print 'unmounted'
    else:
        print 'unable to unmount'

def list():
    mounts = getMounts()

    if len(mounts) > 0:
        for src, mp, fs, opts, p1, p2 in mounts:
            print mp
    else:
        print "No mounts."
