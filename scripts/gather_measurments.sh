#!/bin/bash
# for i in {1..30000}
# do
#    ./target/release/cfnts client -c tests/intermediate.pem nts-server.iol.unh.edu
# done

cargo build --release
./target/release/cfnts client -c tests/intermediate.pem nts-server.iol.unh.edu
