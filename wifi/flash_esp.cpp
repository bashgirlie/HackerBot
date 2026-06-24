#include "esp_wifi.h"

int currentChannel = 1;
String serialBuffer = "";

void sniffer_callback(void* buf, wifi_promiscuous_pkt_type_t type) {
    wifi_promiscuous_pkt_t *pkt = (wifi_promiscuous_pkt_t*)buf;
    uint16_t len = pkt->rx_ctrl.sig_len;
    
    Serial.print("START_PKT:");
    Serial.write((uint8_t*)&len, 2);
    Serial.write(pkt->buf, len);
}

void setup() {
    Serial.begin(921600);
    delay(1000);

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&cfg);
    esp_wifi_set_storage(WIFI_STORAGE_RAM);
    esp_wifi_set_mode(WIFI_MODE_STA);
    esp_wifi_start();

    esp_wifi_set_promiscuous(true);
    esp_wifi_set_promiscuous_rx_cb(&sniffer_callback);
    esp_wifi_set_channel(currentChannel, WIFI_SECOND_CHAN_NONE);
}

void loop() {
    // Check if the Raspberry Pi sent a channel change command
    while (Serial.available() > 0) {
        char c = Serial.read();
        if (c == '\n') {
            if (serialBuffer.startsWith("SET_CH:")) {
                int newChannel = serialBuffer.substring(7).toInt();
                if (newChannel >= 1 && newChannel <= 14) {
                    currentChannel = newChannel;
                    esp_wifi_set_channel(currentChannel, WIFI_SECOND_CHAN_NONE);
                }
            }
            serialBuffer = ""; // Clear buffer for next command
        } else {
            serialBuffer += c;
        }
    }
}
