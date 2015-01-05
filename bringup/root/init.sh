#!/bin/sh

init_spider_py() {
    #IMPORTANT!!!!!!
    #Ensure that the correct leg position file is being used!!!
    cd /home/root/spider
    python spider.py #position_file_here &>>/dev/null
}

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

    #Start up CES interactions
    #init_spider_py
}

main
exit 0
