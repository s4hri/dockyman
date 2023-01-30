# MIT License
#
# Copyright (c) 2023 Social Cognition in Human-Robot Interaction
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

#!/bin/bash
set -e

CURRENT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"


IFS=',' read -r -a groups_array <<< "$USER_GROUPS"
IFS=',' read -r -a ids_array <<< "$GROUP_IDS"

for i in "${!groups_array[@]}"; do
    printf "%s\t%s\t%s\n" "$i" ${groups_array[$i]} ${ids_array[$i]}
    if [ $(getent group ${groups_array[$i]}) ]; then groupmod -o ${groups_array[$i]} --gid ${ids_array[$i]}; else groupadd ${groups_array[$i]} --gid ${ids_array[$i]}; fi
done

if [ -z "$(getent passwd "${USER_UID}" | cut -d: -f1)" ]; then \
  if [ $(getent passwd ${USERNAME}) ]; then \
      echo "User exists" && usermod -u ${USER_UID} ${USERNAME} && groupmod -g ${USER_GID} ${USERNAME} && passwd -d ${USERNAME}; \
  else \
      echo "User not found" && useradd ${USERNAME} && passwd -d ${USERNAME} && usermod -u ${USER_UID} ${USERNAME} && groupmod -g ${USER_GID} ${USERNAME}; \
  fi; \
else \
    echo "UID exists" && old_uname=$(getent passwd "${USER_UID}" | cut -d: -f1) && usermod -l ${USERNAME} ${old_uname} &&  groupmod -n ${USERNAME} ${old_uname}; \
fi;

usermod -ms /bin/bash -d /home/${USERNAME} ${USERNAME}
#mkdir -p /home/$USERNAME
#cp /etc/skel/.bashrc /home/$USERNAME
#cp /etc/skel/.profile /home/$USERNAME
#cp /etc/skel/.bash_logout /home/$USERNAME
chown -R $USER_UID:$USER_GID /home/$USERNAME

if [[ " ${groups_array[*]} " =~ " sudo " ]]; then
    echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME
    chmod 0440 /etc/sudoers.d/$USERNAME
    usermod -a -G root "$(getent passwd ${USER_UID} | cut -d: -f1)"
fi

usermod -a -G $GROUP_IDS "$(getent passwd ${USER_UID} | cut -d: -f1)"
