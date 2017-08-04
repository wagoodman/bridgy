from setuptools import find_packages
from setuptools import setup
from glob import glob

execfile('src/bridgy/version.py')

setup(
    name='bridgy',
    version=__version__,
    url='https://github.com/wagoodman/bridgy',
    license=__license__,
    author=__author__,
    author_email=__email__,
    description='Tool for combining aws cli + tmux + sshfs',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    install_requires=['PyYAML',
                      'requests',
                      'docopt',
                      'inquirer',
                      'fuzzywuzzy',
                      'boto3',
                      'placebo',
                      'python-Levenshtein',
                      'coloredlogs'],
    platforms='linux',
    keywords=['tmux', 'ssh', 'sshfs', 'aws'],
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
        'Programming Language :: Python :: 2.7',
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
            'bridgy = bridgy.bridgy:main'
        ]
    },
)
