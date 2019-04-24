"""MATRIX Labs Python MALOS library"""

import codecs
import os
from subprocess import call

from setuptools import Command, setup, find_packages

__version__ = '0.4.1'


PKG_ROOT = os.path.abspath(os.path.dirname(__file__))
with codecs.open(os.path.join(PKG_ROOT, 'README.rst'), encoding='utf-8') as file:
    LONG_DESCRIPTION = file.read()

class RunTests(Command):
    """Run all tests."""
    description = 'run tests'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """Run all tests!"""
        errno = call(['py.test', '--cov=pymalos', '--cov-report=term-missing', 'tests/'])
        raise SystemExit(errno)


setup(
    name='matrix_io-malos',
    version=__version__,
    description='MATRIX Labs MALOS libraries',
    long_description=LONG_DESCRIPTION,
    url='https://github.com/matrix-io/malos-python',
    author='MATRIX Labs Team',
    author_email='devel@matrixlabs.ai',
    license='GPLv3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    packages=find_packages(),
    install_requires=[
        'docopt==0.6.2',
        'matrix-io-proto>=0.0.32',
        'pyzmq>=18.0.1'
    ],
    extras_require={
        'test': ['coverage', 'pytest', 'pytest-cov'],
    },
    entry_points={
        'console_scripts': [
            'malosclient=matrix_io.malos.cli:main',
        ],
    },
    namespace_packages=[
        'matrix_io',
    ],
    zip_safe=False,
    cmdclass={
        'test': RunTests
    },
)
