
# Minimal example Dockerfile for X11 and audio passthrough
FROM debian:stable-slim

ARG PUID=1000
ARG PGID=1000


RUN apt-get update && \
    apt-get install -y x11-apps pulseaudio-utils sox libsox-fmt-pulse sudo && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /etc/sudoers.d

ENV DEBIAN_FRONTEND=noninteractive

RUN groupadd -g $PGID docky || true
RUN useradd -m -s /bin/bash -u $PUID -g $PGID docky
RUN usermod -a -G root,sudo,video,audio docky
RUN echo "docky ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/docky && chmod 0440 /etc/sudoers.d/docky

RUN chown -R $PUID:$PGID /home/docky/

USER docky

ENV PATH=$PATH:/home/docky/.local/bin

CMD ["bash", "-c",  "xeyes & sleep 1 && play -n synth 1 sine 440 && cat /etc/hosts"]
