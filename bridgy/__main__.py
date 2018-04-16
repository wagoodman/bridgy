#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""bridgy
SSH + TMUX + SSHFS + CLOUD INVENTORY SEARCH.
Fuzzy search for one or more systems then ssh into all matches, organized
by tmux.

Usage:
  bridgy init
  bridgy ssh (-t | --tmux) [-adsuvw] [-l LAYOUT] <host>...
  bridgy ssh [-duv] <host>
  bridgy exec (-t | --tmux) [-adsuvw] [-l LAYOUT] <container>...
  bridgy exec [-duv] <container>
  bridgy list-inventory
  bridgy list-mounts
  bridgy mount [-duv] <host>:<remotedir>
  bridgy unmount [-dv] (-a | <host>...)
  bridgy run <task>
  bridgy update [-v]
  bridgy (-h | --help)
  bridgy --version

Sub-commands:
  init          create the ~/.bridgy/config.yml
  ssh           ssh into the selected host(s)
  exec          exec into the selected container(s) (interactive + tty)
  mount         use sshfs to mount a remote directory to an empty local directory
  unmount       unmount one or more host sshfs mounts
  list-mounts   show all sshfs mounts
  run           execute the given ansible task defined as playbook yml in ~/.bridgy/config.yml
  update        pull the latest inventory from your cloud provider

Options:
  -a        --all            Automatically use all matched hosts.
  -d        --dry-run        Show all commands that you would have run, but don't run them (implies --verbose).
  -l LAYOUT --layout LAYOUT  Use a configured lmux layout for each host.
  -s        --sync-panes     Synchronize input on all visible panes (tmux :setw synchronize-panes on).
  -t        --tmux           Open all ssh connections in a tmux session.
  -u        --update         pull the latest instance inventory from aws then run the specified command.
  -w        --windows        Use tmux windows instead of panes for each matched host.
  -h        --help           Show this screen.
  -v        --verbose        Show debug information.
  --version                  Show version.

Configuration Options are in ~/.bridgy/config.yml
"""
import sys
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')

import logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

import os
import inquirer
from inquirer.themes import Theme
import coloredlogs
import collections
from tabulate import tabulate
from docopt import docopt

from bridgy.version import __version__
from bridgy.command import Ssh, Sshfs, RunAnsiblePlaybook
from bridgy.inventory import InstanceType
import bridgy.inventory as inventory
import bridgy.config as cfg
import bridgy.tmux as tmux
import bridgy.utils as utils

logger = logging.getLogger()



class CustomTheme(Theme):

    def __init__(self):
        super(CustomTheme, self).__init__()

        selection_color = utils.term.bold_bright_cyan
        selected_color  = utils.term.bold_bright_yellow

        self.Question.mark_color = utils.term.bold_bright_cyan
        self.Question.brackets_color = utils.term.bold_bright_cyan
        self.Question.default_color = utils.term.yellow
        self.Checkbox.selection_color = selection_color
        self.Checkbox.selection_icon = '‣'# ❯
        self.Checkbox.selected_icon = '◉ ' #✔⬢◉
        self.Checkbox.selected_color = selected_color
        self.Checkbox.unselected_color = utils.term.normal
        self.Checkbox.unselected_icon = '○ ' #▢ ○ ⬡ 🞅 ⭘ 🔿 🔾
        self.List.selection_color = selection_color
        self.List.selection_cursor = '‣' # ❯
        self.List.unselected_color = utils.term.normal

THEMER = CustomTheme()

def prompt_targets(question, targets=None, instances=None, multiple=True, config=None, type=InstanceType.ALL):
    if targets == None and instances == None or targets != None and instances != None:
        raise RuntimeError("Provide exactly one of either 'targets' or 'instances'")

    if targets:
        instances = inventory.search(config, targets, type=type)

    if len(instances) == 0:
        return []

    if len(instances) == 1:
        return instances

    display_instances = collections.OrderedDict()
    # TODO: fix cap'd length... it's pretty arbitraty
    maxLen = min(max([len(instance.name) for instance in instances]), 55)
    for instance in sorted(instances):
        display = str("%-" + str(maxLen+3) + "s (%s)") % (instance.name, instance.address)
        display_instances[display] = instance

    questions = []

    if multiple:
        question = inquirer.Checkbox('instance',
                                     message="%s%s%s (space to multi-select, enter to finish)" % (utils.term.bold + utils.term.underline, question, utils.term.normal),
                                     choices=list(display_instances.keys()) + ['all'],
                                     # default='all'
                                     )
    else:
        question = inquirer.List('instance',
                                 message="%s%s%s (enter to select)" % (utils.term.bold, question, utils.term.normal),
                                 choices=list(display_instances.keys()),
                                 )
    questions.append(question)

    answers = None
    try:
        answers = inquirer.prompt(questions, theme=THEMER, raise_keyboard_interrupt=True)
    except KeyboardInterrupt:
        logger.error("Cancelled by user")
        sys.exit(1)

    if 'all' in answers["instance"]:
        selected_hosts = instances
    else:
        selected_hosts = []
        if not multiple:
            answers["instance"] = [answers["instance"]]
        for answer in answers["instance"]:
            selected_hosts.append(display_instances[answer])

    return selected_hosts


@utils.SupportedPlatforms('linux', 'windows', 'osx')
def exec_handler(args, config):
    if config.dig('inventory', 'update_at_start') or args['-u']:
        update_handler(args, config)

    if args ['--tmux'] or config.dig('ssh', 'tmux'):
        question = "What containers would you like to exec into?"
        targets = prompt_targets(question, targets=args['<container>'], config=config, type=InstanceType.CONTAINER)
    else:
        question = "What containers would you like to exec into?"
        targets = prompt_targets(question, targets=args['<container>'], config=config, type=InstanceType.CONTAINER, multiple=False)

    if len(targets) == 0:
        logger.info("No matching instances found")
        sys.exit(1)

    for instance in targets:
        if instance.container_id == None:
            logger.info("Could not find container id for instance: %s" % instance)
            sys.exit(1)

    commands = collections.OrderedDict()
    for idx, instance in enumerate(targets):
        name = '{}-{}'.format(instance.name, idx)
        commands[name] = Ssh(config, instance, command="sudo -i docker exec -ti %s bash" % instance.container_id).command

    layout = None
    if args['--layout']:
        layout = args['--layout']

    if args['--tmux'] or config.dig('ssh', 'tmux'):
        tmux.run(config, commands, args['-w'], layout, args['-d'], args['-s'])
    else:
        cmd = list(commands.values())[0]
        if args['-d']:
            logger.debug(cmd)
        else:
            os.system(cmd)

@utils.SupportedPlatforms('linux', 'windows', 'osx')
def ssh_handler(args, config):
    if config.dig('inventory', 'update_at_start') or args['-u']:
        update_handler(args, config)

    if args ['--tmux'] or config.dig('ssh', 'tmux'):
        question = "What instances would you like to ssh into?"
        targets = prompt_targets(question, targets=args['<host>'], config=config, type=InstanceType.VM)
    else:
        question = "What instance would you like to ssh into?"
        targets = prompt_targets(question, targets=args['<host>'], config=config, type=InstanceType.VM, multiple=False)

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

    if args['--tmux'] or config.dig('ssh', 'tmux'):
        tmux.run(config, commands, args['-w'], layout, args['-d'], args['-s'])
    else:
        cmd = list(commands.values())[0]
        if args['-d']:
            logger.debug(cmd)
        else:
            os.system(cmd)


@utils.SupportedPlatforms('linux', 'osx')
def mount_handler(args, config):
    Sshfs.ensure_sshfs_installed()

    if config.dig('inventory', 'update_at_start') or args['-u']:
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
    target_instances = prompt_targets(question, instances=unmounted_targets, multiple=False, config=config)

    if len(target_instances) == 0:
        logger.info("No matching instances found")
        sys.exit(1)

    for sshfsObj in sshfs_objs:
        if sshfsObj.instance in target_instances:
            if sshfsObj.mount():
                logger.info("Mounted %s at %s" % (sshfsObj.instance.name, sshfsObj.mountpoint))
            else:
                logger.error("Unable to mount %s" % sshfsObj.instance.name)


@utils.SupportedPlatforms('linux', 'osx')
def list_mounts_handler(args, config):
    Sshfs.ensure_sshfs_installed()

    if args['-d']:
        return

    for mountpoint in Sshfs.mounts(config.mount_root_dir):
        logger.info(mountpoint)


@utils.SupportedPlatforms('linux', 'osx')
def unmount_handler(args, config):
    Sshfs.ensure_sshfs_installed()

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
        target_instances = prompt_targets(question, instances=mounted_targets, multiple=False, config=config)

    if len(target_instances) == 0:
        logger.error("No matching mounts found")
        if args['-a']:
            logger.warn("Did you select targets with <space> and confirm with <enter>?")
        sys.exit(1)

    for sshfsObj in sshfs_objs:
        if sshfsObj.instance in target_instances:
            if sshfsObj.unmount():
                logger.info("Unmounted %s" % sshfsObj.instance.name)
            else:
                logger.error("Unable to unmount %s" % sshfsObj.instance.name)


@utils.SupportedPlatforms('linux', 'windows', 'osx')
def list_inventory_handler(args, config):
    instances = []
    for instance in sorted(inventory.instances(config)):
        if instance.aliases:
            instances.append( (instance.name, instance.address, '\n'.join(instance.aliases), instance.source, instance.type) )
        else:
            instances.append( (instance.name, instance.address, '--- None ---', instance.source, instance.type) )
    logger.info(tabulate(instances, headers=['Name', 'Address/Dns', 'Aliases', 'Source', 'Type']))


@utils.SupportedPlatforms('linux', 'windows', 'osx')
def update_handler(args, config):
    if args['-d']:
        return

    logger.warn("Updating inventory...")
    inventory_obj = inventory.inventory(config)
    inventory_obj.update()


@utils.SupportedPlatforms('linux', 'windows', 'osx')
def run_handler(args, config):
    # TODO: implement -d -a and -v

    task_name = args['<task>']
    task_playbook = config.dig('run', task_name)

    not_found = []
    desired_instances = []
    desired_targets = [ x.strip() for x in config.dig('run', task_name)[0]['hosts'].split(',') ]
    for desired_target in desired_targets:
        instances = inventory.search(config, [desired_target])
        if len(instances) == 0:
            not_found.append(desired_target)
            continue

        instance = inventory.Instance(desired_target, instances[0].address)
        desired_instances.append(instance)

    if len(not_found) > 0:
        logger.error("Unable to find instances: %s" % ", ".join(not_found))
        sys.exit(1)

    if not task_playbook:
        logger.error("Playbook %s not configured." % repr(task_name))
        sys.exit(1)

    task = RunAnsiblePlaybook(task_name, task_playbook[0], config, desired_instances)
    task.run()

@utils.SupportedPlatforms('linux', 'windows', 'osx')
def init_handler(args, config):
    if args['-d']:
        return
    if config.create():
        logger.info("Config created! Now configure one or more inventory sources in %s" % config.path)
    else:
        logger.error("Config already exists at %s" % config.path)

def main():
    coloredlogs.install(fmt='%(message)s')

    if os.geteuid() == 0:
        logger.error("Do not run this as root")
        sys.exit(1)

    config = cfg.Config()

    version = 'bridgy %s' % __version__
    args = docopt(__doc__, version=version)

    opts = {
        'ssh': ssh_handler,
        'exec': exec_handler,
        'mount': mount_handler,
        'list-mounts': list_mounts_handler,
        'list-inventory': list_inventory_handler,
        'unmount': unmount_handler,
        'update': update_handler,
        'run': run_handler,
    }

    if 'init' in args and args['init']:
        init_handler(args, config)
    else:
        if not config.exists():
            logger.error("Config missing, run 'bridgy init' to create one.")
            sys.exit(1)

        config.read()
        config.verify()

        if not tmux.is_installed():
            if args ['--tmux'] or config.dig('ssh', 'tmux'):
                logger.warn("Tmux not installed. Cannot support split screen.")
            args['--tmux'] = False

        if args['-v']:
            coloredlogs.install(fmt='%(message)s', level='DEBUG')

        if args['-d']:
            args['-v'] = True
            coloredlogs.install(fmt='%(message)s', level='DEBUG')
            logger.warn("Performing dry run, no actions will be taken.")

        # why doesn't docopt pick up on this?
        if args['-t']:
            args['--tmux'] = True

        if args['--version']:
            logger.info(version)
            sys.exit(0)

        for opt, handler in list(opts.items()):
            if args[opt]:
                try:
                    handler(args, config)
                except utils.UnsupportedPlatform as ex:
                    logger.error(ex.message)
                    sys.exit(1)

if __name__ == '__main__':
    main()
