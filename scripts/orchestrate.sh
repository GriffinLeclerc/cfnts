s=nts-server.iol.unh.edu

while ! ping -c1 $s &>/dev/null
        do echo "Waiting"
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

c=132.177.116.19

while ! ping -c1 $c &>/dev/null
        do echo "Waiting"
done
echo "Client Online"

# Gather measurements
ssh -t iol@$s 'bash' < ./scripts/gather_measurments.sh



# pkill ./target/release/cfnts

ssh -t iol@$s sudo reboot
ssh -t iol@$c sudo reboot
