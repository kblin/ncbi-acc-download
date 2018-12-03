import os
import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

long_description = read('README.md')

install_requires = [
    'requests >= 2.4.3',
]

# Can't use environment markers on old setuptools, so fix the requirements
# dynamically here. For wheels, again override the requirements in setup.cfg
# to not cause conflicts.
if sys.version_info[:3] < (2, 7, 9):
    install_requires.extend(['pyOpenSSL', 'ndg-httpsclient'])


tests_require = [
    'pytest',
    'coverage',
    'pytest-cov',
    'requests-mock',
    'pytest-mock',
]

recursive_require = [
    'biopython',
]
validate_require = [
    'biopython',
]


def read_version():
    for line in open(os.path.join('ncbi_acc_download', '__init__.py'), 'r'):
        if line.startswith('__version__'):
            return line.split('=')[-1].strip().strip("'")


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


setup(
    name='ncbi-acc-download',
    version=read_version(),
    author='Kai Blin',
    author_email='kblin@biosustain.dtu.dk',
    description='Download genome files from NCBI by accession.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=install_requires,
    tests_require=tests_require,
    cmdclass={'test': PyTest},
    entry_points={
        'console_scripts': [
            'ncbi-acc-download=ncbi_acc_download.__main__:main',
            'nad=ncbi_acc_download.__main__:main',
        ],
    },
    packages=['ncbi_acc_download'],
    url='https://github.com/kblin/ncbi-acc-download/',
    license='Apache Software License',
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    extras_require={
        'recursive': recursive_require,
        'testing': tests_require,
        'validate': validate_require,
    },
)
