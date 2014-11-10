#!/bin/sh
rsync -av -e "ssh -oUser=root" . edison:~/spider
