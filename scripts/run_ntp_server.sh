#!/bin/bash
cd /home/iol/cfnts

echo $HOSTNAME

./target/release/cfnts ntp-server -f tests/ntp-config.yaml