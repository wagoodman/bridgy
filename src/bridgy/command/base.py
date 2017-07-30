import abc
from error import *

class BaseCommand:
    __metaclass__ = abc.ABCMeta

    def __init__(self, config, instance):
        if not hasattr(config, '__getitem__'):
            raise BadConfigError
        if not isinstance(instance, tuple):
            raise BadInstanceError

        self.config = config
        self.instance = instance

    @property
    def destination(self):
        if 'ssh' in self.config and 'user' in self.config['ssh']:
            return '{user}@{host}'.format(user=self.config['ssh']['user'],
                                          host=self.instance.address)
        else:
            return self.instance.address

    @property
    def options(self):
        bastion = ''
        options = ''

        if 'bastion' in self.config:
            if 'address' not in self.config['bastion']:
                raise MissingBastionHost

            # build a destination from possible config combinations
            if 'user' in self.config['bastion']:
                destination = '{user}@{host}'.format(user=self.config['bastion']['user'],
                                                     host=self.config['bastion']['address'])
            else:
                destination = self.config['bastion']['address']

            bastion_options = ''
            if 'options' in self.config['bastion']:
                bastion_options = self.config['bastion']['options']

            template = "-o ProxyCommand='ssh {options} -W %h:%p {destination}'"
            bastion = template.format(options=bastion_options,
                                      destination=destination)

        if 'ssh' in self.config and 'options' in self.config['ssh']:
            options = self.config['ssh']['options']

        return '{} {}'.format(bastion, options)

    @abc.abstractproperty
    def command(self): pass
