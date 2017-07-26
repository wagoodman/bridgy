"""bridgy
SSH + TMUX + AWS cli + SSHFS.
Fuzzy search for one or more aws hosts then ssh into all matches, organized
by tmux.

Usage:
  bridgy ssh [-teau] [-l LAYOUT] <host>...
  bridgy tunnel <host>
  bridgy list-mounts
  bridgy mount <host>:<remotedir>
  bridgy unmount (-a | <host>...)
  bridgy update
  bridgy (-h | --help)
  bridgy --version

Sub-commands:
  tunnel        open a tunnel to the selected ec2 instance
  mount         use sshfs to mount a remote directory to an empty local directory
  umount        unmount one or more host sshfs mounts
  list-mounts   show all sshfs mounts
  update        pull the latest instance inventory from aws

Options:
  -e        --exact          Use exact match for given hosts (not fuzzy match).
  -a        --all            Automatically use all matched hosts.
  -l LAYOUT --layout LAYOUT  Use a configured lmux layout for each host.
  -u        --update         pull the latest instance inventory from aws then run the specified command
  -t        --template       Use the given ssh template for logging into the ec2 instance
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
# - [ ] setup sshfs mount to a remote dir
#          concept: sshfs -o ProxyCommand='ssh -W %h:%p ubuntu@zest' ubuntu@devbox:/excella ./tmp/
# - [x] templating configurations for logging into systems and running commands
#          question: for immediate returns is there a way to not exit the tmux pane immediately?
#
# General todo:
# - [x] abstract out inventory backends"
#   - [x] aws
#   - [ ] google cloud
#   - [ ] ansible inventory
#   - [ ] csv
#

def promptTargets(targets, multiple=True):
    inventory = getInventory()
    instances = inventory.search(targets)

    if len(instances) == 0:
        logging.getLogger().error("Could not find matching host(s) for %s" % repr(targets))
        sys.exit(1)

    displayInst = collections.OrderedDict()
    for instance in instances:
        display = "%-35s (%s)" % instance
        displayInst[display] = instance


    questions = []

    if multiple:
        q = inquirer.Checkbox('instance',
                              message="What instances would you like to ssh into? (space to multi-select, enter to finish)",
                              choices=displayInst.keys() + ['all'],
                              # default='all'
                              )
        questions.append(q)
    else:
        q = inquirer.List('instance',
                           message="What instance would you like to ssh into? (enter to select)",
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
    targets = promptTargets(args['<host>'])

    commands = collections.OrderedDict()
    for idx, instance in enumerate(targets):
        name = '{}-{}'.format(instance.name, idx)
        commands[name] = ssh.SshCommand(instance)

    layout = None
    if args['--layout']:
        layout = args['--layout']

    try:
        tmux.run(commands, layout)
    except EnvironmentError:
        print('Tmux not installed.')


def mount_handler(args):
    desiredTargets, remotedir = args['<host>:<remotedir>'].split(':')
    targets = promptTargets(desiredTargets, multiple=False)

    for idx, instance in enumerate(targets):
        sshfs.mount(instance,
                    remotedir)

def list_mounts_handler(args):
    sshfs.list()

def unmount_handler(args):
    if args['-a']:
        sshfs.umountAll()
    else:
        # TODO: only give options for mounts that exist
        desiredTargets = args['<host>']
        targets = promptTargets(desiredTargets)

        for idx, instance in enumerate(targets):
            sshfs.umount(instance=instance)

def update_handler(args):
    raise RuntimeError("Unimplemented")


def tunnel_handler(args):
    raise RuntimeError("Unimplemented")


def main():
    if os.geteuid() == 0:
        sys.exit("\nDo not run this as root\n")
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    version = 'bridgy %s' % __version__

    args = docopt(__doc__, version=version)

    if args['--version']:
        print(version)
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
        'tunnel': tunnel_handler,
    }

    for opt, handler in opts.items():
        if args[opt]:
            handler(args)


if __name__ == '__main__':
    main()
