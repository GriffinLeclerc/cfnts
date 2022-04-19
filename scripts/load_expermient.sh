#!/bin/bash
minClients=1
maxClients=50

stepSize=1

numClients=$minClients

 
while [ $numClients -le $maxClients ]
do
    for f in client_nts_ke server_ntp_enc client_nts_ntp server_ke_create
    do
        echo "$numClients client(s)" >> "results/$f"
    done

	for (( k=1; k<=$numClients; k++ ))
    do
        ./target/release/cfnts client -c tests/intermediate.pem doctor.iol.unh.edu &
    done

    # Wait for all clients
    wait

    numClients=$((numClients+$stepSize))
done
