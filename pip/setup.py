from setuptools import setup, find_packages
from setuptools.command.install import install
import os
from dotenv import load_dotenv

# Load the .env file from the parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Function to read the requirements.txt file
def read_requirements():
    with open('requirements.txt') as req:
        return req.read().splitlines()

# Read the version number from the .env file
dockyman_version = os.getenv('DOCKYMAN_VER', '0.1.0')

setup(
    name="dockyman",
    version=dockyman_version,
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "dockyman = dockyman.cli:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool to manage Docker builds and runs within a Docker container.",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/yourusername/dockyman",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
