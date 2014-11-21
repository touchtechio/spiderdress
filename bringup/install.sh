#!/bin/bash
#
# Fashion Edison bringup installer: see https://confluence.ndg.intel.com/display/SPID/How-to%3A+Bring+up+an+Edison

d="`dirname \"$0\"`"
cd $d
source local.conf

# TODO: create backup if exists. Like mv?
scp -p ./system/root-init.service root@$EDISON_SSH_HOST:/etc/systemd/system/
scp -p ./system/sshd.socket root@$EDISON_SSH_HOST:/lib/systemd/system/
scp -p ./system/wpa_supplicant.conf root@$EDISON_SSH_HOST:/etc/wpa_supplicant/
scp -p ./system/bash_completion root@$EDISON_SSH_HOST:/etc/bash_completion
ssh root@$EDISON_SSH_HOST mkdir -p /usr/local/bin
scp -p ./system/nano root@$EDISON_SSH_HOST:/usr/local/bin/nano
scp -p ./system/batctl root@$EDISON_SSH_HOST:/usr/local/sbin/
scp -p ./system/hosts root@$EDISON_SSH_HOST:/etc/hosts

shopt -s dotglob # can also use globstar with '**'
scp -p -r ./root/* root@$EDISON_SSH_HOST:~/

on_remote() {
    ssh root@$EDISON_SSH_HOST $@
}

echo "~/id:"
read nid
echo "$nid" > nid.temp
echo "ft$nid" > hostname.temp
scp -p hostname.temp root@$EDISON_SSH_HOST:/etc/hostname
rm hostname.temp
scp -p nid.temp root@$EDISON_SSH_HOST:~/id
rm nid.temp


disable_service() {
    on_remote systemctl stop $1
    on_remote systemctl disable $1
    on_remote systemctl mask $1
}

#disable_service serial-getty@ttyMFD2.service
#disable_service pwr-button-handler.service
disable_service sketch_reset.service 2>/dev/null
disable_service xdk-daemon.service 2>/dev/null
disable_service rsmb.service 2>/dev/null
disable_service edison_config.service 2>/dev/null
disable_service clloader.service 2>/dev/null

on_remote systemctl stop root-init.service 2>/dev/null
on_remote systemctl enable root-init.service
on_remote systemctl start root-init.service

$d/install-software.sh

# Allow persistent processes
#
on_remote "grep -q '^KillMode' /lib/systemd/system/sshd@.service 2>/dev/null && \
    sed -i 's/^KillMode.*/KillMode=process/' /lib/systemd/system/sshd@.service || \
    echo 'KillMode=process' >> /lib/systemd/system/sshd@.service"

on_remote 'echo root:noside | chpasswd'
