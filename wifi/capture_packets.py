#!/etc/bin/python

'''
How to Use: This is automatically run by the wireless_start.sh script
To stop packet capture, foreground the process by 


Need: pip3 install pyserial scapy


'''

import serial
from scapy.all import RadioTap, binascii, wrpcap
import logging
import os

script_pid = os.getpid()


logging.basicConfig(file="packet_capture.log", filemode="a", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') 

print(f"\ncapture_packets.py started with Process ID: {script_pid}. Script will run in the background.\n" \
      f"To foreground type fg %{script_pid}\n\n")


def capture_packets(serial_connection, pcap_file):
    print("Listening for packets from ESP32... Press CTRL+C to stop.")  #Maybe this can run in background and will have another specified way to quit
    logging.info("Started listening for packets from ESP32 module for capture...")
    try:
        while True:
            line = serial_connection.readline().decode('utf-8', errors='ignore').strip()

            # Check if the incoming line contains our packet marker
            if line.startswith("START_PKT:"):
                hex_data = line.replace("START_PKT:", "")

                try:
                    #convert raw str hex back to bin bytes
                    packet_bytes = binascii.unhexlify(hex_data)

                    #wrap the raw 802.11 buytes in a basic RadioTap header for Wireshark
                    scapy_packet = RadioTap() / packet_bytes

                    # append the packet to your pcap file in rt
                    wrpcap(pcap_file, scapy_packet, append=True)
                    print(f"Captured packet! Size: {len(packet_bytes)} bytes saved.")
                    logging.info(f"Captured packet! Size: {len(packet_bytes)} bytes saved.")
                except Exception as error:
                    print(f"Error parsing packet string: {error}")
                    logging.error(f"Error parsing packet string: {error}")

    except KeyboardInterrupt:   #lets add a different way to exit this. I want to bg it
        print("\nStopping capture. Files are saved.")
        logging.info("\nStopping capture. Files are saved.")
        serial_connection.closed()


if __name__ == '__main__':
    # Open connection to the ESP32 likely /dev/ttyACM0 or /dev/ttyUSB0
    serial_connection = serial.Serial(port='/dev/ttyUSB0', baudrate=115200, timeout=1)
    pcap_file = "esp32_sniffed.pcap"
    capture_packets(serial_connection=serial_connection, pcap_file=pcap_file)
