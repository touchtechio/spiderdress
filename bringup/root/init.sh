#!/bin/sh

main() {
    #cleanup_processes
    #systemctl start wpa_supplicant
    #rfkill unblock bluetooth
    gpio_init_i2c6
    gpio_init_uart
}

main
exit 0
