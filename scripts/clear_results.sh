printf "" > results/client_nts_ke
printf "" > results/client_nts_ntp
printf "" > results/client_err

printf "" > results/server_ke_create
printf "" > results/server_ntp_alone
printf "" > results/server_nts_auth

min_reqs=$(yq '.step_size' tests/experiment.yaml)
min_clients=$(yq '.starting_num_clients' tests/experiment.yaml)

# start with the minimum number of requests
[ -s "tests/reqs_per_second" ] || printf $min_reqs > tests/reqs_per_second

# start with the minimum number of clients
[ -s "tests/num_clients" ] || printf $min_clients > tests/num_clients

# start with the minimum number of aux clients
[ -s "tests/num_aux_clients" ] || printf "0" > tests/num_aux_clients

# reset the orcestrator
# ssh -t iol@132.177.116.25 "printf 0 > cfnts/tests/num_aux_clients"
