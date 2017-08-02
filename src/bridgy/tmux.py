import os
import shlex
import subprocess

def run(config, commands, inWindows=False, layout=None):
    layoutCmds = None
    if layout:
        if layout not in config['tmux']['layout']:
            raise RuntimeError("Config does not define layout: %s" % layout)
        else:
            layoutCmds = config['tmux']['layout'][layout]

    with TmuxSession(commands=commands, inWindows=inWindows, layoutCmds=layoutCmds) as tmux:
        tmux.attach()


# adapted from https://github.com/spappier/tmuxssh/
class TmuxSession(object):

    def __init__(self, session_name=None, commands=None, inWindows=False, layoutCmds=None):
        self._session_name = session_name or 'tmux-{}'.format(os.getpid())
        self._commands = commands
        self._in_windows = inWindows
        self._layout_cmds = layoutCmds

    def __enter__(self):

        # open a set of windows and run some commands
        if self._layout_cmds:
            for cmdIdx, (name, command) in enumerate(self._commands.items()):

                if cmdIdx == 0:
                    self.new_session(self._session_name, window_name=name, command=command)
                else:
                    # new window for all layout panes running the same cmd
                    self.new_window(name, command)

                # create each pane
                for idx, item in enumerate(self._layout_cmds):

                    cmd = shlex.split(item['cmd']) + ['-t', name] + shlex.split(command)
                    if 'run' in item:
                        cmd += shlex.split(item['run'])

                    self.tmux(*cmd)

                    # get rid of the first pane as this is not running a cmd
                    if idx == 0:
                        self.kill_pane(0)

                    self.select_layout('tiled')

        # open one window
        else:
            for cmdIdx, (name, command) in enumerate(self._commands.items()):
                if self._in_windows:
                    if cmdIdx == 0:
                        self.new_session(self._session_name, window_name=name, command=command)
                    else:
                        # new window for all layout panes running the same cmd
                        self.new_window(name, command)
                else:
                    if cmdIdx == 0:
                        self.new_session(self._session_name, window_name='remote-session', command=command)
                    else:
                        self.split_window(command)

                self.select_layout('tiled')

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.kill_session()

    def tmux(self, *args):
        return subprocess.call(['tmux'] + list(args))

    def new_session(self, session_name, window_name=None, command=None):
        cmd = ['new-session', '-ds', session_name]
        if window_name:
            cmd += ['-n', window_name]
        if command:
            cmd += shlex.split(command)

        self.tmux(*cmd)

    def new_window(self, name, command):
        if command:
            self.tmux('new-window', '-n', name, *shlex.split(command))
        else:
            self.tmux('new-window', '-n', name)

    def split_window(self, command):
        self.tmux('split-window', '-t', self._session_name, *shlex.split(command))

    def select_layout(self, layout):
        self.tmux('select-layout', '-t', self._session_name, layout)

    def attach(self):
        self.tmux('attach', '-t', self._session_name)

    def set_window_option(self, option, value):
        self.tmux('set-window-option', '-t', self._session_name, option, value)

    def kill_pane(self, n):
        self.tmux('kill-pane', '-t', str(n))

    def kill_session(self):
        self.tmux('kill-session', '-t', self._session_name)
