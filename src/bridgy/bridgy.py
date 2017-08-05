"""bridgy
SSH + TMUX + SSHFS + CLOUD INVENTORY SEARCH.
Fuzzy search for one or more systems then ssh into all matches, organized
by tmux.

Usage:
  bridgy ssh [-auwvd] [-l LAYOUT] <host>...
  bridgy ssh [-uvd] --no-tmux <host>
  bridgy list-inventory
  bridgy list-mounts
  bridgy mount [-vd] <host>:<remotedir>
  bridgy unmount [-vd] (-a | <host>...)
  bridgy update [-v]
  bridgy (-h | --help)
  bridgy --version

Sub-commands:
  ssh           ssh into the selected host(s)
  mount         use sshfs to mount a remote directory to an empty local directory (linux only)
  unmount       unmount one or more host sshfs mounts (linux only)
  list-mounts   show all sshfs mounts (linux only)
  update        pull the latest inventory from your cloud provider

Options:
  -a        --all            Automatically use all matched hosts.
  -d        --dry-run        Show all commands that you would have run, but don't run them (implies --verbose)
  -l LAYOUT --layout LAYOUT  Use a configured lmux layout for each host.
  -n        --no-tmux        Ssh into a single server without tmux
  -u        --update         pull the latest instance inventory from aws then run the specified command
  -w        --windows        Use tmux windows instead of panes for each matched host.
  -h        --help           Show this screen.
  -v        --verbose        Show debug information.
  --version                  Show version.

Configuration Options are in ~/.bridgy/config.yml
"""

from docopt import docopt

import sys
import os
import logging
import coloredlogs
import collections
from tabulate import tabulate

from version import __version__
from command import Ssh, Sshfs
import inventory
import config as cfg
import tmux
import utils

logger = logging.getLogger()

@utils.SupportedPlatforms('linux', 'windows', 'osx')
def ssh_handler(args, config):
    if config.dig('inventory', 'update_at_start'):
        update_handler(args, config)

    if args ['--no-tmux']:
        question = "What instance would you like to ssh into?"
        targets = utils.prompt_targets(question, targets=args['<host>'], config=config, multiple=False)
    else:
        question = "What instances would you like to ssh into?"
        targets = utils.prompt_targets(question, targets=args['<host>'], config=config)

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

    if args['--no-tmux']:
        cmd = commands.values()[0]
        if args['-d']:
            logger.debug(cmd)
        else:
            os.system(cmd)
    else:
        try:
            tmux.run(config, commands, args['-w'], layout, args['-d'])
        except EnvironmentError:
            logger.error('Tmux not installed.')
            sys.exit(1)

@utils.SupportedPlatforms('linux')
def mount_handler(args, config):
    if config.dig('inventory', 'update_at_start'):
        update_handler(args, config)

    fields = args['<host>:<remotedir>'].split(':')

    if len(fields) != 2:
        logger.error("Requires exactly 2 arguments: host:remotedir")
        sys.exit(1)

    desired_target, remotedir = fields
    instances = inventory.search(config, [desired_target])
    sshfs_objs = [Sshfs(config, instance, remotedir, dry_run=args['-d']) for instance in instances]
    unmounted_targets = [obj.instance for obj in sshfs_objs if not obj.is_mounted]

    question = "What instances would you like to have mounted?"
    target_instances = utils.prompt_targets(question, instances=unmounted_targets, multiple=False, config=config)

    if len(target_instances) == 0:
        logger.info("No matching instances found")
        sys.exit(1)

    for sshfsObj in sshfs_objs:
        if sshfsObj.instance in target_instances:
            if sshfsObj.mount():
                logger.info("Mounted %s at %s" % (sshfsObj.instance.name, sshfsObj.mountpoint))
            else:
                logger.error("Unable to mount %s" % sshfsObj.instance.name)


@utils.SupportedPlatforms('linux')
def list_mounts_handler(args, config):
    if args['-d']:
        return

    for mountpoint in Sshfs.mounts(config.mount_root_dir):
        logger.info(mountpoint)


@utils.SupportedPlatforms('linux')
def unmount_handler(args, config):
    question = "What instances would you like to have unmounted?"

    if args['-a']:
        instances = inventory.instances(config)
        sshfs_objs = [Sshfs(config, instance, dry_run=args['-d']) for instance in instances]
        mounted_targets = [obj.instance for obj in sshfs_objs if obj.is_mounted]
        target_instances = mounted_targets
    else:
        desired_targets = args['<host>']
        instances = inventory.search(config, desired_targets)
        sshfs_objs = [Sshfs(config, instance, dry_run=args['-d']) for instance in instances]
        mounted_targets = [obj.instance for obj in sshfs_objs if obj.is_mounted]
        target_instances = utils.prompt_targets(question, instances=mounted_targets, multiple=False, config=config)

    if len(target_instances) == 0:
        logger.info("No matching mounts found")
        sys.exit(1)

    for sshfsObj in sshfs_objs:
        if sshfsObj.instance in target_instances:
            if sshfsObj.unmount():
                logger.info("Unmounted %s" % sshfsObj.instance.name)
            else:
                logger.error("Unable to unmount %s" % sshfsObj.instance.name)


@utils.SupportedPlatforms('linux', 'windows', 'osx')
def list_inventory_handler(args, config):
    print tabulate( inventory.instances(config), headers=['Name', 'Address/Dns'])

@utils.SupportedPlatforms('linux', 'windows', 'osx')
def update_handler(args, config):
    if args['-d']:
        return
    logger.info("Updating inventory...")
    inventory_obj = inventory.inventory(config)
    inventory_obj.update()


def main():
    coloredlogs.install(fmt='%(message)s')

    if os.geteuid() == 0:
        logger.error("Do not run this as root")
        sys.exit(1)

    version = 'bridgy %s' % __version__

    args = docopt(__doc__, version=version)

    if args['-v']:
        coloredlogs.install(fmt='%(message)s', level='DEBUG')

    if args['-d']:
        args['-v'] = True
        coloredlogs.install(fmt='%(message)s', level='DEBUG')
        logger.warn("Performing dry run, no actions will be taken.")

    if args['--version']:
        logger.info(version)
        sys.exit(0)

    config = cfg.Config()
    config.create()
    config.read()
    config.verify()

    opts = {
        'ssh': ssh_handler,
        'mount': mount_handler,
        'list-mounts': list_mounts_handler,
        'list-inventory': list_inventory_handler,
        'unmount': unmount_handler,
        'update': update_handler,
    }

    for opt, handler in opts.items():
        if args[opt]:
            try:
                handler(args, config)
            except utils.UnsupportedPlatform as ex:
                logger.error(ex.message)
                sys.exit(1)

if __name__ == '__main__':
    main()
