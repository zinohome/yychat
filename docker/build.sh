#!/bin/bash
IMGNAME=zinohome/yychat-openai
IMGVERSION=v0.2.3
docker build --no-cache -t $IMGNAME:$IMGVERSION .