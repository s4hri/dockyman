#!/bin/bash

set -e

echo "DOCKYMAN -> Running host pre-launch configuration..."

# --- Check if PulseAudio is installed and running ---
if command -v pulseaudio > /dev/null && command -v pactl > /dev/null; then
    if ! pactl info > /dev/null 2>&1; then
        echo "🟡 PulseAudio not running. Trying to start it..."
        pulseaudio --start || echo "🔴 [ERROR] Failed to start PulseAudio."
    else
        echo "🟢 PulseAudio is running."
    fi
else
    echo "🔵 PulseAudio is not installed. Audio may not work in containers."
    
    # Optional installation suggestions
    if [ -f /etc/debian_version ]; then
        echo "-> You can install it on Debian/Ubuntu with: sudo apt install pulseaudio"
    else
        echo "[!] Please install PulseAudio using your distribution package manager."
    fi
fi

# --- X11 Display Access ---
if command -v xhost &> /dev/null; then
    xhost +local:docker > /dev/null
    echo "🟢 X11 access granted to Docker containers."
else
    echo "🟡 'xhost' not found. GUI apps may not display correctly."
fi

# --- PulseAudio socket check ---
PULSE_SOCKET="$XDG_RUNTIME_DIR/pulse/native"
if [[ -S "$PULSE_SOCKET" ]]; then
    echo "🟢 PulseAudio socket found: $PULSE_SOCKET"
else
    echo "🟡 PulseAudio socket not found at $PULSE_SOCKET"
fi

# --- GPU detection ---
if command -v nvidia-smi &> /dev/null && nvidia-smi -L &> /dev/null; then
    echo "🟢 GPU detected — enabling NVIDIA runtime"
    export DOCKER_RUNTIME=nvidia
    export GPU_DEVICES=all
else
    echo "🔵 No GPU found — falling back to CPU mode"
    export DOCKER_RUNTIME=runc
    export GPU_DEVICES=none
fi

echo "✅ Host setup successful. Ready to launch Docker containers."
