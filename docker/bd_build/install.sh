#!/bin/bash
set -e
set -x
apt clean && rm -rf /var/lib/apt/lists/* && \
apt-get --allow-insecure-repositories update && DEBIAN_FRONTEND=noninteractive && \
apt install --allow-insecure-repositories -y --no-install-recommends build-essential libssl-dev libffi-dev python3-dev net-tools libsasl2-dev curl wget procps git libnss3-tools python3-pip && \
apt install --allow-insecure-repositories -y software-properties-common  && add-apt-repository -y ppa:deadsnakes/ppa && apt install -y python3.11 && \
rm /usr/bin/python && ln -s /usr/bin/python3.11 /usr/bin/python && \
python -m pip install virtualenv && \
cd /opt && \
git clone https://github.com/zinohome/yychat.git && \
cd /opt/yychat/ && \
git pull && \
virtualenv venv && \
. venv/bin/activate && \
pip install -r requirements.txt && \
cp /opt/yychat/docker/bd_build/50_start_h.sh /etc/my_init.d/50_start_h.sh &&
chmod 755 /etc/my_init.d/50_start_h.sh