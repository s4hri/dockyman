#!/bin/bash

echo "DOCKYMAN -> Running inizialization script (docker container)"
set -a
source /var/dockyman/scripts/env_vars
set +a
exec "$@"
