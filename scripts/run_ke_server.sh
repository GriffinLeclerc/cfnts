#!/bin/bash


# cd /home/iol/cfnts
cd /home/griffin/dev/cfnts

memcached -u root &

echo $HOSTNAME

python3 scripts/fill-memcached.py

sudo RUST_BACKTRACE=1 ./target/release/cfnts ke-server -f tests/nts-ke-config.yaml