import os
from colorama import init as colorama_init

# Initialize colorama
colorama_init(autoreset=True, strip=False, convert=False)

LOCAL_UID = int(os.getenv('LOCAL_UID', 1000))
LOCAL_GID = int(os.getenv('LOCAL_GID', 1000))
LOCAL_USERNAME = str(os.getenv('LOCAL_USERNAME', os.getenv('USER', 'docky')))
PREFIX_TARGET = str(os.getenv('PREFIX_TARGET', ''))

HOST_CONFIG_FILE = "hosts.yaml"