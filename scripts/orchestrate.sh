s=doctor.iol.unh.edu
c=132.177.116.19
server_uname="griffin"

while true
do
    while ! ssh $server_uname@$s 'echo "ping"'
    do
        sleep 1
        echo "Trying again..."
    done
    echo "Server Online"

    (
        # start the KE server
        ssh -t $server_uname@$s 'bash' < ./scripts/run_ke_server.sh
    ) &

    # allow keys to populate
    sleep 2

    (
        # start the NTP server
        ssh -t $server_uname@$s sudo 'bash' < ./scripts/run_ntp_server.sh
    ) &

    # allow ntp to start
    sleep 1

    # start with the minimum number of aux clients
    [ -s "tests/num_aux_clients" ] || printf "0" > tests/num_aux_clients

    aux_clients=("23" "98" "27" "77" "72" "93" "97" "74" "96" "21" "83" "26" "90" "85" "24")

    aux_count=$(head -n 1 tests/num_aux_clients)
    declare -i aux_count

    # start the aux clients
    for i in $(seq 1 $aux_count)
    do
        quart=${aux_clients[$((i-1))]}
        ip=132.177.116.$quart
        
        while ! ssh iol@$ip 'echo "ping"'
        do
            sleep 1
            echo "Waiting for aux client..."
        done

        (
            ssh -t iol@$ip 'bash' < ./scripts/gather_measurements.sh
        ) &
    done

    # allow aux clients to start
    sleep 1

    while ! ssh iol@$c 'echo "ping"'
    do
        sleep 1
        echo "Trying again..."
    done
    echo "Client Online"

    # Gather measurements
    ssh -t iol@$c 'bash' < ./scripts/gather_measurements.sh

    # pkill ./target/release/cfnts

    ssh -t $server_uname@$s sudo reboot

    for i in $(seq 1 $aux_count)
    do
        quart=${aux_clients[$((i-1))]}
        (
            ssh -t iol@132.177.116.$quart sudo reboot
        ) &
    done

    ssh -t iol@$c sudo reboot
done