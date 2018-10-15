import os
from typing import List

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

NAME = 'pvault'
VERSION = '0.0.0'
DESCRIPTION = 'Password management system.'

REQUIRES = [
    # Pyramid
    'pyramid',

    # Pyramid related stuff
    'pyramid_jinja2',
    'pyramid_retry',
    'pyramid_tm',

    # Postgresql driver
    'psycopg2-binary',

    # SQLAlchemy related stuff
    'SQLAlchemy',
    'transaction',
    'zope.sqlalchemy',
    'alembic',

    # Redis sessions
    'redis',
    'msgpack',

    # Signing
    'itsdangerous',

    'plaster_pastedeploy',
]

DEV_REQUIRES = [
    # IPython
    'ipython',

    # Code quality
    'mypy',
    'pep8',
    'pylint',
    'autopep8',
    
    # Refactor
    'rope',

    # Pyramid utility
    'pyramid_ipython',
    'pyramid_debugtoolbar',

    # WSGI server
    'waitress',

    # Tests
    'webtest',
    'pytest',
    'pytest-cov',

    # Docs
    'sphinx',
]

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=README + '\n\n' + CHANGES,
    long_description_content_type='text/markdown',
    url='https://github.com/MarcAureleCoste/sqla-filters',

    author='Marc-Aurele Coste',
    author_email='',

    license='MIT',
    zip_safe=False,

    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    keywords='web pyramid password',

    install_requires=REQUIRES,
    extras_require={
        'dev': DEV_REQUIRES,
    },

    packages=find_packages(),
    include_package_data=True,

    entry_points={
        'paste.app_factory': [
            'main = pvault:main',
        ],
    },
)
