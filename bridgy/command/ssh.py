from command import base

class Ssh(base.BaseCommand):
    @property
    def command(self):
        cmd = 'ssh {options} {destination}'
        return cmd.format(destination=self.destination,
                          options=self.options )
