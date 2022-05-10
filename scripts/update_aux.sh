aux_clients=("23" "98" "27" "77" "72" "93" "97" "74" "96" "21" "83")

aux_count=11

# start the aux clients
for i in $(seq 1 $aux_count)
do
    echo i
    quart=${aux_clients[$((i-1))]}
    ip=132.177.116.$quart
    ssh -t iol@$ip "cd cfnts/ && git reset --hard HEAD && rm tests/num_aux_clients && git pull"
    ssh -t iol@$ip 'bash' < ./scripts/rebuild.sh
    ssh -t iol@$ip "printf 0 > cfnts/tests/num_aux_clients"
done