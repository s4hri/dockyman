"""dockyman - Docker Compose orchestration across multiple machines."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("dockyman")
except PackageNotFoundError:
    __version__ = "unknown"
