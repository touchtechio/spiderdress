#!/bin/sh

main() {
    #cleanup_processes
    
    #start edison as access point
    #systemctl start hostapd

    # setting up to connect to another hotspot
    #systemctl start wpa_supplicant
    
    #setting up bluetooth
    #rfkill unblock bluetooth
    
    /home/root/gpio-i2c6-enable
    /home/root/gpio-uart-enable
}

main
exit 0
