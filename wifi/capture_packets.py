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

script_pid = os.getpid()

# Standard PCAP Global Header (Link type 105 = LinkType IEEE 802.11)
PCAP_GLOBAL_HEADER = struct.pack('<IHHIIII', 0xa1b2c3d4, 2, 4, 0, 0, 65535, 105)
MAGIC_HEADER = b"START_PKT:"

# Fixed 'file' parameter to 'filename' to prevent crashes
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

def run_live_scan(serial_connection, target_bssid=None):
    """Hops channels 1-11 for 5 seconds to build a dynamic target map or locate a target."""
    if target_bssid:
        target_bssid = target_bssid.lower()
        print(f"[+] Automated Mode: Scanning channels for target BSSID [{target_bssid}]...")
        logging.info(f"Automated Mode: Scanning channels for target BSSID [{target_bssid}]...")
    else:
        print("\n[+] Interactive Mode: Scanning 2.4GHz spectrum for 5 seconds...")
        
    networks = {} # maps bssid -> (ssid, channel)

    start_scan = time.time()
    current_channel = 1
    last_hop = time.time()

    serial_connection.write(f"SET_CH:{current_channel}\n".encode())
    buffer = b""
    
    while time.time() - start_scan < 5.0:
        if time.time() - last_hop > 0.3:
            current_channel = (current_channel % 11) + 1
            serial_connection.write(f"SET_CH:{current_channel}\n".encode())
            last_hop = time.time()
        
        chunk = serial_connection.read(serial_connection.in_waiting or 512)
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
            payload_end = len_offset + 2 + pkt_len

            if len(buffer) < payload_end:
                buffer = buffer[start_idx:]
                break

            packet_bytes = buffer[len_offset+2:payload_end]
            buffer = buffer[payload_end:]

            if len(packet_bytes) >= 36 and packet_bytes[0] == 0x80:
                bssid = parse_mac(packet=packet_bytes, offset=16)
                if bssid and bssid not in networks:
                    ssid = parse_ssid(packet_bytes=packet_bytes)
                    networks[bssid] = (ssid, current_channel)

    # --- PIPELINE ROUTING ---
    
    # Path A: Headless Automation Mode (-m scan -b <MAC>)
    if target_bssid:
        if target_bssid in networks:
            ssid, chan = networks[target_bssid]
            print(f"[🚀] Auto-Discovery Success: Found '{ssid}' on Channel {chan}")
            logging.info(f"Auto-Discovery Success: Found '{ssid}' on Channel {chan}")
            return target_bssid, chan
        else:
            print(f"[-] Auto-Discovery Failure: Target {target_bssid} not detected in range.")
            logging.warning(f"Auto-Discovery Failure: Target {target_bssid} not detected in range.")
            return None, None

    # Path B: Interactive Fallback Mode (No flags passed)
    if not networks:
        print("[-] No networks detected. Try repositioning your hardware.")
        return None, None
        
    print("\n=== AVAILABLE Wi-Fi Networks ===")
    net_list = list(networks.items())
    for idx, (bssid, (ssid, chan)) in enumerate(net_list):
        print(f"[{idx}] SSID: {ssid:<25} BSSID: {bssid}  (CH: {chan})")
    
    while True:
        try:
            choice = input("Select an index (or 'q' to quit): ")
            if choice.lower() == 'q':
                return None, None
            choice_idx = int(choice)
            if 0 <= choice_idx < len(net_list):
                target_bssid, (ssid, chan) = net_list[choice_idx]
                return target_bssid, chan
        except ValueError:
            pass
        print("[!] Invalid selection.")


def capture_packets(serial_connection, base_pcap_name, target_bssid=None, channel=1):
    print("Listening for packets from ESP32... Press CTRL+C to stop.")  
    logging.info("Started listening for packets from ESP32 module for capture...")

    # Max file size configuration (50 MB in bytes)
    MAX_FILE_SIZE = 50 * 1024 * 1024 

    # String tracking logic for safe file definitions
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

    # Send the final chosen radio channel rule to the ESP32
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
                # FIX 1: Extracted single element using [0] to avoid tuple crashes
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
                        addr1 = parse_mac(packet=packet_bytes, offset=4) # destination
                        addr2 = parse_mac(packet=packet_bytes, offset=10) # source
                        addr3 = parse_mac(packet=packet_bytes, offset=16) # BSSID

                        if target_bssid in [addr1, addr2, addr3]:
                            should_save = True

                if should_save:
                    now = time.time()
                    seconds = int(now)
                    microseconds = int((now - seconds) * 1000000)
                    
                    packet_header_bytes = struct.pack('<IIII', seconds, microseconds, pkt_len, pkt_len)
                    bytes_to_write = packet_header_bytes + packet_bytes
                    packet_total_size = len(bytes_to_write)

                    # --- Live Log Rotation Engine Check ---
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
                    
                    # Flush every 25 packets to extend SD card life
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
    parser.add_argument("-c", "--channel", help="Static Target Channel", type=int, default=1)
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

    if args.mode == "all":
        capture_packets(ser, base_pcap_name=args.output, target_bssid=None, channel=args.channel)
        
    elif args.mode == "scan" and args.bssid:
        # Run automated background discovery pass
        target, channel = run_live_scan(ser, target_bssid=args.bssid)
        if target:
            # Target located -> Lock channel and capture target packets
            capture_packets(ser, base_pcap_name=args.output, target_bssid=target, channel=channel)
        else:
            # Fallback Safety: Target not found, drop back to safe Catch-All operations
            print(f"[!] Falling back to Catch-All Mode on Channel {args.channel}...")
            logging.info(f"Falling back to Catch-All Mode on Channel {args.channel}")
            capture_packets(ser, base_pcap_name=args.output, target_bssid=None, channel=args.channel)
            
    else:
        # Fallback to Menu UI if flags are omitted
        print("=== INTERACTIVE SELECTION ===")
        print(" Scan and lock onto a local network")
        print(" Blind Catch-All mode channel capture")
        user_choice = input("Select Option (1 or 2): ").strip()
        
        if user_choice == "1":
            target, channel = run_live_scan(ser)
            if target:
                capture_packets(ser, base_pcap_name=args.output, target_bssid=target, channel=channel)
        else:
            capture_packets(ser, base_pcap_name=args.output, target_bssid=None, channel=args.channel)
            
    ser.close()
