import setuptools
import glob
import os

exec(open('./bridgy/version.py').read())

setuptools.setup(
    name='bridgy',
    version=__version__,
    url='https://github.com/wagoodman/bridgy',
    license=__license__,
    author=__author__,
    author_email=__email__,
    description='Easily search your cloud inventory and integrate with ssh + tmux + sshfs',
    packages=setuptools.find_packages(),
    package_data={
        'bridgy': ['config/samples/*.yml']
    },
    include_package_data=True,
    zip_safe=False,
    install_requires=['PyYAML',
                      'requests',
                      'docopt',
                      'blessings',
                      'inquirer >= 2.2.0',
                      'fuzzywuzzy',
                      'boto3',
                      'placebo',
                      'coloredlogs',
                      'tabulate',
                      'ansible',],
    platforms='linux',
    keywords=['tmux', 'ssh', 'sshfs', 'aws', 'newrelic', 'inventory', 'cloud'],
    # latest from https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Systems Administration',
        'Topic :: System :: System Shells',
        'Topic :: Terminals',
        'Topic :: Utilities',
        ],
    entry_points={
        'console_scripts': [
            'bridgy = bridgy.__main__:main'
        ]
    },
)
