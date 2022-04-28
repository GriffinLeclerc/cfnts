#!/bin/bash
min_clients=$(yq '.step_size' tests/experiment.yaml)

# start with the minimum number of clients
[ -s "tests/num_clients" ] || printf $min_clients > tests/num_clients

# exit if we've reached max_clients
num_clients=$(head -n 1 tests/num_clients)

max_clients=$(yq '.max_clients' tests/experiment.yaml)

if (( num_clients > max_clients )); then
    # Concluded
    exit 0
fi

# Run the experiment
./target/release/cfnts client -c tests/intermediate.pem nts-server.iol.unh.edu
