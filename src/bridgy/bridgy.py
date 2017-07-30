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
  unmount       unmount one or more host sshfs mounts
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

# Add future options:
#   bridgy scp [-r] <host>:<remotedir> <localdir>
#   bridgy tunnel <host>
#   bridgy list-boxes         just show the inventory
#
# - [ ] open ssh tunnel for remote debuggers
#          concept: ssh -L 8080:web-server:80 -L 8443:web-server:443 bastion-host -N
#             then: curl https://localhost:8443/secure.txt
#           source: https://solitum.net/an-illustrated-guide-to-ssh-tunnels/
#
from docopt import docopt

import sys
import os
import collections
import logging
import inquirer
import coloredlogs

from command import Ssh, Sshfs
import inventory
import config
import tmux

__version__ = '0.0.1'

logger = logging.getLogger()

def promptTargets(question, targets=None, instances=None, multiple=True):
    if targets == None and instances == None or targets != None and instances != None:
        raise RuntimeError("Provide exactly one of either 'targets' or 'instances'")

    if targets:
        instances = inventory.search(CONFIG, targets)

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


def ssh_handler():
    question = "What instances would you like to ssh into?"
    targets = promptTargets(question, targets=ARGS['<host>'])

    commands = collections.OrderedDict()
    for idx, instance in enumerate(targets):
        name = '{}-{}'.format(instance.name, idx)
        commands[name] = Ssh(CONFIG, instance).command

    layout = None
    if ARGS['--layout']:
        layout = ARGS['--layout']

    try:
        tmux.run(commands, ARGS['-w'], layout)
    except EnvironmentError:
        logger.error('Tmux not installed.')
        sys.exit(1)


def mount_handler():
    fields = ARGS['<host>:<remotedir>'].split(':')

    if len(fields) != 2:
        logger.error("Requires exactly 2 arguments: host:remotedir")
        sys.exit(1)

    desiredTarget, remotedir = fields
    instances = inventory.search(CONFIG, [desiredTarget])
    sshfsObjs = [Sshfs(CONFIG, instance, remotedir) for instance in instances]
    unmountedTargets = [obj.instance for obj in sshfsObjs if not obj.is_mounted]

    question = "What instances would you like to have mounted?"
    targetInstances = promptTargets(question, instances=unmountedTargets, multiple=False)

    if len(targetInstances) == 0:
        logger.info("No matching instances found")
        sys.exit(1)

    for sshfsObj in sshfsObjs:
        if sshfsObj.instance in targetInstances:
            if sshfsObj.mount():
                logger.info("Mounted %s at %s" % (sshfsObj.instance.name, remotedir))
            else:
                logger.error("Unable to mount %s" % sshfsObj.instance.name)


def list_mounts_handler():
    for mountpoint in Sshfs.mounts(CONFIG.mount_root_dir):
        logger.info(mountpoint)

def unmount_handler():

    question = "What instances would you like to have unmounted?"

    if ARGS['-a']:
        instances = inventory.instances(CONFIG)
        sshfsObjs = [Sshfs(CONFIG, instance) for instance in instances]
        mountedTargets = [obj.instance for obj in sshfsObjs if obj.is_mounted]
        targetInstances = mountedTargets
    else:
        desiredTargets = ARGS['<host>']
        instances = inventory.search(CONFIG, desiredTargets)
        sshfsObjs = [Sshfs(CONFIG, instance) for instance in instances]
        mountedTargets = [obj.instance for obj in sshfsObjs if obj.is_mounted]
        targetInstances = promptTargets(question, instances=mountedTargets, multiple=False)

    if len(targetInstances) == 0:
        logger.info("No matching mounts found")
        sys.exit(1)

    for sshfsObj in sshfsObjs:
        if sshfsObj.instance in targetInstances:
            if sshfsObj.unmount():
                logger.info("Unmounted %s" % sshfsObj.instance.name)
            else:
                logger.error("Unable to unmount %s" % sshfsObj.instance.name)

def update_handler():
    raise RuntimeError("Unimplemented")
    inventory = inventory(CONFIG)
    inventory.update()


def main():
    global CONFIG, ARGS
    coloredlogs.install(fmt='%(message)s')

    if os.geteuid() == 0:
        logger.error("Do not run this as root")
        sys.exit(1)

    version = 'bridgy %s' % __version__

    ARGS = docopt(__doc__, version=version)

    if ARGS['--version']:
        logger.info(version)
        sys.exit(0)

    CONFIG = config.Config()
    CONFIG.create()
    CONFIG.read()
    CONFIG.verify()

    opts = {
        'ssh': ssh_handler,
        'mount': mount_handler,
        'list-mounts': list_mounts_handler,
        'unmount': unmount_handler,
        'update': update_handler,
    }

    for opt, handler in opts.items():
        if ARGS[opt]:
            handler()


if __name__ == '__main__':
    main()
