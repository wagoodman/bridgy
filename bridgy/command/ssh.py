from bridgy.command.error import *

class Ssh(object):

    def __init__(self, config, instance):
        if not hasattr(config, '__getitem__'):
            raise BadConfigError
        if not isinstance(instance, tuple):
            raise BadInstanceError

        self.config = config
        self.instance = instance

    @property
    def destination(self):
        if self.config.dig('ssh', 'user'):
            return '{user}@{host}'.format(user=self.config.dig('ssh', 'user'),
                                          host=self.instance.address)
        else:
            return self.instance.address

    @property
    def options(self):
        bastion = ''
        options = ''

        if 'bastion' in self.config:
            if not self.config.dig('bastion', 'address'):
                raise MissingBastionHost

            # build a destination from possible config combinations
            if self.config.dig('bastion', 'user'):
                destination = '{user}@{host}'.format(user=self.config.dig('bastion', 'user'),
                                                     host=self.config.dig('bastion', 'address'))
            else:
                destination = self.config.dig('bastion', 'address')

            bastion_options = self.config.dig('bastion', 'options') or ''

            template = "-o ProxyCommand='ssh {options} -W %h:%p {destination}'"
            bastion = template.format(options=bastion_options,
                                      destination=destination)

        options = self.config.dig('ssh', 'options') or ''

        return '{} {}'.format(bastion, options)


    @property
    def command(self):
        cmd = 'ssh {options} {destination}'
        return cmd.format(destination=self.destination,
                          options=self.options )
