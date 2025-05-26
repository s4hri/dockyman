from setuptools import setup, find_packages

version = "3.0"

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='dockyman',
    version=version,
    packages=find_packages(),
    install_requires=requirements,
    include_package_data=True,
    package_data={
        'dockyman_cli': ['model/*.yaml', 'model/base/*', 'model/local/*'],
    },
    entry_points={
        'console_scripts': [
            'dockyman=dockyman.cli:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)