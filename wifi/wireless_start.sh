#!/bin/bash

# --- CONFIGURATION ---
SCRIPT_DIR="/home/pi"
PYTHON_SCRIPT="capture_packets.py"
LOG_FILE="packet_capture.log"

# Options: 
#   To capture ALL packets on channel 6 automatically:
#     FLAGS="-m all -c 6"
#   To scan and lock onto a specific router MAC automatically:
#     FLAGS="-m scan -b 00:11:22:33:44:55"
#   To launch in INTERACTIVE mode (requires running inside an open terminal):
#     FLAGS=""
FLAGS="-m all -c 1"
# ---------------------

echo "[+] Starting Wireless Packet Capture Automation Pipeline..." >> "$SCRIPT_DIR/$LOG_FILE"

# 1. Wait for system USB driver infrastructure to stabilize after a cold boot
sleep 5

# 2. Check if the ESP32 serial port exists before running to avoid silent crashes
if [ ! -e "/dev/ttyUSB0" ]; then
    echo "[-] ERROR: /dev/ttyUSB0 not found. ESP32 disconnected?" >> "$SCRIPT_DIR/$LOG_FILE"
    exit 1
fi

# 3. Launch the Python engine in the background
#    - 'nohup' keeps it alive if the terminal session closes
#    - '>>' redirects console output directly to your log file
nohup python3 "$SCRIPT_DIR/$PYTHON_SCRIPT" $FLAGS >> "$SCRIPT_DIR/$LOG_FILE" 2>&1 &

# 4. Capture the Background Process ID (PID)
LAUNCH_PID=$!
echo "[🚀] Success! Engine running in background with PID: $LAUNCH_PID" >> "$SCRIPT_DIR/$LOG_FILE"
echo "[🚀] Success! Engine running in background with PID: $LAUNCH_PID"


# 5. Save the PID to a file so a stop script can find it easily later
echo $LAUNCH_PID > "$SCRIPT_DIR/capture.pid"

