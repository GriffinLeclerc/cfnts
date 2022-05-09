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

# start with the minimum number of clients
[ -s "tests/num_aux_clients" ] || printf "0" > tests/num_aux_clients

# stop the experiment at 500 reqs per second
line=$(head -n 1 tests/reqs_per_second)
declare -i line

if [[ $line -gt 500 ]]
then
    aux_count=$(head -n 1 tests/num_aux_clients)
    declare -i aux_count

    if [[ $aux_count == 5 ]]
    then
        # stop the arbiter
        ssh -t iol@132.177.116.25 sudo reboot
    fi

    printf $(($aux_count+1)) > tests/num_aux_clients
    # tell the arbiter to start an(other) aux client
    ssh -t iol@132.177.116.25 "printf $(($aux_count+1)) > cfnts/tests/num_aux_clients"

    # reset our count
    printf "" > tests/reqs_per_second

fi


# Run the experiment
./target/release/cfnts client -c tests/intermediate.pem nts-server.iol.unh.edu
