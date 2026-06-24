# Use
- First the wireless_start.sh script to start the scan_wifi.py and the capture_packets.py scripts
- Choose the network you want to test
- Once we have collected enough packets from the chosen network, we need to foreground capture_packets.py: `fg %{pid}` and then `CTRL+C`.
- Next, we want to use aircrack-ng: `aircrack-ng -w {wordlist} esp32_sniffed.pcap`
- If we need to crack a WPA 4-way handshake, we might want to use hashcat, specifically `hcxtools`
- Install hcxtools: `sudo apt install hcxtools`
- Convert capture file to hashcat's format: `hcxpcapngtool esp32_sniffed.pcap -o hashcat.txt`
- Crack the password, example: `hashcat -m 22000 hashcat.txt {wordlist}`




## Information and tips
The robot should be capable of capturing packets with no issue, however, the cracking process may require more processing power than the raspberry pi can handle, consider leaving the cracking to a more robust device that you can transfer capture to.
