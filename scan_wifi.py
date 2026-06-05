#!/etc/bin/python

import subprocess


'''
To detect WiFi you need:
- sudo apt  install network-manager
'''


def scan_wifi_networks():
    try: # run nmcli command to list Wi-Fi networks
        cmd = ["nmcli", "-t", "-f", "SSID,BSSID,SIGNAL", "dev", "wifi", "list"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)

        #split output by lines
        lines = result.stdout.strip().split("\n")

        print(f"{'SSID':<30} {'BSSID (MAC)':<20} {'Signal Strength':<15}")
        print("-" * 65)

        for line in lines:
            if line: #nmcli fields are colon-separated
                fields = line.split(":")

                #handle cases where SSID contains a colon or is hidden
                if len(fields) >= 3:
                    signal = fields[-1]
                    bssid = ":".join(fields[-7:-1])
                    ssid = ":".join(fields[:-7]) if len(fields) > 3 else fields[0]
                
                if not ssid:
                    ssid = "[Hidden Network]"
                
                print(f"{ssid:<30} {bssid:<20} {signal:<15}")
    
    except subprocess.CalledProcessError as error:
        print(f"Error executing scan: {error.stderr}")
    except FileNotFoundError:
        print(f"Error: 'nmcli' command not found. Ensure NetworkManager is installed and running.")


if __name__ == _main__':
    scan_wifi_networks()
