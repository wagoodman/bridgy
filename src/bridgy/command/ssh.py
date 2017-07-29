import base
import logging

logger = logging.getLogger(__name__)

class Ssh(base.BaseCommand):
    @property
    def command(self):
        cmd = '{app} {options} {user}@{host}'
        return cmd.format(app='ssh',
                          user=self.config['ssh']['user'],
                          host=self.instance.address,
                          options=self.options )
