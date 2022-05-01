#!/bin/bash

echo $(whoami)
echo $HOSTNAME

cd /home/iol/cfnts 

min_reqs=$(yq '.step_size' tests/experiment.yaml)

# start with the minimum number of requests
[ -s "tests/reqs_per_second" ] || printf $min_reqs > tests/reqs_per_second

# Run the experiment
./target/release/cfnts client -c tests/intermediate.pem nts-server.iol.unh.edu
