import logging
import sys
import os
import yaml
from collections import namedtuple
from tempfile import NamedTemporaryFile

from bridgy.command.error import *
from bridgy.command import Ssh

logger = logging.getLogger()

class RunAnsiblePlaybook(object):

    def __init__(self, name, playbook, config, instances):
        self.name = name
        self.playbook = playbook
        self.config = config
        self.instances = instances
        self.become_user = config.dig('ansible', 'become_user')
        self.become_method = config.dig('ansible', 'become_method')

    def _build_host_file_contents(self):
        inventory_str = ''
        for instance in self.instances:
            ssh_obj = Ssh(self.config, instance)
            instance_str = "{} ansible_host={}".format(instance.name, instance.address)

            options = ssh_obj.options
            if len(options) > 0:
                instance_str += " ansible_ssh_common_args=\"{}\"".format(options)

            user = self.config.dig('ssh', 'user')
            if user:
                instance_str += " ansible_user=\"{}\"".format(user)

            inventory_str += instance_str + '\n'
        return inventory_str

    def run(self):
        with NamedTemporaryFile(delete=True) as playbook_file:
            playbook_str = yaml.dump([self.playbook])
            playbook_file.write(playbook_str)
            playbook_file.flush()

            with NamedTemporaryFile(delete=True) as ansible_cfg:
                ansible_str = """
[defaults]
host_key_checking = False
stdout_callback = debug
remote_tmp = $HOME/.ansible/tmp
"""
                ansible_cfg.write(ansible_str)
                ansible_cfg.flush()

                with NamedTemporaryFile(delete=True) as hosts_file:

                    inventory_str = self._build_host_file_contents()
                    hosts_file.write(inventory_str)
                    hosts_file.flush()

                    options = {  
                                 'subset': None, 
                                 'ask_pass': False, 
                                 'listtags': None, 
                                 'become_method':  self.become_method or 'sudo', 
                                 'become_user':    self.become_user or 'root', 
                                 'sudo': False, 
                                 'private_key_file': None, 
                                 'syntax': None, 
                                 'skip_tags': [], 
                                 'diff': False, 
                                 'sftp_extra_args': '', 
                                 'check': False, 
                                 'force_handlers': False, 
                                 'remote_user': None, 
                                 'become_method': u'sudo', 
                                 'vault_password_file': None, 
                                 'listtasks': None, 
                                 'output_file': None, 
                                 'ask_su_pass': False, 
                                 'new_vault_password_file': None, 
                                 'inventory': u'hosts', 
                                 'forks': 100, 
                                 'listhosts': None, 
                                 'ssh_extra_args': '', 
                                 'tags': [u'all'], 
                                 'become_ask_pass': False, 
                                 'start_at_task': None, 
                                 'flush_cache': None, 
                                 'step': None, 
                                 'become': True, 
                                 'su_user': None, 
                                 'ask_sudo_pass': False, 
                                 'extra_vars': [], 
                                 'verbosity': 3, 
                                 'su': False, 
                                 'ssh_common_args': '', 
                                 'connection': 'ssh', 
                                 'ask_vault_pass': False, 
                                 'timeout': 10, 
                                 'module_path': None, 
                                 'sudo_user': None, 
                                 'scp_extra_args': ''
                                 }

                    os.environ['ANSIBLE_CONFIG'] = ansible_cfg.name

                    from ansible_utils import Runner

                    runner = Runner(
                        playbook=playbook_file.name,
                        hosts=hosts_file.name,
                        options=options
                    )

                    stats = runner.run()

