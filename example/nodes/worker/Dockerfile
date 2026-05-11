
# Minimal example Dockerfile for a worker node
FROM debian:stable-slim

ARG PUID=1000
ARG PGID=1000

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y sudo && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /etc/sudoers.d

RUN groupadd -g $PGID docky || true
RUN useradd -m -s /bin/bash -u $PUID -g $PGID docky
RUN usermod -a -G root,sudo docky
RUN echo "docky ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/docky && chmod 0440 /etc/sudoers.d/docky

RUN chown -R $PUID:$PGID /home/docky/

USER docky

ENV PATH=$PATH:/home/docky/.local/bin

CMD ["bash", "-c", "cat /etc/hosts"]
