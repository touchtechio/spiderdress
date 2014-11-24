#!/bin/bash -e
d="`dirname \"$0\"`"
cd $d
source local.conf

scp -r -p ./support/python/lib/* root@$EDISON_SSH_HOST:/usr/lib/python2.7/site-packages/

ssh root@$EDISON_SSH_HOST mkdir -p tmp/requests/

scp -r -p ./support/python/requests/* root@$EDISON_SSH_HOST:tmp/requests/
ssh root@$EDISON_SSH_HOST 'cd tmp/requests && python setup.py install && cd && rm -rf tmp/requests'
