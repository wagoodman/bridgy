# bridgy

![Image](https://api.travis-ci.org/wagoodman/bridgy.svg?branch=master)

***Note: this is a work in progress, so no guarentees!***

(*TL;DR: this tool = AWS cli + ssh + tmux + sshfs*)

Just get me to my ec2 box with a simple search. Multiple matches? Just
ssh into all matches in a tmux session.

```
$ python bridgy ssh awesomebox
[?] What instances would you like to ssh into? (space to multi-select, enter to finish):
 > x dev-myawesomeboxname
   x qa-myawesomeboxname
   o [all]
[opens tmux session split into panes... add -w for windows]

```

Have a special multi-pane layout for every system you login to? Drop it in
the config (~/.bridgy/config.yml), reference it by name:
```
tmux:
  layouts:
    logger:
      - cmd: split-window -h
      - cmd: split-window -h
      - cmd: split-window -v
        run: tail -f /var/log/messages
```
...then...
```
$ python bridgy ssh -l logger awesomebox
```

Want to mount a dir on your ec2 instance locally with the same simple search?

```
$ python bridgy sshfs awesomebox:/appdir/
[?] What instances would you like to have mounted? (enter to select):
 > o dev-myawesomeboxname
   o qa-myawesomeboxname

Mounted dev-myawesomeboxname:/tmp at ~/.bridgy/mounts/dev-myawesomeboxname
```

## Features

- [x] fuzzy search ec2 instances to IP
- [x] prompt for selecting target (matched) hosts
- [x] multi-select from matche host options
- [x] open multiple ec2 ssh connections via tmux (splits or tabs)
- [x] configure tmux layouts for one or more ec2 connections
- [ ] open ssh tunnel for remote debuggers
- [x] seamless bastion hopping (via configuration)
- [ ] push / pull files to and from instances (ansible? scp?)
- [x] setup sshfs mount to a remote dir
- [x] templating configurations for logging into systems and running commands
- [x] supported inventory backends
  - [x] aws
  - [ ] google cloud
  - [ ] ansible inventory
  - [ ] new relic
  - [x] csv

## Installing

```
sudo apt install -y sshfs tmux
pip install bridgy
```

## Usage
```
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
```
