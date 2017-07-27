import os
import shlex
from tmuxssh import TmuxSession

from config import Config


def run(commands, inWindows=False, layout=None):
    if layout and layout not in Config['tmux']['layout']:
        raise RuntimeError("Config does not define layout: %s" % layout)

    with TmuxSession('tmux-{}'.format(os.getpid())) as tmux:

        # open a set of terminals and run some commands
        if layout:
            for name, command in commands.items():

                # new window for all layout panes running the same cmd
                cmd = ['new-window', '-n', name]
                tmux.tmux(*cmd)

                # create each pane
                for idx, item in enumerate(Config['tmux']['layout'][layout]):

                    cmd = shlex.split(item['cmd']) + \
                        ['-t', name] + shlex.split(command)
                    if 'run' in item:
                        cmd += shlex.split(item['run'])

                    tmux.tmux(*cmd)

                    # get rid of the first pane as this is not running a cmd
                    if idx == 0:
                        tmux.kill_pane(0)

                    tmux.select_layout('tiled')

        # open one terminal
        else:
            for name, command in commands.items():
                if inWindows:
                    # new window for all layout panes running the same cmd
                    cmd = ['new-window', '-n', name] + shlex.split(command)
                    tmux.tmux(*cmd)
                else:
                    tmux.split_window(command)

                tmux.select_layout('tiled')

            # this get's rid of the local
            if not inWindows:
                tmux.kill_pane(0)

        tmux.attach()
