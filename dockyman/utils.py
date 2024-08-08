import paramiko
from urllib.parse import urlparse
import logging
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Set up basic logging
logging.basicConfig(level=logging.FATAL)
logger = logging.getLogger(__name__)

def run_ssh_command(host, command):
    url = urlparse(host)
    hostname = url.hostname
    username = url.username
    port = url.port if url.port else 22  # Default to port 22 if not specified

    logger.debug(f"Connecting to {hostname} as {username} on port {port}")
    #print(Fore.CYAN + f"  Connecting to {hostname} as {username} on port {port}")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=hostname, username=username, port=port)

    logger.debug(f"Executing command: {command}")

    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()

    logger.debug(f"Exit status: {exit_status}")

    if exit_status != 0:
        error_message = stderr.read().decode().strip()
        raise Exception(f"Command failed on {hostname}: {error_message}")

    result = stdout.read().decode().strip()
    ssh.close()
    logger.debug(f"Command output: {result}")
    print(Fore.GREEN + f"  Executing command: {command}", 
          Fore.YELLOW + f"  Exit status: {exit_status}", 
          Fore.WHITE + Style.BRIGHT + f"  Command output: {result}")
    return result
