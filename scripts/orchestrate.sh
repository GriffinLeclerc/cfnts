s=nts-server.iol.unh.edu
c=132.177.116.19

while true
do
    while ! ssh iol@$s 'echo "ping"'
    do
        sleep 1
        echo "Trying again..."
    done
    echo "Server Online"

    (
        # start the KE server
        ssh -t iol@$s 'bash' < ./scripts/run_ke_server.sh
    ) &
    disown %1

    # allow keys to populate
    sleep 0.5

    (
        # start the NTP server
        ssh -t iol@$s sudo 'bash' < ./scripts/run_ntp_server.sh
    ) &
    disown %1

    # allow ntp to start
    sleep 0.5

    aux_clients=("23" "98" "27" "77" "72")

    aux_count=$(head -n 1 tests/num_aux_clients)
    declare -i aux_count

    # start the aux clients
    for i in $(seq 1 aux_count)
        quart=${aux_clients[$((i-1))]}
        (
            ssh -t iol@132.177.116.$quart 'bash' < ./scripts/gather_measurements.sh
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

    ssh -t iol@$s sudo reboot

    for i in $(seq 1 aux_count)
        quart=${aux_clients[$((i-1))]}
        (
            ssh -t iol@132.177.116.$quart sudo reboot
        ) &
    done

    ssh -t iol@$c sudo reboot
done