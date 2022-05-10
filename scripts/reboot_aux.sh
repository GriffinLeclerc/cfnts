aux_clients=("23" "98" "27" "77" "72" "93" "97" "74" "96" "21" "83")

aux_count=11

# start the aux clients
for i in $(seq 1 $aux_count)
do
    quart=${aux_clients[$((i-1))]}
    ip=132.177.116.$quart
    ssh -t iol@$ip sudo reboot
done