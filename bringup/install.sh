#!/bin/bash
d="`dirname \"$0\"`"
cd $d
source local.conf

# TODO: create backup if exists. Like mv?
scp -p ./system/root-init.service root@$EDISON_SSH_HOST:/etc/systemd/system/
scp -p ./system/wpa_supplicant.conf root@$EDISON_SSH_HOST:/etc/wpa_supplicant/
scp -p ./system/bash_completion root@$EDISON_SSH_HOST:/etc/bash_completion
ssh root@$EDISON_SSH_HOST mkdir -p /usr/local/bin
scp -p ./system/nano root@$EDISON_SSH_HOST:/usr/local/bin/nano

shopt -s dotglob # can also use globstar with '**'
scp -p -r ./root/* root@$EDISON_SSH_HOST:~/

on_remote() {
    ssh root@$EDISON_SSH_HOST $@
}

disable_service() {
    on_remote systemctl stop $1
    on_remote systemctl disable $1
    on_remote systemctl mask $1
}

#disable_service serial-getty@ttyMFD2.service
#disable_service pwr-button-handler.service
disable_service sketch_reset.service
disable_service xdk-daemon.service
disable_service rsmb.service
disable_service edison_config.service
disable_service clloader.service

on_remote systemctl stop root-init.service
on_remote systemctl enable root-init.service
on_remote systemctl start root-init.service

# Allow persistent processes
#
on_remote "grep -q '^KillMode' /lib/systemd/system/sshd@.service 2>/dev/null && \
    sed -i 's/^KillMode.*/KillMode=process/' /lib/systemd/system/sshd@.service || \
    echo 'KillMode=process' >> /lib/systemd/system/sshd@.service"
