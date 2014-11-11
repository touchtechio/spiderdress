#!/bin/bash -e
d="`dirname \"$0\"`"
cd $d
source local.conf

scp -r -p ./support/python/lib/* root@$EDISON_SSH_HOST:/usr/lib/python2.7/site-packages/

ssh edison mkdir tmp

scp -r -p ./support/python/requests root@$EDISON_SSH_HOST:tmp/requests
ssh edison 'cd tmp/requests && python setup.py install && cd && rm -rf tmp/requests'

ssh root@$EDISON_SSH_HOST mkdir -p tmp
scp -r -p ./support/packages/* root@$EDISON_SSH_HOST:tmp/

cat <<EOF
TO FINALIZE: In ~/tmp on edison, install wwXX .ipk packages, e.g.:
   opkg install tmp/ww33/bash_4.3-r0_core2-32.ipk
   opkg install tmp/ww33/coreutils_8.22-r0_core2-32.ipk
   opkg install tmp/ww33/util-linux-bash-completion_2.24.1-r0_core2-32.ipk

These three example packages are the minimum recommended set.
EOF
