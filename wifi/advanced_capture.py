#!/usr/bin/env python3

'''
How to Use: This is automatically run by the wireless_start.sh script
To stop packet capture, foreground the process by using the PID or job tools.

Need: pip3 install pyserial
'''

import serial
import logging
import os
import sys
import struct
import argparse
import time
import random

script_pid = os.getpid()

# Standard PCAP Global Header (Link type 105 = LinkType IEEE 802.11)
PCAP_GLOBAL_HEADER = struct.pack('<IHHIIII', 0xa1b2c3d4, 2, 4, 0, 0, 65535, 105)
MAGIC_HEADER = b"START_PKT:"

logging.basicConfig(filename="packet_capture.log", filemode="a", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') 

print(f"\ncapture_packets.py started with Process ID: {script_pid}.\n"
      f"To kill background process type: kill {script_pid}\n\n")

def parse_mac(packet, offset):
    """Extract and format mac address from bytes"""
    if len(packet) < offset + 6:
        return None
    return ":".join(f"{b:02x}" for b in packet[offset:offset+6])

def parse_ssid(packet_bytes):
    """Parses human-readable Network Name (SSID) from 802.11 Beacon tags."""
    try:
        pos = 36
        while pos < len(packet_bytes):
            tag_number = packet_bytes[pos]
            tag_length = packet_bytes[pos+1]
            if tag_number == 0: # tag 0 is SSID
                ssid_bytes = packet_bytes[pos+2 : pos+2+tag_length]
                return ssid_bytes.decode('utf-8', errors='ignore')
            pos += 2 + tag_length
    except Exception:
        pass
    return "Hidden Network"

def run_automated_survey(serial_connection, survey_duration=10.0, rssi_threshold=-85):
    """
    Hops channels 1-11 rapidly to map out all nearby BSSIDs.
    Filters out weak networks and returns a list of targets sorted by signal strength.
    """
    print(f"[+] Starting automated spectrum survey ({survey_duration})...")
    logging.info(f"[+] Starting automated spectrum survey ({survey_duration})...")
        
    networks = {} # maps bssid -> {"ssid": ssid, "channel", chan, "rssi": rssi}

    start_scan = time.time()
    current_channel = 1
    last_hop = time.time()

    serial_connection.write(f"SET_CH:{current_channel}\n".encode())
    buffer = b""
    
    while time.time() - start_scan < survey_duration:
        # Hop channels every 300ms to catch beacons across the 2.4GHz band
        if time.time() - last_hop > 0.3:
            current_channel = (current_channel % 11) + 1
            serial_connection.write(f"SET_CH:{current_channel}\n".encode())
            last_hop = time.time()

        # Read from serial interface
        chunk = serial_connection.read(serial_connection.in_waiting or 512)
        if not chunk:
            continue
        buffer += chunk
        
        # Process the buffer stream
        while True:
            start_idx = buffer.find(MAGIC_HEADER)
            if start_idx == -1:
                buffer = buffer[-len(MAGIC_HEADER):] # only keeps last N bytes so we can check if header is cut across chunks
                break
            if len(buffer) < start_idx + len(MAGIC_HEADER) + 3: # +3 accounts for 2byte len + 1byte RSSI
                buffer = buffer[start_idx:]
                break

            len_offset = start_idx + len(MAGIC_HEADER)
            pkt_len = struct.unpack('<H', buffer[len_offset:len_offset+2])[0]

            # extract rssi (signed 8-bit int)
            rssi_idx = len_offset + 2 #two bytes after the start of the header (2bytes for pkt_len)
            # rssi is 1-byte and begins at the next byte after pkt_len
            rssi = struct.unpack('<b', buffer[rssi_idx:rssi_idx+1])[0]

            # payload begins 1byte after the start of rssi (rssi is 1byte)
            payload_start = rssi_idx + 1
            payload_end = payload_start + pkt_len

            # check if buffer is less than payload_end
            if len(buffer) < payloaf=d_end:
                buffer = buffer[start_idx:]
                break

            packet_bytes = buffer[payload_start:payload_end]
            buffer = buffer[payload_end:]

            # 0x80 is an 802.11 Management Frame (Beacon)
            if len(packet_bytes) >= 36 and packet_bytes[0] == 0x80:  # beacon frame
                bssid = parse_mac(packet_bytes, 16)
                ssid = parse_ssid(packet_bytes)

                if bssid:
                    if bssid not in networks or networks[bssid]["rssi"] < rssi:
                        networks[bssid] = {
                            "ssid": ssid,
                            "channel": current_channel,
                            "rssi": rssi
                        }

    # --- POST-SURVEY FILTERING & SORTING PIPELINE ---
   
    # 1. Convert dict items into a flat list
    discovered_list = list(networks.values())
   
    # 2. Filter out weak networks that will result in bad/corrupted captures
    viable_targets = [net for net in discovered_list if net["rssi"] >= rssi_threshold]
   
    # 3. Sort targets by RSSI in descending order (strongest signal first)
    # Note: Since RSSI values are negative, key=lambda x: x["rssi"] works beautifully
    # because -45 is greater than -80. reverse=True ensures highest values are index 0.
    sorted_targets = sorted(viable_targets, key=lambda x: x["rssi"], reverse=True)

    print(f"[+] Survey complete. Found {len(discovered_list)} networks, {len(sorted_targets)} are viable.")
    for idx, net in enumerate(sorted_targets[:5]): # print top 5
        print(f"  [{idx}] Strength: {net["rssi"]}dBm | Chan: {net["channel"]} | SSID: {net["ssid"]}")
    
    return sorted_targets
    


def capture_packets(serial_connection, base_pcap_name, target_bssid=None, channel=1):
    print("Listening for packets from ESP32... Press CTRL+C to stop.")  
    logging.info("Started listening for packets from ESP32 module for capture...")

    MAX_FILE_SIZE = 50 * 1024 * 1024 

    if target_bssid:
        target_bssid = target_bssid.lower()
        clean_bssid_str = target_bssid.replace(":", "")
        filename = f"{clean_bssid_str}_{base_pcap_name}"
        print(f"MODE: Target Lock. Filtering for BSSID: {target_bssid} on Channel {channel}")
        logging.info(f"MODE: Target Lock. Filtering for BSSID: {target_bssid} on Channel {channel}")
    else:
        filename = base_pcap_name
        print(f"Mode: Catch-All. Recording all traffic heard by the ESP32 on Channel {channel}...")
        logging.info(f"Mode: Catch-All. Recording all traffic heard by the ESP32 on Channel {channel}...")
    
    print(f"Writing directly to {filename}...")
    logging.info(f"Writing directly to {filename}...")

    serial_connection.write(f"SET_CH:{channel}\n".encode())
    serial_connection.reset_input_buffer()
    time.sleep(0.5)

    try:
        pcap_file = open(filename, 'wb')
        pcap_file.write(PCAP_GLOBAL_HEADER)
        current_file_size = len(PCAP_GLOBAL_HEADER)
    except Exception as e:
        print(f"[-] File Error: {e}")
        return

    total_captured = 0
    total_saved = 0
    buffer = b""

    try:
        while True:
            chunk = serial_connection.read(serial_connection.in_waiting or 2048)
            if not chunk:
                continue
            buffer += chunk

            while True:
                start_idx = buffer.find(MAGIC_HEADER)
                if start_idx == -1:
                    buffer = buffer[-len(MAGIC_HEADER):]
                    break

                if len(buffer) < start_idx + len(MAGIC_HEADER) + 2:
                    buffer = buffer[start_idx:]
                    break

                len_offset = start_idx + len(MAGIC_HEADER)
                pkt_len = struct.unpack('<H', buffer[len_offset:len_offset+2])[0]

                payload_start = len_offset + 2
                payload_end = payload_start + pkt_len
                if len(buffer) < payload_end:
                    buffer = buffer[start_idx:]
                    break

                packet_bytes = buffer[payload_start:payload_end]
                total_captured += 1
                buffer = buffer[payload_end:]

                should_save = False
                if target_bssid is None:
                    should_save = True
                else:
                    if len(packet_bytes) >= 24:
                        addr1 = parse_mac(packet=packet_bytes, offset=4)
                        addr2 = parse_mac(packet=packet_bytes, offset=10)
                        addr3 = parse_mac(packet=packet_bytes, offset=16)

                        if target_bssid in [addr1, addr2, addr3]:
                            should_save = True

                if should_save:
                    now = time.time()
                    seconds = int(now)
                    microseconds = int((now - seconds) * 1000000)
                    
                    packet_header_bytes = struct.pack('<IIII', seconds, microseconds, pkt_len, pkt_len)
                    bytes_to_write = packet_header_bytes + packet_bytes
                    packet_total_size = len(bytes_to_write)

                    if current_file_size + packet_total_size > MAX_FILE_SIZE:
                        pcap_file.close()
                        
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        name_part, ext_part = os.path.splitext(filename)
                        archive_name = f"{name_part}_{timestamp}{ext_part}"
                        
                        os.rename(filename, archive_name)
                        logging.info(f"[🔄] File limit hit. Archived log to {archive_name}")
                        print(f"\n[🔄] File limit reached. Archived log to: {archive_name}")
                        
                        pcap_file = open(filename, 'wb')
                        pcap_file.write(PCAP_GLOBAL_HEADER)
                        current_file_size = len(PCAP_GLOBAL_HEADER)

                    pcap_file.write(bytes_to_write)
                    current_file_size += packet_total_size
                    total_saved += 1
                    
                    if total_saved % 25 == 0:
                        pcap_file.flush()
                        print(f"Packets Written: {total_saved} (Parsed from ESP: {total_captured})", end='\r')

    except KeyboardInterrupt:
        print("\n[-] Capture terminated by user request.")
    finally:
        pcap_file.close()
        print(f"\n[+] Processing ended. Saved {total_saved} packets to disk.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ESP32-Pi Native Capture Script")
    parser.add_argument("-m", "--mode", choices=["scan", "all"], help="Automation Execution Mode", default=None)
    parser.add_argument("-b", "--bssid", help="Target BSSID", type=str, default=None)
    parser.add_argument("-c", "--channel", help="Static Target Channel", type=int, default=None)
    parser.add_argument("-o", "--output", help="Output filename base string", type=str, default="wifi_capture.pcap")
    parser.add_argument("-p", "--port", help="Serial connection device path", type=str, default="/dev/ttyUSB0")
    args = parser.parse_args()

    try:
        ser = serial.Serial(args.port, 921600, timeout=0.1)
        time.sleep(2)
        ser.reset_input_buffer()
    except Exception as e:
        print(f"[-] Failure opening serial hardware port {args.port}: {e}")
        sys.exit(1)
    
