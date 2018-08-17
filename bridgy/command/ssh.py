from bridgy.error import *
from bridgy.inventory import get_bastion, get_ssh_options, get_ssh_user

class Ssh(object):

    def __init__(self, config, instance, command=''):
        if not hasattr(config, '__getitem__'):
            raise BadConfigError
        if not isinstance(instance, tuple):
            raise BadInstanceError

        self.config = config
        self.instance = instance
        self.custom_command = command

    @property
    def destination(self):
        user = get_ssh_user(self.config, self.instance)
        # self.config.dig('ssh', 'user')
        if user:
            return '{user}@{host}'.format(user=user,
                                          host=self.instance.address)
        else:
            return self.instance.address

    @property
    def options(self):
        bastion = ''
        options = ''

        bastionObj = get_bastion(self.config, self.instance)

        if bastionObj != None:
            template = "-o ProxyCommand='ssh {options} -W %h:%p {destination}'"
            bastion = template.format(options=bastionObj.options,
                                      destination=bastionObj.destination)

        options = get_ssh_options(self.config, self.instance)

        # options = self.config.dig('ssh', 'options') or ''

        return '{} {} -t'.format(bastion, options)


    @property
    def command(self):
        cmd = 'ssh {options} {destination} {command}'
        return cmd.format(destination=self.destination,
                          options=self.options,
                          command=self.custom_command)
