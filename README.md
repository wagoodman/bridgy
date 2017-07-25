# bridgy

***Note: this is a work in progress, so no guarentees!***

(*TL;DR: this tool = AWS clit + ssh + tmux + sshfs*)

Just get me to my ec2 box with a lazy fuzzy search. Multiple matches? Just
ssh into all matches in a tmux session.

TODO: finish me!

```
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
```
