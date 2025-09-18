#!/bin/bash
cd /opt/yychat && \
source .venv/bin/activate
nohup python app.py >> /tmp/yychat.log 2>&1 &
