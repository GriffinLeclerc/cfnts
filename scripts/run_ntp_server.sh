#!/bin/bash
# cd /home/iol/cfnts
cd /home/griffin/dev/cfnts

echo $(whoami)
echo $HOSTNAME

./target/release/cfnts ntp-server -f tests/ntp-config.yaml