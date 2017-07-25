from __future__ import print_function
from setuptools import setup

with open('requirements.txt') as f:
    required_packages = f.read().splitlines()

setup(
    name='bridgy',
    version='0.0.1',
    url='https://github.com/wagoodman/bridgy',
    license='MIT',
    author='William Alex Goodman',
    install_requires=required_packages,
    description='Tool for combining aws cli + tmux + sshfs',
    packages=['bridgy'],
    include_package_data=True,
    platforms='linux',
    classifiers = [
        'Programming Language :: Python',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    entry_points={
        'console_scripts': [
            'bridgy = bridgy.__main__:main'
        ]
    },
)
