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
USER_GID := $(shell id -g)
LINUX_DISTRO := $(shell awk -F= '/^ID=/{print $$2}' /etc/os-release)
LINUX_VERSION := $(shell awk -F= '/^VERSION_ID=/{print $$2}' /etc/os-release)

export USER_UID
export USER_GID

.DEFAULT_GOAL := default

DOCKER_COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; else echo "docker compose"; fi)


ENV_FILE_RUN := ../.env
ENV_FILE_BUILD := ../build.env
COMPOSE_BASE := -f ../compose.base.yaml
COMPOSE_LOCAL := -f ../compose.local.yaml
COMPOSE_RUN := -f ../compose.yaml
ENV_BUILD := --env-file ${ENV_FILE_BUILD}

DOCKYMAN_BASE_COMMAND := ${DOCKER_COMPOSE} ${COMPOSE_BASE} ${ENV_BUILD}
DOCKYMAN_LOCAL_COMMAND := ${DOCKER_COMPOSE} ${COMPOSE_LOCAL} ${ENV_BUILD}

DOCKYMAN_BUILD_BASE_COMMAND := ${DOCKYMAN_BASE_COMMAND} up --remove-orphans
DOCKYMAN_BUILD_LOCAL_COMMAND := ${DOCKYMAN_LOCAL_COMMAND} up --remove-orphans

DOCKYMAN_RUN_COMMAND := ${DOCKER_COMPOSE} ${COMPOSE_RUN} up --remove-orphans

DOCKYMAN_BASE_SERVICES := $(shell USER_UID=${USER_UID} USER_GID=${USER_GID} ${DOCKYMAN_BASE_COMMAND} config --services)
DOCKYMAN_LOCAL_SERVICES := $(shell USER_UID=${USER_UID} USER_GID=${USER_GID} ${DOCKYMAN_LOCAL_COMMAND} config --services)

.PHONY: init install-docker install-docker-compose check-nvidia build build-base build-local dev release push clean init-host stop log dockyman-run

default:
	@if grep -q '^PROFILE=dev' ${ENV_FILE_BUILD}; then \
        $(MAKE) init && $(MAKE) build && $(MAKE) create_env; \
	else \
		echo "The building process is completed!"; \
		echo "To rebuild please make sure you are in development profile running 'make dev'"; \
	fi

create_env:
	@rm -f ${ENV_FILE_RUN};
	@cat ${ENV_FILE_BUILD} >> ${ENV_FILE_RUN};
	@echo "" >> ${ENV_FILE_RUN};
	@if lspci | grep -i nvidia >/dev/null 2>&1; then \
		echo "NVIDIA GPU was detected."; \
		echo "GPU_PROFILE=nvidia-gpu" >> ${ENV_FILE_RUN}; \
	else \
		echo "GPU_PROFILE=no-gpu" >> ${ENV_FILE_RUN}; \
	fi

check_docker_sock_permission:
	@if [ -S /var/run/docker.sock ]; then \
		if test -w /var/run/docker.sock; then \
			echo "Current user has write permission on /var/run/docker.sock"; \
		else \
			echo "Current user does not have write permission on /var/run/docker.sock"; \
		fi; \
	else \
		echo "Docker socket not found: /var/run/docker.sock"; \
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

init: install-docker install-docker-compose check_docker_sock_permission check-nvidia

build-base: stop
	@for service in $(DOCKYMAN_BASE_SERVICES); do \
		echo "Building base image from service '$$service' ..."; \
		set -e; \
		ACTION=build_base ${DOCKYMAN_BASE_COMMAND} run $$service; \
	done

build-local: stop
	@for service in $(DOCKYMAN_LOCAL_SERVICES); do \
		echo "Building local image from service '$$service' ..."; \
		set -e; \
		ACTION=build_local ${DOCKYMAN_LOCAL_COMMAND} run $$service; \
	done

push: stop
	@for service in $(DOCKYMAN_BASE_SERVICES); do \
		echo "Pushing base image from service '$$service' ..."; \
		set -e; \
		ACTION=push ${DOCKYMAN_BASE_COMMAND} run $$service; \
	done

clean: stop
	@rm -f ${ENV_FILE_RUN};
	@for service in $(DOCKYMAN_BASE_SERVICES); do \
		echo "Cleaning image from service '$$service' ..."; \
		set -e; \
		ACTION=clean ${DOCKYMAN_BASE_COMMAND} run $$service; \
	done

dev:
	@if grep -q '^PROFILE=' ${ENV_FILE_BUILD}; then \
        sed -i 's/^PROFILE=.*/PROFILE=dev/' ${ENV_FILE_BUILD}; \
    else \
        echo "PROFILE=dev" >> ${ENV_FILE_BUILD}; \
    fi; \
	$(MAKE) create_env;
	@echo "Development profile added or updated in ${ENV_FILE_BUILD}"

release:
	@echo "Creating release..."
	@if [ "${VERSION}" ]; then \
		if grep -q '^VERSION=' ${ENV_FILE_BUILD}; then \
			sed -i 's/^VERSION=.*/VERSION=${VERSION}/' ${ENV_FILE_BUILD}; \
		else \
			echo "VERSION=${VERSION}" >> ${ENV_FILE_BUILD}; \
		fi; \
		echo "Version ${VERSION} added or updated in ${ENV_FILE_BUILD}"; \
		if grep -q '^PROFILE=' ${ENV_FILE_BUILD}; then \
			sed -i 's/^PROFILE=.*/PROFILE=prod/' ${ENV_FILE_BUILD}; \
		else \
			echo "PROFILE=prod" >> ${ENV_FILE_BUILD}; \
		fi; \
		echo "Development profile added or updated in ${ENV_FILE_BUILD}"; \
		$(MAKE) create_env; \
	else \
		echo "Please provide a version using 'make release VERSION=<version>'"; \
	fi
    

init-host:
	bash scripts/initHost.sh

build: build-base build-local

stop:
	${DOCKYMAN_BASE_COMMAND} down --remove-orphans
	${DOCKYMAN_LOCAL_COMMAND} down --remove-orphans

log:
	bash scripts/logLocalInfo.sh > ../lastrun.log

dockyman-run:
	${DOCKYMAN_RUN_COMMAND}

run: default log init-host dockyman-run stop

clean-docker:
	@docker container prune -f
	@docker network prune -f
	@docker image prune -af
	@docker volume prune -f