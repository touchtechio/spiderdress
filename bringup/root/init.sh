#!/bin/sh

main() {
    #cleanup_processes
    
    #start edison as access point
    #systemctl start hostapd

    # setting up to connect to another hotspot
    #systemctl start wpa_supplicant
    
    #setting up bluetooth
    #rfkill unblock bluetooth
    
    /home/root/bin/gpio-i2c6-enable
    /home/root/bin/gpio-uart-enable
    #/home/root/bin/gpio-trigger-enable
    #/home/root/bin/gpio-trigger-twiddle
    /home/root/bin/wifi-adhoc-enable
}

main
exit 0
