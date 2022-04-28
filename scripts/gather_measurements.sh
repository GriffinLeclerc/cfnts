#!/bin/bash

echo $(whoami)
echo $HOSTNAME

cd /home/iol/cfnts 

min_clients=$(yq '.step_size' tests/experiment.yaml)

# start with the minimum number of clients
[ -s "tests/num_clients" ] || printf $min_clients > tests/num_clients

# exit if we've reached max_clients
num_clients=$(head -n 1 tests/num_clients)

max_clients=$(yq '.max_clients' tests/experiment.yaml)

if (( num_clients > max_clients )); then
    # Concluded, reset the experiment
    printf "" > tests/num_clients
    # and kill the arbiter
    ssh iol@132.177.116.25 sudo shutdown now
    exit 0
fi

# Run the experiment
./target/release/cfnts client -c tests/intermediate.pem nts-server.iol.unh.edu
