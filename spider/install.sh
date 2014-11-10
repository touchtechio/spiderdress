#!/bin/sh
./deploy.sh
ssh root@edison 'ln -s /home/root/spider/edi2c /usr/lib/python2.7/site-packages/'