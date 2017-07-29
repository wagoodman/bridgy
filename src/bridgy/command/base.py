import abc

class BaseCommand:
    __metaclass__ = abc.ABCMeta

    def __init__(self, config, instance):
        self.config = config
        self.instance = instance

    @property
    def options(self):
        bastion = ''
        template = ''

        if 'bastion' in self.config:
            bastion = '-o ProxyCommand=\'ssh %s -W %%h:%%p %s@%s\' ' % (
                                            self.config['bastion']['template'],
                                            self.config['bastion']['user'],
                                            self.config['bastion']['address'])

        if 'ssh' in self.config and 'template' in self.config['ssh']:
            template = self.config['ssh']['template']

        return '{} {}'.format(bastion, template)

    @abc.abstractproperty
    def command(self): pass
