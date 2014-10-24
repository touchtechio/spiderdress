#!/bin/sh

init_uart() {
    echo 248 > /sys/class/gpio/export
    echo 249 > /sys/class/gpio/export
    echo 214 > /sys/class/gpio/export

    echo low > /sys/class/gpio/gpio248/direction
    echo high > /sys/class/gpio/gpio249/direction
    echo low > /sys/class/gpio/gpio214/direction
}

init_i2c6() {
    # NOTE: this will not all work when connected to breakout, because
    #       there is no tri-state. I think. TODO: check
    #author: David Pierret (davidx.pierret@intel.com)
    #this script initialyse Arduino board to use I2C6
    echo 28 > /sys/class/gpio/export
    echo 27 > /sys/class/gpio/export
    echo 204 > /sys/class/gpio/export
    echo 205 > /sys/class/gpio/export
    echo 236 > /sys/class/gpio/export
    echo 237 > /sys/class/gpio/export
    echo 14 > /sys/class/gpio/export
    echo 165 > /sys/class/gpio/export
    echo 212 > /sys/class/gpio/export
    echo 213 > /sys/class/gpio/export
    echo 214 > /sys/class/gpio/export
    echo low > /sys/class/gpio/gpio214/direction
    echo low > /sys/class/gpio/gpio204/direction
    echo low > /sys/class/gpio/gpio205/direction
    echo in > /sys/class/gpio/gpio14/direction
    echo in > /sys/class/gpio/gpio165/direction
    echo low > /sys/class/gpio/gpio236/direction
    echo low > /sys/class/gpio/gpio237/direction
    echo in > /sys/class/gpio/gpio212/direction
    echo in > /sys/class/gpio/gpio213/direction
    echo mode1 > /sys/kernel/debug/gpio_debug/gpio28/current_pinmux
    echo mode1 > /sys/kernel/debug/gpio_debug/gpio27/current_pinmux
    echo high > /sys/class/gpio/gpio214/direction
}

main() {
    #cleanup_processes
    #systemctl start wpa_supplicant
    #rfkill unblock bluetooth
    init_i2c6
    init_uart
}

main
exit 0
