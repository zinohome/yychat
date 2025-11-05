#!/bin/bash
IMGNAME=zinohome/yychat
IMGVERSION=v0.4.6.2
docker build --no-cache -t $IMGNAME:$IMGVERSION .