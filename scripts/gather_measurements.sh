#!/bin/bash

echo $(whoami)
echo $HOSTNAME

cd /home/iol/cfnts 

min_reqs=$(yq '.step_size' tests/experiment.yaml)
min_clients=$(yq '.starting_num_clients' tests/experiment.yaml)

# start with the minimum number of requests
[ -s "tests/reqs_per_second" ] || printf $min_reqs > tests/reqs_per_second

# start with the minimum number of clients
[ -s "tests/num_clients" ] || printf $min_clients > tests/num_clients

# stop the experiment at 500 reqs per second
line=$(head -n 1 tests/reqs_per_second)
declare -i line

if [[ $line -ge 500 ]]
then
    # stop the arbiter
    ssh -t iol@132.177.116.25 sudo reboot
fi


# Run the experiment
./target/release/cfnts client -c tests/intermediate.pem nts-server.iol.unh.edu
