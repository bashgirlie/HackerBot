#!/bin/bash

SCRIPT_DIR="/home/pi"
PID_FILE="$SCRIPT_DIR/capture.pid"
LOG_FILE="$SCRIPT_DIR/packet_capture.log"

if [ -f "$PID_FILE" ]; then
    TARGET_PID=$(cat "$PID_FILE")
    echo "[+] Stopping packet capture process: $TARGET_PID"
    echo "[+] Stopping packet capture process: $TARGET_PID" >> "$LOG_FILE"
    
    # Send SIGINT (same as pressing Ctrl+C) so Python safely flushes and closes the PCAP file
    kill -2 $TARGET_PID
    
    rm "$PID_FILE"
else
    echo "[-] No active capture.pid file found."
fi
