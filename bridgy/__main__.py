"""bridgy
SSH + TMUX + AWS cli + SSHFS.
Fuzzy search for one or more aws hosts then ssh into all matches, organized
by tmux.

Usage:
  bridgy ssh [-teauw] [-l LAYOUT] <host>...
  bridgy list-mounts
  bridgy mount <host>:<remotedir>
  bridgy unmount (-a | <host>...)
  bridgy update
  bridgy (-h | --help)
  bridgy --version

Sub-commands:
  mount         use sshfs to mount a remote directory to an empty local directory
  umount        unmount one or more host sshfs mounts
  list-mounts   show all sshfs mounts
  update        pull the latest instance inventory from aws

Options:
  -a        --all            Automatically use all matched hosts.
  -e        --exact          Use exact match for given hosts (not fuzzy match).
  -l LAYOUT --layout LAYOUT  Use a configured lmux layout for each host.
  -t        --template       Use the given ssh template for logging into the ec2 instance
  -u        --update         pull the latest instance inventory from aws then run the specified command
  -w        --windows        Use tmux windows instead of panes for each matched host.
  -h        --help           Show this screen.
  --version                  Show version.

Configuration Options are in ~/.bridgy/config.yml
"""
from docopt import docopt

import sys
import os
import collections
import logging
import inquirer
import coloredlogs

from inventory import getInventory
from config import Config
import tmux
import ssh
import sshfs

__version__ = '0.0.1'


# Just get me to my ec2 box with a fuzy search. Multiple matches? I probably
# wanted to get into all of them in a tmux session anyway.
#
# - [x] fuzzy search ec2 instances to IP
# - [x] prompt for selecting target (matched) hosts
# - [x] multi-select from matche host options
# - [x] open multiple ec2 ssh connections via tmux (splits or tabs)
# - [x] configure tmux layouts for one or more ec2 connections
# - [ ] open ssh tunnel for remote debuggers
#          concept: ssh -L 8080:web-server:80 -L 8443:web-server:443 bastion-host -N
#             then: curl https://localhost:8443/secure.txt
#           source: https://solitum.net/an-illustrated-guide-to-ssh-tunnels/
# - [x] seamless bastion hopping (via configuration)
# - [ ] push / pull files to and from instances (ansible? scp?)
# - [x] setup sshfs mount to a remote dir
#          concept: sshfs -o ProxyCommand='ssh -W %h:%p ubuntu@zest' ubuntu@devbox:/excella ./tmp/
# - [x] templating configurations for logging into systems and running commands
#          question: for immediate returns is there a way to not exit the tmux pane immediately?
#
# General todo:
# - [ ] make osx friendly
# - [x] abstract out inventory backends"
#   - [x] aws
#   - [ ] google cloud
#   - [ ] ansible inventory
#   - [x] csv
#
# Add future options:
#   bridgy scp [-r] <host>:<remotedir> <localdir>
#   bridgy tunnel <host>
#

logger = logging.getLogger()

def getInstances(targets):
    inventory = getInventory()
    return inventory.search(targets)

def promptTargets(question, targets=None, instances=None, multiple=True):
    if targets == None and instances == None or targets != None and instances != None:
        raise RuntimeError("Provide exactly one of either 'targets' or 'instances'")

    if targets:
        instances = getInstances(targets)

    if len(instances) == 0:
        return []

    if len(instances) == 1:
        return instances

    displayInst = collections.OrderedDict()
    for instance in instances:
        display = "%-35s (%s)" % instance
        displayInst[display] = instance


    questions = []

    if multiple:
        q = inquirer.Checkbox('instance',
                              message="%s (space to multi-select, enter to finish)" % question,
                              choices=displayInst.keys() + ['all'],
                              # default='all'
                              )
    else:
        q = inquirer.List('instance',
                           message="%s (enter to select)" % question,
                           choices=displayInst.keys(),
                           )
    questions.append(q)

    answers = inquirer.prompt(questions)
    if 'all' in answers["instance"]:
        selectedHosts = instances
    else:
        selectedHosts = []
        if not multiple:
            answers["instance"] = [answers["instance"]]
        for answer in answers["instance"]:
            selectedHosts.append(displayInst[answer])

    return selectedHosts


def ssh_handler(args):
    question = "What instances would you like to ssh into?"
    targets = promptTargets(question, targets=args['<host>'])

    commands = collections.OrderedDict()
    for idx, instance in enumerate(targets):
        name = '{}-{}'.format(instance.name, idx)
        commands[name] = ssh.SshCommand(instance)

    layout = None
    if args['--layout']:
        layout = args['--layout']

    try:
        tmux.run(commands, args['-w'], layout)
    except EnvironmentError:
        logger.error('Tmux not installed.')


def mount_handler(args):
    fields = args['<host>:<remotedir>'].split(':')
    if len(fields) != 2:
        raise RuntimeError("Requires exactly 2 arguments: host:remotedir")

    desiredTarget, remotedir = fields
    instances = getInstances([desiredTarget])
    mountedTargets = [instance for instance in instances if sshfs.isMounted(instance)]
    unmountedTargets = set(instances) - set(mountedTargets)
    question = "What instances would you like to have mounted?"
    targets = promptTargets(question, instances=unmountedTargets, multiple=False)

    if len(targets) > 0:
        for idx, instance in enumerate(targets):
            if sshfs.mount(instance, remotedir):
                logger.info("Mounted %s at %s" % (instance.name, remotedir))
            else:
                logger.info("Unable to mount %s" % instance.name)
    else:
        logger.info("No matching instances found")


def list_mounts_handler(args):
    for mountpoint in sshfs.getMounts():
        logger.info(mountpoint)

def unmount_handler(args):

    question = "What instances would you like to have unmounted?"

    if args['-a']:
        instances = getInventory().instances()
        mountedTargets = [instance for instance in instances if sshfs.isMounted(instance)]
        targets = mountedTargets
    else:
        desiredTargets = args['<host>']
        instances = getInstances(desiredTargets)
        mountedTargets = [instance for instance in instances if sshfs.isMounted(instance)]
        targets = promptTargets(question, instances=mountedTargets, multiple=False)

    if len(targets) > 0:
        for idx, instance in enumerate(targets):
            if sshfs.umount(instance=instance):
                logger.info("Unmounted %s" % instance.name)
            else:
                logger.info("Unable to unmount %s" % instance.name)
    else:
        logger.info("No matching mounts found")


def update_handler(args):
    raise RuntimeError("Unimplemented")
    inventory = getInventory()
    inventory.update()


def main():
    coloredlogs.install(fmt='%(message)s')

    if os.geteuid() == 0:
        logger.error("Do not run this as root")
        sys.exit(1)

    version = 'bridgy %s' % __version__

    args = docopt(__doc__, version=version)

    if args['--version']:
        logger.info(version)
        sys.exit(0)

    Config.create()
    Config.read()
    Config.verify()

    opts = {
        'ssh': ssh_handler,
        'mount': mount_handler,
        'list-mounts': list_mounts_handler,
        'unmount': unmount_handler,
        'update': update_handler,
    }

    for opt, handler in opts.items():
        if args[opt]:
            handler(args)


if __name__ == '__main__':
    main()
