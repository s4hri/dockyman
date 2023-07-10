# MIT License
#
# Copyright (c) 2023 Istituto Italiano di Tecnologia (IIT)
#                    Author: Davide De Tommaso (davide.detommaso@iit.it)
#                    Project: Dockyman
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

USER_UID := $(shell id -u)
LINUX_DISTRO := $(shell awk -F= '/^ID=/{print $$2}' /etc/os-release)
LINUX_VERSION := $(shell awk -F= '/^VERSION_ID=/{print $$2}' /etc/os-release)

include base.env

export USER_UID

.DEFAULT_GOAL := default

DOCKER_COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; else echo "docker compose"; fi)

COMPOSE_DEV := -f compose.dev.yaml
COMPOSE_PROD := -f compose.yaml
ENV_DEV := --env-file base.env
ENV_PROD := --env-file local.env

#GPU_PROFILE := no-gpu

DOCKYMAN_DEV_COMMAND := ${DOCKER_COMPOSE} ${COMPOSE_DEV} ${ENV_DEV}
DOCKYMAN_PROD_COMMAND := ${DOCKER_COMPOSE} ${COMPOSE_PROD} ${ENV_PROD}
DOCKYMAN_DEV_SERVICES := $(shell USER_UID=${USER_UID} ${DOCKYMAN_DEV_COMMAND} config --services)

.PHONY: init install-docker install-docker-compose check-nvidia build build-base build-local push clean init-host stop log dockyman-run

default:
	@if [ ! -f local.env ]; then \
		echo "LOCAL_IMAGE_NAME=${IMAGE_NAME}.local" > local.env; \
		if lspci | grep -i nvidia >/dev/null 2>&1; then \
			echo "NVIDIA GPU was detected."; \
			echo "GPU_PROFILE=nvidia-gpu" >> local.env; \
		else \
			echo "GPU_PROFILE=no-gpu" >> local.env; \
		fi; \
		$(MAKE) init; \
		$(MAKE) build; \
	fi

check-nvidia:
	@if lspci | grep -i nvidia >/dev/null 2>&1; then \
		if dpkg -s nvidia-docker2 >/dev/null 2>&1; then \
			echo "nvidia-docker2 is already installed."; \
		else \
			echo "nvidia-docker2 is not installed."; \
			read -p "Do you want to install the NVIDIA Container Toolkit? [Y/N]: " response; \
				if [ "$$response" = "Y" ]; then \
					LINUX_DISTRO=$(LINUX_DISTRO) LINUX_VERSION=$(LINUX_VERSION); \
					URL="$$(case $$LINUX_DISTRO in ubuntu) echo 'https://nvidia.github.io/nvidia-docker/$$LINUX_DISTRO$$LINUX_VERSION.04/nvidia-docker.list' ;; debian) echo 'https://nvidia.github.io/nvidia-docker/$$LINUX_DISTRO$$LINUX_VERSION/nvidia-docker.list' ;; *) echo '' ;; esac)"; \
					[ -n "$$URL" ] && \
					{ \
						curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -; \
						curl -s -L "$$URL" | sudo tee /etc/apt/sources.list.d/nvidia-docker.list; \
						sudo apt-get update; \
						sudo apt-get install -y nvidia-docker2; \
						sudo systemctl restart docker; \
					}; \
				else \
					echo "Skipping package installation."; \
				fi; \
		fi; \
	fi


install-docker:
	@if ! command -v docker >/dev/null 2>&1; then \
		echo "Docker is not installed in your system."; \
		read -p "Do you want to install Docker from the official repository? [Y/N]: " response; \
			if [ $$response = "Y" ]; then \
				echo "Installing package..."; \
				curl -fsSL https://get.docker.com -o get-docker.sh; \
				sudo sh get-docker.sh; \
				rm get-docker.sh; \
			else \
				echo "Skipping package installation."; \
			fi \
	else \
		echo "Docker is already installed."; \
	fi

install-docker-compose:
	@$(DOCKER_COMPOSE) version >/dev/null 2>&1 || { \
		echo "Docker Compose not found. Installing..."; \
		curl -sSL https://github.com/docker/compose/releases/latest/download/docker-compose-$(shell uname -s)-$(shell uname -m) -o /usr/local/bin/docker-compose; \
		chmod +x /usr/local/bin/docker-compose; \
		echo "Docker Compose installed successfully!"; \
	}

init: install-docker install-docker-compose check-nvidia

build-base: stop
	@for service in $(DOCKYMAN_DEV_SERVICES); do \
		echo "Building base image from service '$$service' ..."; \
		set -e; \
		ACTION=build_base ${DOCKYMAN_DEV_COMMAND} run $$service; \
	done

build-local: stop
	@for service in $(DOCKYMAN_DEV_SERVICES); do \
		echo "Building local image from service '$$service' ..."; \
		set -e; \
		ACTION=build_local ${DOCKYMAN_DEV_COMMAND} run $$service; \
	done

push: stop
	@for service in $(DOCKYMAN_DEV_SERVICES); do \
		echo "Pushing image from service '$$service' ..."; \
		set -e; \
		ACTION=push ${DOCKYMAN_DEV_COMMAND} run $$service; \
	done

clean: stop
	rm -f local.env
	@for service in $(DOCKYMAN_DEV_SERVICES); do \
		echo "Cleaning base image from service '$$service' ..."; \
		set -e; \
		ACTION=clean ${DOCKYMAN_DEV_COMMAND} run $$service; \
	done

init-host:
	bash scripts/initHost.sh

stop:
	${DOCKYMAN_DEV_COMMAND} down --remove-orphans

log:
	bash scripts/logLocalInfo.sh > ../lastrun.log

dockyman-run:
	${DOCKYMAN_PROD_COMMAND} up --remove-orphans

build: build-base build-local

run: default log init-host dockyman-run stop

clean-docker:
	@docker container prune -f
	@docker network prune -f
	@docker image prune -af
	@docker volume prune -f