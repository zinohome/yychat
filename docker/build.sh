#!/bin/bash
IMGNAME=zinohome/yychat-openai
IMGVERSION=v0.0.1
docker build --no-cache -t $IMGNAME:$IMGVERSION .