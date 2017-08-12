try:
    import unittest.mock as mock
except ImportError:
    import mock

import collections
import subprocess
import pytest
import shlex
import os

from bridgy.tmux import TmuxSession

@mock.patch.object(subprocess, 'Popen')
def test_tmux_multiple_splits(mock_proc):
    proc_obj = lambda: None
    proc_obj.returncode = 0
    proc_obj.communicate = lambda: ('', '')
    mock_proc.return_value = proc_obj

    commands = [('somebox-0', "ssh -o ProxyCommand='ssh  -W %h:%p ubuntu@zest'  ubuntu@devbox1"),
                ('somebox-1', "ssh -o ProxyCommand='ssh  -W %h:%p ubuntu@zest'  ubuntu@devbox2")]
    commands = collections.OrderedDict(commands)

    session_name = 'tmux-15578'

    with TmuxSession(session_name=session_name, commands=commands) as tmux:
        pass

    calls = [mock.call(['tmux', 'new-session', '-ds', 'tmux-15578', '-n', 'remote-session', 'ssh', '-o', 'ProxyCommand=ssh  -W %h:%p ubuntu@zest', 'ubuntu@devbox1'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'select-layout', '-t', 'tmux-15578', 'tiled'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'split-window', '-t', 'tmux-15578', 'ssh', '-o', 'ProxyCommand=ssh  -W %h:%p ubuntu@zest', 'ubuntu@devbox2'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'select-layout', '-t', 'tmux-15578', 'tiled'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'kill-session', '-t', 'tmux-15578'], stderr=-1, stdout=-1)]

    # be sure that all calls were positivly called, and that no other calls were made
    assert len(calls) == mock_proc.call_count
    for call in calls:
        mock_proc.assert_has_calls([call])

@mock.patch.object(subprocess, 'Popen')
def test_tmux_multiple_windows(mock_proc):
    proc_obj = lambda: None
    proc_obj.returncode = 0
    proc_obj.communicate = lambda: ('', '')
    mock_proc.return_value = proc_obj

    commands = [('somebox-0', "ssh -o ProxyCommand='ssh  -W %h:%p ubuntu@zest'  ubuntu@devbox1"),
                ('somebox-1', "ssh -o ProxyCommand='ssh  -W %h:%p ubuntu@zest'  ubuntu@devbox2")]
    commands = collections.OrderedDict(commands)

    session_name = 'tmux-15578'

    with TmuxSession(session_name=session_name, commands=commands, in_windows=True) as tmux:
        pass

    calls = [mock.call(['tmux', 'new-session', '-ds', 'tmux-15578', '-n', 'somebox-0', 'ssh', '-o', 'ProxyCommand=ssh  -W %h:%p ubuntu@zest', 'ubuntu@devbox1'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'select-layout', '-t', 'tmux-15578', 'tiled'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'new-window', '-n', 'somebox-1', 'ssh', '-o', 'ProxyCommand=ssh  -W %h:%p ubuntu@zest', 'ubuntu@devbox2'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'select-layout', '-t', 'tmux-15578', 'tiled'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'kill-session', '-t', 'tmux-15578'], stderr=-1, stdout=-1)]

    # be sure that all calls were positivly called, and that no other calls were made
    assert len(calls) == mock_proc.call_count
    for call in calls:
        mock_proc.assert_has_calls([call])


@mock.patch.object(subprocess, 'Popen')
def test_tmux_layout(mock_proc):
    proc_obj = lambda: None
    proc_obj.returncode = 0
    proc_obj.communicate = lambda: ('', '')
    mock_proc.return_value = proc_obj

    commands = [('somebox-0', "ssh -o ProxyCommand='ssh  -W %h:%p ubuntu@zest'  ubuntu@devbox1"),
                ('somebox-1', "ssh -o ProxyCommand='ssh  -W %h:%p ubuntu@zest'  ubuntu@devbox2")]
    commands = collections.OrderedDict(commands)
    layout_cmds = [{'cmd': 'split-window -h', 'run': 'echo "first split" && bash'}, {'cmd': 'split-window -h', 'run': 'echo "second split" && bash'}, {'cmd': 'split-window -v', 'run': 'echo "third split" && bash'}]
    session_name = 'tmux-15578'

    with TmuxSession(session_name=session_name, commands=commands, in_windows=True, layout_cmds=layout_cmds) as tmux:
        pass

    calls = [mock.call(['tmux', 'new-session', '-ds', 'tmux-15578', '-n', 'somebox-0', 'ssh', '-o', 'ProxyCommand=ssh  -W %h:%p ubuntu@zest', 'ubuntu@devbox1'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'split-window', '-h', '-t', 'somebox-0', 'ssh', '-o', 'ProxyCommand=ssh  -W %h:%p ubuntu@zest', 'ubuntu@devbox1', 'echo', 'first split', '&&', 'bash'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'kill-pane', '-t', '0'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'select-layout', '-t', 'tmux-15578', 'tiled'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'split-window', '-h', '-t', 'somebox-0', 'ssh', '-o', 'ProxyCommand=ssh  -W %h:%p ubuntu@zest', 'ubuntu@devbox1', 'echo', 'second split', '&&', 'bash'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'select-layout', '-t', 'tmux-15578', 'tiled'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'split-window', '-v', '-t', 'somebox-0', 'ssh', '-o', 'ProxyCommand=ssh  -W %h:%p ubuntu@zest', 'ubuntu@devbox1', 'echo', 'third split', '&&', 'bash'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'select-layout', '-t', 'tmux-15578', 'tiled'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'new-window', '-n', 'somebox-1', 'ssh', '-o', 'ProxyCommand=ssh  -W %h:%p ubuntu@zest', 'ubuntu@devbox2'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'split-window', '-h', '-t', 'somebox-1', 'ssh', '-o', 'ProxyCommand=ssh  -W %h:%p ubuntu@zest', 'ubuntu@devbox2', 'echo', 'first split', '&&', 'bash'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'kill-pane', '-t', '0'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'select-layout', '-t', 'tmux-15578', 'tiled'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'split-window', '-h', '-t', 'somebox-1', 'ssh', '-o', 'ProxyCommand=ssh  -W %h:%p ubuntu@zest', 'ubuntu@devbox2', 'echo', 'second split', '&&', 'bash'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'select-layout', '-t', 'tmux-15578', 'tiled'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'split-window', '-v', '-t', 'somebox-1', 'ssh', '-o', 'ProxyCommand=ssh  -W %h:%p ubuntu@zest', 'ubuntu@devbox2', 'echo', 'third split', '&&', 'bash'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'select-layout', '-t', 'tmux-15578', 'tiled'], stderr=-1, stdout=-1),
             mock.call(['tmux', 'kill-session', '-t', 'tmux-15578'], stderr=-1, stdout=-1)]

    # be sure that all calls were positivly called, and that no other calls were made
    assert len(calls) == mock_proc.call_count
    for call in calls:
        mock_proc.assert_has_calls([call])
