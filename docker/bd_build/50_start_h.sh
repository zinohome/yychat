#!/bin/bash
cd /opt/yychat && \
nohup ./start_with_venv.sh >> /tmp/yychat.log 2>&1 &
