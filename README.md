# bridgy

![Image](https://api.travis-ci.org/wagoodman/bridgy.svg?branch=master)  [![PyPI version](https://badge.fury.io/py/bridgy.svg)](https://badge.fury.io/py/bridgy)
(***WIP/beta***)

**TL;DR**: bridgy = ssh + tmux + sshfs + cloud inventory search

Just get me to my ec2 box with a simple search. Multiple matches? Just
ssh into all matching instances via tmux.

![Image](demo.gif)

**Features:**
- [x] Custom inventory sources:
  - [x] AWS (supports matching by tag, dns, or instance-id)
  - [ ] GCP
  - [x] New Relic
  - [x] CSV
  - [ ] Ansible inventory
- [x] Search against multiple inventory sources simultaneously
- [x] Connect to inventory sources via a bastion/jumpbox
- [x] Fuzzy search against the inventory
- [x] Prompt for single/multi selection for matched hosts in inventory
- [x] Open multiple ssh connections via tmux (splits or tabs)
- [x] Configure custom tmux layouts (via config)
- [x] Seamless connection via bastion (via config)
- [x] Setup sshfs mount to a remote dir
- [x] Run custom command on login (via config)
- [x] Run arbitrary ansible playbooks
- [x] Push / pull files (via ansible fetch/copy task)
- [ ] Ssh tunnel to hosts
- [ ] ECS support (exec to container, search tasks, etc)
- [x] Python3 support :)

**(Want a feature? Just [create an issue](https://github.com/wagoodman/bridgy/issues/new?labels=enhancement) describing it)**

## Installing

**Linux**
```
pip install --user bridgy

# optionally support sshing into multiple systems at once
sudo apt install tmux

# optionally support remote mounts
sudo apt install sshfs
```

**OSX**
```
sudo easy_install pip
pip install --user bridgy --ignore-installed six

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

## Current features

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
$ bridgy ssh -l logger awesomebox
```

Want to remotely mount a dir from your ec2 instance over ssh locally?

```
$ bridgy mount awesomebox:/appdir
[?] What instances would you like to have mounted? (enter to select):
 > o dev-myawesomeboxname                   (10.10.60.220)
   o qa-myawesomeboxname                    (10.10.63.13)

Mounted dev-myawesomeboxname:/tmp at ~/.bridgy/mounts/dev-myawesomeboxname
```

Need to connect to your boxes via a jumpbox? Drop in your bastion connection information in the yaml config:
```
bastion:
  user: some-username
  address: some-ip-or-host
  # optional ssh arguments
  options: -C -o ServerAliveInterval=255 -o FingerprintHash=sha256 -o TCPKeepAlive=yes -o ForwardAgent=yes -p 22222
```

Want to perform arbitrary tasks? Drop in an ansible playbook in config (~/.bridgy/config.yml), reference it by name:
```
run:
  grab-files:
    - hosts: app-srv-13, dev-srv
      gather_facts: no
      tasks:
        - name: 'Get secrets.yml'
          fetch:
            src: /appdir/config/secrets.yml
            dest: /tmp/prefix-{{ inventory_hostname }}.secrets.yml
            fail_on_missing: yes
            flat: yes
        - name: 'Get production.rb'
          fetch:
            src: /appdir/config/environments/production.rb
            dest: /tmp/prefix-{{ inventory_hostname }}.production.rb
            fail_on_missing: yes
            flat: yes
        - name: 'Get database.yml'
          fetch:
            src: /appdir/config/database.yml
            dest: /tmp/prefix-{{ inventory_hostname }}.database.yml
            fail_on_missing: yes
            flat: yes
```
then...
```
$ bridgy run grab-files

PLAY [app-srv-13, dev-srv] *****************************************************

TASK [Get secrets.yml] ********************************************************
ok: [dev-srv]
ok: [app-srv-13]

TASK [Get production.rb] ******************************************************
ok: [dev-srv]
ok: [app-srv-13]

TASK [Get database.yml] *******************************************************
ok: [dev-srv]
ok: [app-srv-13]

$ ls -1 /tmp | grep prefix
prefix-dev-srv.database.yml
prefix-dev-srv.production.rb
prefix-dev-srv.secrets.yml
prefix-app-srv-13.database.yml
prefix-app-srv-13.production.rb
prefix-app-srv-13.secrets.yml

```

## Usage
```
  bridgy ssh [-adsuvw] [-l LAYOUT] <host>...
  bridgy ssh [-dsuv] --no-tmux <host>
  bridgy list-inventory
  bridgy list-mounts
  bridgy mount [-duv] <host>:<remotedir>
  bridgy unmount [-dv] (-a | <host>...)
  bridgy run <task>
  bridgy update [-v]
  bridgy (-h | --help)
  bridgy --version

Sub-commands:
  ssh           ssh into the selected host(s)
  mount         use sshfs to mount a remote directory to an empty local directory
  unmount       unmount one or more host sshfs mounts
  list-mounts   show all sshfs mounts
  run           execute the given ansible task defined as playbook yml in ~/.bridgy/config.yml
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
