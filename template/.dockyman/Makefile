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

ifeq ($(origin PROJECT_DIR), undefined)
    PROJECT_DIR := ..
else
    PROJECT_DIR := $(PROJECT_DIR)
endif

SCRIPTS := ${PROJECT_DIR}/scripts
ENV_FILE_RUN := ${PROJECT_DIR}/.env
ENV_FILE_BUILD := ${PROJECT_DIR}/build.env
COMPOSE_BASE := -f ${PROJECT_DIR}/compose.base.yaml
COMPOSE_LOCAL := -f ${PROJECT_DIR}/compose.local.yaml
COMPOSE_RUN := -f ${PROJECT_DIR}/compose.yaml
ENV_BUILD := --env-file ${ENV_FILE_BUILD}


UNAME := $(shell uname)
DOCKER_INSTALLED := $(shell command -v docker 2> /dev/null)
DOCKER_COMPOSE_INSTALLED := $(shell command -v docker-compose 2> /dev/null)
NVIDIA_DOCKER_INSTALLED := $(shell command -v nvidia-container-toolkit 2> /dev/null)
HAS_NVIDIA_GPU := $(shell lspci | grep -i nvidia)
HAS_DOCKER_GROUP := $(shell groups $(USER) | grep -o '\bdocker\b')

ifeq ($(UNAME), Linux)
    ifeq ($(shell lsb_release -is), Ubuntu)
        PACKAGE_MANAGER := apt-get
        DOCKER_INSTALL_CMD := curl -fsSL https://get.docker.com | sh
        DOCKER_COMPOSE_INSTALL_CMD := sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.3/docker-compose-$(shell uname -s)-$(shell uname -m)" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose
        NVIDIA_DOCKER_INSTALL_CMD := \
		                            curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg ; \
	                                curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
	                                sed 's\#deb https://\#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://\#g' | \
	                                sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list ; \
	                                sed -i -e '/experimental/ s/^\#//g' /etc/apt/sources.list.d/nvidia-container-toolkit.list ; \
	                                sudo apt-get update ; \
	                                sudo apt-get install -y nvidia-container-toolkit

    else ifeq ($(shell cat /etc/os-release | grep '^ID=' | cut -d= -f2), centos)
        PACKAGE_MANAGER := yum
        DOCKER_INSTALL_CMD := sudo yum install -y docker-ce
        DOCKER_COMPOSE_INSTALL_CMD := sudo curl -L "https://github.com/docker/compose/releases/download/2.23.3/docker-compose-$(shell uname -s)-$(shell uname -m)" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose
        NVIDIA_DOCKER_INSTALL_CMD := curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | \
		                             sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo ; \
									 sudo yum-config-manager --enable nvidia-container-toolkit-experimental ; \
									 sudo yum install -y nvidia-container-toolkit

    else ifeq ($(shell cat /etc/os-release | grep '^ID=' | cut -d= -f2), arch)
        PACKAGE_MANAGER := pacman
        DOCKER_INSTALL_CMD := sudo pacman -S --noconfirm docker
        DOCKER_COMPOSE_INSTALL_CMD := sudo pacman -S --noconfirm docker-compose
        NVIDIA_DOCKER_INSTALL_CMD := sudo pacman -S --noconfirm nvidia-docker
    else ifeq ($(shell cat /etc/os-release | grep '^ID=' | cut -d= -f2), alpine)
        PACKAGE_MANAGER := apk
        DOCKER_INSTALL_CMD := apk add --no-cache docker
        DOCKER_COMPOSE_INSTALL_CMD := apk add --no-cache docker-compose
        NVIDIA_DOCKER_INSTALL_CMD := echo "Alpine Linux does not support NVIDIA Docker by default." ; \
                                     echo "Please refer to the NVIDIA Docker documentation for Alpine-based images: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#alpine"
    else
        $(error Unsupported Linux distribution)
    endif
else
    $(error This Makefile is intended for Linux only)
endif

ifeq ($(DOCKER_INSTALLED),)
all: install-all
else
DOCKER_COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; else echo "docker compose"; fi)

DOCKYMAN_BASE_COMMAND := ${DOCKER_COMPOSE} ${COMPOSE_BASE} ${ENV_BUILD}
DOCKYMAN_LOCAL_COMMAND := ${DOCKER_COMPOSE} ${COMPOSE_LOCAL} ${ENV_BUILD}

DOCKYMAN_BUILD_BASE_COMMAND := ${DOCKYMAN_BASE_COMMAND} up --remove-orphans
DOCKYMAN_BUILD_LOCAL_COMMAND := ${DOCKYMAN_LOCAL_COMMAND} up --remove-orphans

DOCKYMAN_RUN_COMMAND := ${DOCKER_COMPOSE} ${COMPOSE_RUN} up --remove-orphans

DOCKYMAN_BASE_SERVICES := $(shell USER_UID=${USER_UID} USER_GID=${USER_GID} ${DOCKYMAN_BASE_COMMAND} config --services)
DOCKYMAN_LOCAL_SERVICES := $(shell USER_UID=${USER_UID} USER_GID=${USER_GID} ${DOCKYMAN_LOCAL_COMMAND} config --services)
endif


.PHONY: install-docker
install-docker:
	@if [ -z "$(DOCKER_INSTALLED)" ]; then \
        read -p "Docker is not installed. Do you want to install it? (y/N) " choice; \
        case "$$choice" in \
            y|Y) $(DOCKER_INSTALL_CMD) ;; \
            *) echo "Aborting Docker installation." ;; \
        esac \
    else \
        echo "Docker is already installed." ; \
    fi

.PHONY: install-docker-compose
install-docker-compose:
	@if [ -z "$(DOCKER_COMPOSE_INSTALLED)" ]; then \
        read -p "Docker Compose is not installed. Do you want to install it? (y/N) " choice; \
        case "$$choice" in \
            y|Y) $(DOCKER_COMPOSE_INSTALL_CMD) ;; \
            *) echo "Aborting Docker Compose installation." ;; \
        esac \
    else \
        echo "Docker Compose is already installed." ; \
    fi

.PHONY: install-nvidia-docker
install-nvidia-docker:
	@if [ -z "$(NVIDIA_DOCKER_INSTALLED)" ] && [ -n "$(HAS_NVIDIA_GPU)" ]; then \
        read -p "NVIDIA Docker is not installed. Do you want to install it? (y/N) " choice; \
        case "$$choice" in \
            y|Y) $(NVIDIA_DOCKER_INSTALL_CMD) ;; \
            *) echo "Aborting NVIDIA Docker installation." ;; \
        esac \
    elif [ -z "$(HAS_NVIDIA_GPU)" ]; then \
        echo "No NVIDIA GPU detected. Skipping NVIDIA Docker installation." ; \
    else \
        echo "NVIDIA Docker is already installed." ; \
    fi

.PHONY: add-docker-group
add-docker-group:
	@if [ -z "$(HAS_DOCKER_GROUP)" ]; then \
        read -p "Your user is not in the 'docker' group. Do you want to add it? (y/N) " choice; \
        case "$$choice" in \
            y|Y) sudo usermod -aG docker $(USER); $(MAKE) reboot ;; \
            *) echo "Not adding your user to the 'docker' group." ;; \
        esac \
    else \
        echo "Your user is already in the 'docker' group." ; \
    fi


.PHONY: reboot
reboot:
	@read -p "Do you want to reboot the machine now? (y/N) " choice; \
    case "$$choice" in \
        y|Y) sudo reboot ;; \
        *) echo "Skipping system reboot." ;; \
    esac

.PHONY: install-all
install-all: install-docker install-docker-compose install-nvidia-docker add-docker-group
	@echo "Installation and configuration completed."


.PHONY: uninstall-docker
uninstall-docker:
	@read -p "This will uninstall Docker, its configuration, and remove Docker images and containers. Do you want to proceed? (y/N) " choice; \
	case "$$choice" in \
		y|Y) \
			echo "Stopping Docker services..." ; \
			sudo systemctl stop docker; \
			\
			echo "Uninstalling Docker packages..." ; \
			if [ -f /etc/os-release ]; then \
				if [ "$$(grep -oP '(?<=^ID=).+' /etc/os-release)" = "ubuntu" ] || [ "$$(grep -oP '(?<=^ID=).+' /etc/os-release)" = "debian" ]; then \
					sudo apt-get purge docker-ce docker-ce-cli containerd.io; \
				elif [ "$$(grep -oP '(?<=^ID=).+' /etc/os-release)" = "centos" ]; then \
					sudo yum remove docker-ce docker-ce-cli containerd.io; \
				elif [ "$$(grep -oP '(?<=^ID=).+' /etc/os-release)" = "arch" ]; then \
					sudo pacman -Rns docker; \
				else \
					echo "Unsupported Linux distribution."; \
					exit 1; \
				fi \
			else \
				echo "Unable to determine the Linux distribution."; \
				exit 1; \
			fi; \
			\
			echo "Removing Docker configuration and data..." ; \
			sudo rm -rf /etc/docker; \
			sudo rm -rf /var/lib/docker; \
			\
			echo "Removing Docker Compose (if installed)..." ; \
			if [ -x /usr/local/bin/docker-compose ]; then \
				sudo rm /usr/local/bin/docker-compose; \
			fi; \
			\
			echo "Removing Docker user and group (if present)..." ; \
			if getent group docker >/dev/null; then \
				sudo deluser $(USER) docker; \
				sudo delgroup docker; \
			fi; \
			echo "Uninstall complete." ; \
			;; \
		*) \
			echo "Aborting uninstallation." ; \
			;; \
	esac

.PHONY: uninstall-nvidia-docker
uninstall-nvidia-docker:
	@read -p "This will uninstall NVIDIA Docker. Do you want to proceed? (y/N) " choice; \
	case "$$choice" in \
		y|Y) \
			echo "Uninstalling NVIDIA Docker..."; \
			if [ -z "$(HAS_NVIDIA_GPU)" ]; then \
				echo "No NVIDIA GPU detected. Skipping NVIDIA Docker uninstallation."; \
			else \
				if dpkg -l | grep -q nvidia-container-toolkit; then \
					sudo apt-get remove -y nvidia-container-toolkit; \
					echo "Uninstall complete."; \
				else \
					echo "NVIDIA Docker is not installed."; \
				fi; \
			fi; \
			;; \
		*) \
			echo "Aborting uninstallation."; \
			;; \
	esac

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  install-docker             Install Docker"
	@echo "  install-docker-compose     Install Docker Compose"
	@echo "  install-nvidia-docker      Install NVIDIA Docker"
	@echo "  add-docker-group           Add current user to the 'docker' group"
	@echo "  reboot                     Reboot the machine"
	@echo "  install-all                Install Docker, Docker Compose, NVIDIA Docker, add user to 'docker' group, and reboot"
	@echo "  uninstall-docker           Uninstall Docker, Docker Compose"
	@echo "  uninstall-nvidia-docker    Uninstall NVIDIA Docker"
	@echo "  help                       Display this help message"


default:
	@if grep -q '^PROFILE=development' ${ENV_FILE_BUILD}; then \
		$(MAKE) install-all && $(MAKE) build && $(MAKE) create_env; \
	else \
		if ! test -f ${ENV_FILE_RUN}; then \
			$(MAKE) install-all && $(MAKE) pull && $(MAKE) build-local && $(MAKE) create_env; \
		else \
			echo "The building process is completed!"; \
			echo "To rebuild, please make sure you are in development profile running 'make dev'"; \
		fi; \
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

build-base-nocache:
	${DOCKYMAN_BASE_COMMAND} down --remove-orphans
	${DOCKYMAN_LOCAL_COMMAND} down --remove-orphans

	@for service in $(DOCKYMAN_BASE_SERVICES); do \
		echo "Building base image from service '$$service' ..."; \
		set -e; \
		ACTION=build_base_nocache ${DOCKYMAN_BASE_COMMAND} run $$service; \
	done

build-base:
	${DOCKYMAN_BASE_COMMAND} down --remove-orphans
	${DOCKYMAN_LOCAL_COMMAND} down --remove-orphans
	@for service in $(DOCKYMAN_BASE_SERVICES); do \
		echo "Building base image from service '$$service' ..."; \
		set -e; \
		ACTION=build_base ${DOCKYMAN_BASE_COMMAND} run $$service; \
	done

remove-build-base:
	${DOCKYMAN_BASE_COMMAND} down --remove-orphans
	${DOCKYMAN_LOCAL_COMMAND} down --remove-orphans
	@for service in $(DOCKYMAN_BASE_SERVICES); do \
		echo "Removing base image from service '$$service' ..."; \
		set -e; \
		ACTION=clean_base ${DOCKYMAN_BASE_COMMAND} run $$service; \
	done

build-local:
	${DOCKYMAN_BASE_COMMAND} down --remove-orphans
	${DOCKYMAN_LOCAL_COMMAND} down --remove-orphans
	@for service in $(DOCKYMAN_LOCAL_SERVICES); do \
		echo "Building local image from service '$$service' ..."; \
		set -e; \
		ACTION=build_local ${DOCKYMAN_LOCAL_COMMAND} run $$service; \
	done

pull:
	${DOCKYMAN_BASE_COMMAND} down --remove-orphans
	${DOCKYMAN_LOCAL_COMMAND} down --remove-orphans
	@for service in $(DOCKYMAN_BASE_SERVICES); do \
		echo "Pulling base image from service '$$service' ..."; \
		set -e; \
		ACTION=pull ${DOCKYMAN_BASE_COMMAND} run $$service; \
	done

push:
	${DOCKYMAN_BASE_COMMAND} down --remove-orphans
	${DOCKYMAN_LOCAL_COMMAND} down --remove-orphans

	@for service in $(DOCKYMAN_BASE_SERVICES); do \
		echo "Pushing base image from service '$$service' ..."; \
		set -e; \
		ACTION=push ${DOCKYMAN_BASE_COMMAND} run $$service; \
	done

clean:
	${DOCKYMAN_BASE_COMMAND} down --remove-orphans
	${DOCKYMAN_LOCAL_COMMAND} down --remove-orphans

	@echo "Cleaning volumes ...";
	@${DOCKYMAN_LOCAL_COMMAND} down -v;
	@echo "Removing env ${ENV_FILE_RUN} ... ";
	@rm -f ${ENV_FILE_RUN};
	@for service in $(DOCKYMAN_BASE_SERVICES); do \
		echo "Cleaning image from service '$$service' ..."; \
		set -e; \
		ACTION=clean ${DOCKYMAN_BASE_COMMAND} run $$service; \
	done

dev:
	@echo "Configuring DEVELOPMENT PROFILE..."
	@if grep -q '^PROFILE=' ${ENV_FILE_BUILD}; then \
		sed -i 's/^PROFILE=.*/PROFILE=development/' ${ENV_FILE_BUILD}; \
	else \
		echo "PROFILE=dev" >> ${ENV_FILE_BUILD}; \
	fi;
	@echo "DEVELOPMENT PROFILE updated in ${ENV_FILE_BUILD}";
	$(MAKE) create_env;

production: remove-build-base
	@echo "Configuring PRODUCTION PROFILE..."
	@if grep -q '^PROFILE=' ${ENV_FILE_BUILD}; then \
		sed -i 's/^PROFILE=.*/PROFILE=production/' ${ENV_FILE_BUILD}; \
	else \
		echo "PROFILE=production" >> ${ENV_FILE_BUILD}; \
	fi;
	@echo "PRODUCTION PROFILE updated in ${ENV_FILE_BUILD}"; \
	$(MAKE) create_env;

init-host:
	bash ${SCRIPTS}/initHost.sh

build: build-base build-local
	@docker network prune -f

rebuild: clean build-base-nocache build-local

stop:
	${DOCKYMAN_BASE_COMMAND} down --remove-orphans
	${DOCKYMAN_LOCAL_COMMAND} down --remove-orphans

log:
	bash ${SCRIPTS}/logLocalInfo.sh > ../lastrun.log

dockyman-run:
	${DOCKYMAN_RUN_COMMAND}

run: default log init-host dockyman-run stop

clean-docker:
	@docker network prune -f
	@docker system prune -af
	@docker volume prune -f