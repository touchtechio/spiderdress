#!/bin/bash -e
d=$(dirname $(readlink -f $0))
cd $d
source local.conf

# copy opkgs from build dir
# svn/git up/down zip etc from external
# configs?

cp -arvfL /usr/lib/python2.7/dist-packages/serial ./support/python/lib/
cp -avfL /usr/share/bash-completion/bash_completion system/

wget https://github.com/defnull/bottle/raw/master/bottle.py -O ./support/python/lib/bottle.py
git clone https://github.com/kennethreitz/requests ./support/python/requests

# finally update zip file