from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='dockyman',
    version='0.1',
    packages=find_packages(),
    install_requires=requirements,
    include_package_data=True,
    package_data={
        '': ['model/*'],
    },
    entry_points={
        'console_scripts': [
            'dockyman=dockyman.cli:main',
        ],
    },
)
