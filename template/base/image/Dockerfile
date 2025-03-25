# Original image stage
ARG DOCKER_SRC=ubuntu:latest
FROM ${DOCKER_SRC}

LABEL version="base"

# Install here your packages ..
RUN apt-get update && \
    apt-get install -y git x11-apps mesa-utils
