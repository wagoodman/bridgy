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


def prompt_targets(question, targets=None, instances=None, multiple=True):
    if targets == None and instances == None or targets != None and instances != None:
        raise RuntimeError("Provide exactly one of either 'targets' or 'instances'")

    if targets:
        instances = inventory.search(config, targets)

    if len(instances) == 0:
        return []

    if len(instances) == 1:
        return instances

    display_instances = collections.OrderedDict()
    for instance in sorted(instances):
        display = "%-55s (%s)" % instance
        display_instances[display] = instance

    questions = []

    if multiple:
        q = inquirer.Checkbox('instance',
                              message="%s (space to multi-select, enter to finish)" % question,
                              choices=display_instances.keys() + ['all'],
                              # default='all'
                              )
    else:
        q = inquirer.List('instance',
                           message="%s (enter to select)" % question,
                           choices=display_instances.keys(),
                           )
    questions.append(q)

    answers = inquirer.prompt(questions)
    if 'all' in answers["instance"]:
        selected_hosts = instances
    else:
        selected_hosts = []
        if not multiple:
            answers["instance"] = [answers["instance"]]
        for answer in answers["instance"]:
            selected_hosts.append(display_instances[answer])

    return selected_hosts


def ssh_handler(args, config):
    if config.dig('inventory', 'update_at_start'):
        update_handler(args, config)

    question = "What instances would you like to ssh into?"
    targets = prompt_targets(question, targets=args['<host>'])

    if len(targets) == 0:
        logger.info("No matching instances found")
        sys.exit(1)

    commands = collections.OrderedDict()
    for idx, instance in enumerate(targets):
        name = '{}-{}'.format(instance.name, idx)
        commands[name] = Ssh(config, instance).command

    layout = None
    if args['--layout']:
        layout = args['--layout']

    try:
        tmux.run(config, commands, args['-w'], layout)
    except EnvironmentError:
        logger.error('Tmux not installed.')
        sys.exit(1)


def mount_handler(args, config):
    if config.dig('inventory', 'update_at_start'):
        update_handler(args, config)

    fields = args['<host>:<remotedir>'].split(':')

    if len(fields) != 2:
        logger.error("Requires exactly 2 arguments: host:remotedir")
        sys.exit(1)

    desired_target, remotedir = fields
    instances = inventory.search(config, [desired_target])
    sshfs_objs = [Sshfs(config, instance, remotedir) for instance in instances]
    unmounted_targets = [obj.instance for obj in sshfs_objs if not obj.is_mounted]

    question = "What instances would you like to have mounted?"
    target_instances = prompt_targets(question, instances=unmounted_targets, multiple=False)

    if len(target_instances) == 0:
        logger.info("No matching instances found")
        sys.exit(1)

    for sshfsObj in sshfs_objs:
        if sshfsObj.instance in target_instances:
            if sshfsObj.mount():
                logger.info("Mounted %s at %s" % (sshfsObj.instance.name, remotedir))
            else:
                logger.error("Unable to mount %s" % sshfsObj.instance.name)


def list_mounts_handler(args, config):
    for mountpoint in Sshfs.mounts(config.mount_root_dir):
        logger.info(mountpoint)


def unmount_handler(args, config):
    question = "What instances would you like to have unmounted?"

    if args['-a']:
        instances = inventory.instances(config)
        sshfs_objs = [Sshfs(config, instance) for instance in instances]
        mounted_targets = [obj.instance for obj in sshfs_objs if obj.is_mounted]
        target_instances = mounted_targets
    else:
        desired_targets = args['<host>']
        instances = inventory.search(config, desired_targets)
        sshfs_objs = [Sshfs(config, instance) for instance in instances]
        mounted_targets = [obj.instance for obj in sshfs_objs if obj.is_mounted]
        target_instances = prompt_targets(question, instances=mounted_targets, multiple=False)

    if len(target_instances) == 0:
        logger.info("No matching mounts found")
        sys.exit(1)

    for sshfsObj in sshfs_objs:
        if sshfsObj.instance in target_instances:
            if sshfsObj.unmount():
                logger.info("Unmounted %s" % sshfsObj.instance.name)
            else:
                logger.error("Unable to unmount %s" % sshfsObj.instance.name)


def update_handler(args, config):
    logger.info("Updating inventory...")
    inventory_obj = inventory.inventory(config)
    inventory_obj.update()


def main():
    global config, args
    coloredlogs.install(fmt='%(message)s')

    if os.geteuid() == 0:
        logger.error("Do not run this as root")
        sys.exit(1)

    version = 'bridgy %s' % __version__

    args = docopt(__doc__, version=version)

    if args['--version']:
        logger.info(version)
        sys.exit(0)

    config = config.Config()
    config.create()
    config.read()
    config.verify()

    opts = {
        'ssh': ssh_handler,
        'mount': mount_handler,
        'list-mounts': list_mounts_handler,
        'unmount': unmount_handler,
        'update': update_handler,
    }

    for opt, handler in opts.items():
        if args[opt]:
            handler(args, config)


if __name__ == '__main__':
    main()
