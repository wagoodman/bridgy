"""bridgy
SSH + TMUX + AWS cli + SSHFS.
Fuzzy search for one or more aws hosts then ssh into all matches, organized
by tmux.

Usage:
  bridgy ssh [-teau] [-l LAYOUT] <host>...
  bridgy tunnel <host>
  bridgy mount <host>:<dir> <dir>
  bridgy unmount <host>
  bridgy update
  bridgy (-h | --help)
  bridgy --version

Sub-commands:
  tunnel        open a tunnel to the selected ec2 instance
  mount         use sshfs to mount a remote directory to an empty local directory
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

def promptTargets(targets):
    inventory = getInventory()
    instances = inventory.search(targets)

    displayInst = collections.OrderedDict()
    for instance in instances:
        display = "%-35s (%s)" % instance
        displayInst[display] = instance

    questions = [
        inquirer.Checkbox('instance',
                          message="What instances would you like to ssh into? (space to multi-select, enter to finish)",
                          choices=displayInst.keys() + ['all'],
                          # default='all'
                          ),
    ]

    answers = inquirer.prompt(questions)
    if 'all' in answers["instance"]:
        selectedHosts = instances
    else:
        selectedHosts = []
        for answer in answers["instance"]:
            selectedHosts.append(displayInst[answer])

    return selectedHosts


def ssh_handler(args):
    try:
        template = 'ssh '
        if 'bastion' in Config:
            # old way: via netcat
            template += '-o ProxyCommand=\'ssh %s -W %%h:%%p %s@%s\' ' % (
                Config['bastion']['template'], Config['bastion']['user'], Config['bastion']['address'])
            # new way: ProxyJump (not working)
            # template += '-o ProxyJump=\'%s@%s:22\' ' % (Config['bastion']['user'], Config['bastion']['address'])
        if 'ssh' in Config and 'template' in Config['ssh']:
            template += "%s " % Config['ssh']['template']
        template += ' {} '

        desiredTargets = (h for h in args['<host>'])
        targets = promptTargets(desiredTargets)

        commands = collections.OrderedDict()
        for idx, instance in enumerate(targets):
            name = '%s-%d' % (instance.name, idx)
            commands[name] = template.format("%s@%s" % (
                Config['ssh']['user'], instance.address))

        layout = None
        if args['--layout']:
            layout = args['--layout']

        tmux.run(commands, layout)
    except EnvironmentError:
        print('You need to install tmux before using this script.')


def mount_handler(args):
    raise RuntimeError("Unimplemented")


def unmount_handler(args):
    raise RuntimeError("Unimplemented")


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
        'unmount': unmount_handler,
        'update': update_handler,
        'tunnel': tunnel_handler,
    }

    for opt, handler in opts.items():
        if args[opt]:
            handler(args)


if __name__ == '__main__':
    main()
