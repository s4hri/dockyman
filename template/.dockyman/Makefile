USER_UID := $(shell id -u)
LINUX_DISTRO := $(shell awk -F= '/^ID=/{print $$2}' /etc/os-release)
LINUX_VERSION := $(shell awk -F= '/^VERSION_ID=/{print $$2}' /etc/os-release)

include .env

export USER_UID

.DEFAULT_GOAL := default

DOCKER_COMPOSE := $(shell command -v docker-compose 2>/dev/null || echo "docker-compose")
DOCKER_COMPOSE_CLI := $(shell command -v docker 2>/dev/null && docker compose --version 2>/dev/null || echo "docker compose")

COMPOSE_DEV := -f compose.dev.yaml
COMPOSE_PROD := -f compose.yaml

GPU_PROFILE := no-gpu

DOCKYMAN_SERVICES := $(shell USER_UID=${USER_UID} ${DOCKER_COMPOSE} ${COMPOSE_DEV} config --services)

.PHONY: init install-docker check-nvidia build-base build-local push clean init-host stop log dockyman-run

default: init build

check-nvidia:
	@if lspci | grep -i nvidia >/dev/null 2>&1; then \
		echo "NVIDIA GPU was detected."; \
		GPU_PROFILE=nvidia-gpu; \
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

init: install-docker check-nvidia

build-base: stop
	@for service in $(DOCKYMAN_SERVICES); do \
		echo "Building base image from service $$service ..."; \
		set -e; \
		ACTION=build_base ${DOCKER_COMPOSE} ${COMPOSE_DEV} run $$service; \
	done

build-local: stop
	@for service in $(DOCKYMAN_SERVICES); do \
		echo "Building local image from service $$service ..."; \
		set -e; \
		ACTION=build_local ${DOCKER_COMPOSE} ${COMPOSE_DEV} run $$service; \
	done

push: stop
	@for service in $(DOCKYMAN_SERVICES); do \
		echo "Pushing image from service $$service ..."; \
		set -e; \
		ACTION=push ${DOCKER_COMPOSE} ${COMPOSE_DEV} run $$service; \
	done

clean: stop
	@for service in $(DOCKYMAN_SERVICES); do \
		echo "Cleaning base image from service $$service ..."; \
		set -e; \
		ACTION=clean ${DOCKER_COMPOSE} ${COMPOSE_DEV} run $$service; \
	done

init-host:
	bash scripts/initHost.sh

stop:
	${DOCKER_COMPOSE} ${COMPOSE_DEV} down --remove-orphans
	${DOCKER_COMPOSE} --log-level ERROR down --remove-orphans

log:
	bash scripts/logLocalInfo.sh > ../lastrun.log

dockyman-run:
	GPU_PROFILE=${GPU_PROFILE} ${DOCKER_COMPOSE} ${COMPOSE_PROD} up --remove-orphans

build: build-base build-local

run: build-local init log init-host dockyman-run stop

clean-docker:
	@docker container prune -f
	@docker network prune -f
	@docker image prune -af
	@docker volume prune -f
