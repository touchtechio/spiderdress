#!/bin/sh

main() {
    #cleanup_processes
    
    #start edison as access point
    #systemctl start hostapd

    # setting up to connect to another hotspot
    #systemctl start wpa_supplicant
    
    #setting up bluetooth
    #rfkill unblock bluetooth
    
    # else where??
    gpio_init_i2c6
    gpio_init_uart
}

main
exit 0
