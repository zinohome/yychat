#!/bin/bash
IMGNAME=zinohome/yychat-openai
IMGVERSION=v0.2.5
docker build --no-cache -t $IMGNAME:$IMGVERSION .