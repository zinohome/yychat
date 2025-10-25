#!/bin/bash
IMGNAME=zinohome/yychat
IMGVERSION=v0.3.7
docker build --no-cache -t $IMGNAME:$IMGVERSION .