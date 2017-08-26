import logging
import sys
import os
from collections import namedtuple
from tempfile import NamedTemporaryFile

from bridgy.command.error import *
from bridgy.command import Ssh

logger = logging.getLogger()


Options = namedtuple('Options', ['connection', 'module_path', 'forks', 'become',
                                 'become_method', 'become_user', 'check', 'verbosity'] )

class RunAnsibleTask(object):

    def __init__(self, name, playbook, config, instances):
        self.name = name
        self.playbook = playbook
        self.config = config
        self.instances = instances
        self.become_user = config.dig('ansible', 'become_user')
        self.become_method = config.dig('ansible', 'become_method')

    def _task(self, hosts_file):
        # really?
        os.environ['ANSIBLE_NOCOWS'] = '1'

        try:
            from ansible.parsing.dataloader import DataLoader
            from ansible.vars import VariableManager
            from ansible.inventory import Inventory
            from ansible.playbook.play import Play
            from ansible.executor.task_queue_manager import TaskQueueManager
        except ImportError:
            logger.error("Ansible is not installed")
            sys.exit(1)

        variable_manager = VariableManager()
        loader = DataLoader()

        options = Options(connection='paramiko', module_path='', forks=100, become=True,
                          become_method=self.become_method, become_user=self.become_user, check=False, verbosity=5)

        passwords = dict(vault_pass='secret')

        inventory = Inventory(loader=loader,
                              variable_manager=variable_manager,
                              host_list=hosts_file.name)

        variable_manager.set_inventory(inventory)

        play = Play().load(self.playbook,
                           variable_manager=variable_manager,
                           loader=loader)

        tqm = TaskQueueManager(inventory=inventory,
                               variable_manager=variable_manager,
                               loader=loader,
                               options=options,
                               passwords=passwords,
                               stdout_callback="default")

        return play, tqm

    def _build_host_file_contents(self):
        inventory_str = ''
        for instance in self.instances:
            ssh_obj = Ssh(self.config, instance)
            instance_str = "{} ansible_host={}".format(instance.name, instance.address)

            options = ssh_obj.options
            if len(options) > 0:
                instance_str += " ssh_args=\"{}\"".format(options)

            user = self.config.dig('ssh', 'user')
            if user:
                instance_str += " ansible_user=\"{}\"".format(user)

            inventory_str += instance_str + '\n'
        return inventory_str

    def run(self):

        with NamedTemporaryFile(delete=True) as hosts_file:
            inventory_str = self._build_host_file_contents()
            hosts_file.write(inventory_str)
            hosts_file.flush()

            task_queue = None
            try:
                play, task_queue = self._task(hosts_file)
                result = task_queue.run(play)
            finally:
                if task_queue is not None:
                    task_queue.cleanup()
