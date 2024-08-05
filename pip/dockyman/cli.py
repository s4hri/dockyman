import os
import sys
import docker

def init_command(directory):
    client = docker.from_env()
    image_name = "iitschri/dockyman:latest"
    
    # Check if the Docker image is available, if not pull it
    try:
        client.images.get(image_name)
    except docker.errors.ImageNotFound:
        print(f"Image {image_name} not found locally. Pulling from Docker Hub...")
        client.images.pull(image_name)

    # Absolute path of the target directory
    target_directory = os.path.abspath(directory)

    # Check if target directory exists
    if not os.path.exists(target_directory):
        print(f"Error: The target directory {target_directory} does not exist.")
        sys.exit(1)
    
    # Get the current user and group id
    user_id = os.getuid()
    group_id = os.getgid()

    # Create a temporary container with a bind mount
    print(f"Running container to copy files from /workdir/model to {target_directory}")
    container = client.containers.run(
        image_name,
        command=f"sh -c 'cp -r /workdir/model/* /target_directory && chown -R {user_id}:{group_id} /target_directory'",
        volumes={target_directory: {'bind': '/target_directory', 'mode': 'rw'}},
        detach=True
    )

    # Wait for the container to finish its job
    result = container.wait()
    logs = container.logs().decode('utf-8')
    print("Container logs:\n", logs)

    # Clean up the temporary container
    container.remove()

    # Check if the files were copied
    if not os.listdir(target_directory):
        print(f"Error: No files were copied to {target_directory}. Please check the container logs above for details.")
    else:
        print(f"Contents from /workdir/model in {image_name} have been copied to {directory} with correct ownership.")

def install_command(inventory_filepath):
    client = docker.from_env()
    image_name = "iitschri/dockyman:latest"
    
    # Check if the Docker image is available, if not pull it
    try:
        client.images.get(image_name)
    except docker.errors.ImageNotFound:
        print(f"Image {image_name} not found locally. Pulling from Docker Hub...")
        client.images.pull(image_name)

    # Absolute path of the inventory file
    inventory_path = os.path.abspath(inventory_filepath)

    # Check if inventory file exists
    if not os.path.exists(inventory_path):
        print(f"Error: The inventory file {inventory_path} does not exist.")
        sys.exit(1)
    
    # Create a temporary container with a bind mount
    print(f"Running container to execute Ansible playbook with inventory file {inventory_path}")
    container = client.containers.run(
        image_name,
        command=f"ansible-playbook /workdir/ansible/jobs/setup/install_docker.yml -i /inventory/inventory.ini",
        volumes={inventory_path: {'bind': '/inventory/inventory.ini', 'mode': 'rw'}},
        detach=True
    )

    # Wait for the container to finish its job
    result = container.wait()
    logs = container.logs().decode('utf-8')
    print("Container logs:\n", logs)

    # Clean up the temporary container
    container.remove()

    print(f"Ansible playbook executed with inventory file {inventory_path}")

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
    else:
        print(f"Unknown command: {command}")
        print("Usage: dockyman <command> <args>")
        sys.exit(1)

if __name__ == "__main__":
    main()
