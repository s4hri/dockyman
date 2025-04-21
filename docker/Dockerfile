# Use the official Python image as a base
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

ARG DOCKYMAN_VER

ENV DOCKYMAN_VER=$DOCKYMAN_VER

# Install system dependencies and Docker
RUN apt-get update && \
    apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    openssh-client \
    git \
    gosu \
    sudo && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
    echo "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user named 'docky' and add it to the sudo group
RUN useradd -m -s /bin/bash docky && \
    usermod -aG sudo docky

# Allow 'docky' to use sudo without a password
RUN echo 'docky ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Create 'docker' group if it does not exist and add 'docky' to it
RUN groupadd -f docker && usermod -aG docker docky

# Set permissions for 'docky' home directory and any necessary files
RUN chown -R docky:docky /home/docky

# Copy the requirements.txt to install dependencies
COPY requirements.txt .

# Ensure that the app directory is in the Python path
ENV PYTHONPATH=/app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Dockyman application code
COPY . .

RUN chown -R docky:docky /app

# Make sure the scripts are executable
RUN chmod +x /app/dockyman/cli.py

COPY docker/entrypoint.sh /app/entrypoint.sh

RUN sudo chmod +x /app/entrypoint.sh

# Use the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command to show help
CMD ["--help"]
