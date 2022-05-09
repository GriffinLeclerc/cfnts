printf "" > results/client_nts_ke
printf "" > results/client_nts_ntp

printf "" > results/server_ke_create
printf "" > results/server_ntp_alone
printf "" > results/server_nts_auth

printf "" > tests/reqs_per_second
printf "" > tests/num_clients
printf "" > tests/num_aux_clients

ssh -t iol@132.177.116.25 "printf 0 > cfnts/tests/num_aux_clients"