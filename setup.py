from setuptools import find_packages
from setuptools import setup
from glob import glob

# with open('requirements.txt') as f:
#     required_packages = f.read().splitlines()

setup(
    name='bridgy',
    version='0.0.1',
    url='https://github.com/wagoodman/bridgy',
    license='MIT',
    author='William Alex Goodman',
    description='Tool for combining aws cli + tmux + sshfs',
    #install_requires=required_packages,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
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
