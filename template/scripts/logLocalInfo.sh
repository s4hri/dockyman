#!/bin/bash

cat /etc/os-release
echo ""
date
echo ""
lsb_release -a
echo ""
aplay -l
echo ""
free
echo ""
lshw
echo ""
docker version
echo ""
docker compose version