import os
from setuptools import setup, find_packages

def get_dockyman_version(env_file):
    """Reads the version from the dockyman.env file."""
    version = None
    with open(env_file, 'r') as file:
        for line in file:
            if line.startswith("DOCKYMAN_VER="):
                # Extract the version
                version = line.split('=')[1].strip()
                break
    if not version:
        raise ValueError("DOCKYMAN_VER not found in the env file")
    return version

# Path to the dockyman.env file
env_file_path = os.path.join('dockyman', 'model', 'dockyman.env')

# Get the version from the dockyman.env file
version = get_dockyman_version(env_file_path)

# Load the requirements
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='dockyman',
    version=version,
    packages=find_packages(),
    install_requires=requirements,
    include_package_data=True,
    package_data={
        'dockyman': [
            'model/compose.yaml',
            'model/dockyman.env',
            'model/nodes.yaml',
            'model/base/*',
            'model/local/*',
            'model/profiles/*',
            'model/scripts/*',
            'model/workdir/*',
        ],
    },
    entry_points={
        'console_scripts': [
            'dockyman-cli=dockyman.cli:main',
        ],
    },
)
