import os
import sys
import subprocess

def init_command(directory):
    image_name = "iitschri/dockyman:latest"
    
    # Pull the latest Docker image if not available locally
    pull_image(image_name)

    # Absolute path of the target directory
    target_directory = os.path.abspath(directory)

    # Check if the target directory exists
    if not os.path.exists(target_directory):
        print(f"Error: The target directory {target_directory} does not exist.")
        sys.exit(1)
    
    # Get the current user and group id
    user_id = os.getuid()
    group_id = os.getgid()

    # Run the Docker container to copy files
    print(f"Running container to copy files from /workdir/model to {target_directory}")
    command = [
        "docker", "run", "--rm", "--network", "host",
        "-v", f"{target_directory}:/target_directory",
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        image_name,
        "sh", "-c", f"cp -r /workdir/model/* /target_directory && chown -R {user_id}:{group_id} /target_directory"
    ]
    run_command(command)

    # Check if the files were copied
    if not os.listdir(target_directory):
        print(f"Error: No files were copied to {target_directory}.")
    else:
        print(f"Contents from /workdir/model in {image_name} have been copied to {directory} with correct ownership.")

def install_command(inventory_filepath):
    # Absolute path of the inventory file
    inventory_path = os.path.abspath(inventory_filepath)

    # Check if the inventory file exists
    if not os.path.exists(inventory_path):
        print(f"Error: The inventory file {inventory_path} does not exist.")
        sys.exit(1)
    
    # Read the inventory file and execute the install commands directly
    with open(inventory_path) as f:
        for line in f:
            if line.strip():
                run_command(line.strip().split())

def build_base_command(directory):
    image_name = "iitschri/dockyman:latest"
    
    # Pull the latest Docker image if not available locally
    pull_image(image_name)

    # Absolute path of the target directory
    target_directory = os.path.abspath(directory)

    # Check if the target directory exists
    if not os.path.exists(target_directory):
        print(f"Error: The target directory {target_directory} does not exist.")
        sys.exit(1)
    
    compose_file = os.path.join(target_directory, "compose.yaml")
    env_file = os.path.join(target_directory, "build.env")

    # Check if the compose file and env file exist
    if not os.path.exists(compose_file):
        print(f"Error: The Docker Compose file {compose_file} does not exist.")
        sys.exit(1)
    if not os.path.exists(env_file):
        print(f"Error: The environment file {env_file} does not exist.")
        sys.exit(1)

    # Run the Docker Compose build command directly
    print(f"Running Docker Compose build with {compose_file} and {env_file}")
    command = [
        "docker-compose", "-f", compose_file, "--env-file", env_file, "build"
    ]
    run_command(command, shell=False)

def pull_image(image_name):
    #print(f"Pulling Docker image {image_name}")
    #command = ["docker", "pull", image_name]
    #run_command(command)
    pass

def run_command(command, shell=True):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
    for line in iter(process.stdout.readline, b''):
        print(line.decode('utf-8').strip())
    process.stdout.close()
    process.stderr.close()
    return_code = process.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, command)

def main():
    if len(sys.argv) < 2:
        print("Usage: dockyman <command> <args>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        directory = sys.argv[2] if len(sys.argv) > 2 else "."
        init_command(directory)
    elif command == "install":
        if len(sys.argv) < 3:
            print("Usage: dockyman install <inventory_filepath>")
            sys.exit(1)
        inventory_filepath = sys.argv[2]
        install_command(inventory_filepath)
    elif command == "build_base":
        if len(sys.argv) < 3:
            print("Usage: dockyman build_base <directory>")
            sys.exit(1)
        directory = sys.argv[2]
        build_base_command(directory)
    else:
        print(f"Unknown command: {command}")
        print("Usage: dockyman <command> <args>")
        sys.exit(1)

if __name__ == "__main__":
    main()
