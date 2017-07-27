from config import Config

# any ssh-based command should be built here

def options():
    bastion = ''
    template = ''

    if 'bastion' in Config:
        bastion = '-o ProxyCommand=\'ssh %s -W %%h:%%p %s@%s\' ' % (
                                        Config['bastion']['template'],
                                        Config['bastion']['user'],
                                        Config['bastion']['address'])

    if 'ssh' in Config and 'template' in Config['ssh']:
        template = Config['ssh']['template']

    return '{} {}'.format(bastion, template)

def SshCommand(instance):

    cmd = '{app} {options} {user}@{host}'
    return cmd.format(app='ssh',
                      user=Config['ssh']['user'],
                      host=instance.address,
                      options=options() )

def SshfsCommand(instance, remotedir, mountpoint):

    cmd = '{app} {options} {user}@{host}:{remotedir} {mountpoint}'
    return cmd.format(app='sshfs',
                      user=Config['ssh']['user'],
                      host=instance.address,
                      remotedir=remotedir,
                      mountpoint=mountpoint,
                      options=options() )
