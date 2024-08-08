# Use the official Python image as a base
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies and Docker
RUN apt-get update && \
    apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    openssh-client \
    git && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
    echo "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt to install dependencies
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Dockyman application code
COPY . .

# Ensure that the app directory is in the Python path
ENV PYTHONPATH=/app

# Make sure the scripts are executable
RUN chmod +x /app/dockyman/cli.py

# Set the entrypoint to the Dockyman CLI
ENTRYPOINT ["python", "/app/dockyman/cli.py"]

# Default command to show help
CMD ["--help"]
