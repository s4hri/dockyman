import os
import getpass
from colorama import init as colorama_init

# Initialize colorama
colorama_init(autoreset=True, strip=False, convert=False)

LOCAL_UID = int(os.getenv('LOCAL_UID', os.getuid()))
LOCAL_GID = int(os.getenv('LOCAL_GID', os.getgid()))
LOCALHOST_USER = str(os.getenv('LOCALHOST_USER', getpass.getuser()))
DISPLAY = str(os.getenv('DISPLAY'))

PREFIX_TARGET = str(os.getenv('PREFIX_TARGET', ''))
LOCAL_IMAGE_GROUPS = os.getenv('LOCAL_IMAGE_GROUPS', '')
HOST_CONFIG_FILE = "hosts.yaml"