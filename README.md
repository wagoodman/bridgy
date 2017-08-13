# bridgy

![Image](https://api.travis-ci.org/wagoodman/bridgy.svg?branch=master)  **WIP/beta**

**TL;DR**: bridgy = ssh + tmux + sshfs + cloud inventory search

Just get me to my ec2 box with a simple search. Multiple matches? Just
ssh into all matching instances via tmux.

![Image](demo.gif)

Have a special multi-pane tmux layout for every system you login to? Drop it in
the config (~/.bridgy/config.yml), reference it by name:
```
tmux:
  layouts:
    logger:
      - cmd: split-window -h
      - cmd: split-window -h
      - cmd: split-window -v
        run: tail -f /var/log/messages
      - cmd: set-window-option synchronize-panes on
```
then...
```
$ python bridgy ssh -l logger awesomebox
```

Want to remotely mount a dir from your ec2 instance over ssh locally?

```
$ python bridgy mount awesomebox:/appdir
[?] What instances would you like to have mounted? (enter to select):
 > o dev-myawesomeboxname                   (10.10.60.220)
   o qa-myawesomeboxname                    (10.10.63.13)

Mounted dev-myawesomeboxname:/tmp at ~/.bridgy/mounts/dev-myawesomeboxname
```

## Installing

**Linux**
```
sudo pip install bridgy

# optionally support sshing into multiple systems at once
sudo apt install tmux

# optionally support remote mounts
sudo apt install sshfs
```

**OSX**
```
sudo easy_install pip
sudo pip install bridgy --ignore-installed six

# optionally support sshing into multiple systems at once
brew install tmux

# optionally support remote mounts
brew install osxfuse
brew install sshfs
```

**Windows**
```
¯\_(ツ)_/¯
```

## Current features / Wish list

- [x] Fuzzy search against the inventory
- [x] Custom inventory backends:
  - [x] AWS
  - [ ] GCP
  - [ ] Ansible inventory
  - [x] New Relic
  - [x] CSV
- [x] Prompt for single/multi selection for matched hosts in inventory
- [x] Open multiple ssh connections via tmux (splits or tabs)
- [x] Configure custom tmux layouts (via config)
- [x] Seamless connection via bastion (via config)
- [x] Setup sshfs mount to a remote dir
- [x] Run custom command on login (via config)
- [ ] Push / pull files to and from instances (ansible? scp?)
- [ ] Ssh tunnel to hosts
- [ ] Multiple invocations of bridgy adds to the same tmux session
- [ ] Python3 support

**(Want a feature? Just [create an issue](https://github.com/wagoodman/bridgy/issues/new?labels=enhancement) describing it)**

## Usage
```
  bridgy ssh [-adsuvw] [-l LAYOUT] <host>...
  bridgy ssh [-dsuv] --no-tmux <host>
  bridgy list-inventory
  bridgy list-mounts
  bridgy mount [-duv] <host>:<remotedir>
  bridgy unmount [-dv] (-a | <host>...)
  bridgy update [-v]
  bridgy (-h | --help)
  bridgy --version

Sub-commands:
  ssh           ssh into the selected host(s)
  mount         use sshfs to mount a remote directory to an empty local directory
  unmount       unmount one or more host sshfs mounts
  list-mounts   show all sshfs mounts
  update        pull the latest inventory from your cloud provider

Options:
  -a        --all            Automatically use all matched hosts.
  -d        --dry-run        Show all commands that you would have run, but don't run them (implies --verbose).
  -l LAYOUT --layout LAYOUT  Use a configured lmux layout for each host.
  -n        --no-tmux        Ssh into a single server without tmux.
  -s        --sync-panes     Synchronize input on all visible panes (tmux :setw synchronize-panes on).
  -u        --update         pull the latest instance inventory from aws then run the specified command.
  -w        --windows        Use tmux windows instead of panes for each matched host.
  -h        --help           Show this screen.
  -v        --verbose        Show debug information.
  --version                  Show version.

Configuration Options are in ~/.bridgy/config.yml
```
