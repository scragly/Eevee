from setuptools import find_packages, setup

setup(
    name='eevee',
    version='2.0.0a0',
    description='A Discord bot for Pokemon Go communities.',
    url='https://github.com/scragly/Eevee',
    author='Scragly',
    author_email='',
    license='GNU General Public License v3.0',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Topic :: Games/Entertainment :: Role-Playing',
        'Topic :: Communications :: Chat',
        'Topic :: Utilities',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='pokemon pokemongo community discord bot',

    # find_packages(exclude=['contrib', 'docs', 'tests'])
    packages=find_packages(),

    install_requires=[
        'discord.py',
        'python-dateutil>=2.6',
        'asyncpg>=0.13',
        'python-Levenshtein>=0.12',
        'fuzzywuzzy',
        'psutil',
        'aiocontextvars',
        'colorthief',
        'more_itertools'
    ],

    dependency_links=[
        'git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py-1'
    ],

    package_data={
        'eevee': ['data/*.json'],
    },

    entry_points={
        'console_scripts': [
            'eevee=eevee.launcher:main',
            'eevee-bot=eevee.__main__:main'
        ],
    },
)
