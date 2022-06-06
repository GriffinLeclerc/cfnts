# Augmented cfnts

[![CircleCI](https://circleci.com/gh/cloudflare/cfnts.svg?style=svg)](https://circleci.com/gh/cloudflare/cfnts)

cfnts is an implementation of the NTS protocol written in Rust. After careful study of CFNTS and its time transfer pro-cedures, key areas of operation in both the client and the server were identified and an experimental benchmarking suite was developed to quantify operational time of the NTS-KE and authenticated NTPv4. 

**Prereqs**:
rustc 1.47.0 (18bf6b4f0 2020-10-07)

**Building**:

We use cargo to build the software.`cargo build --release` will generate the necessary materials for running both the client and the server.

**Running Experimental Setup**
Three machines are required, the NTS Server, an NTS Client, and an NTS Arbiter. Auxillary clients may also be added to increase the load to the NTS Server. 

The NTS Server hosts both the NTS-KE and the NTP server instances. The NTS Client will issue NTS-KE and NTP requests to the server according to the configuration file. The NTS Arbiter orchestrates the experiment by driving the client(s) and the server. 

There are a number of configuration files that are utilized and should be customized to achieve desired results.

`tests/experiment.yaml` details most experiment configuration parameters. Detailed descriptions of each can be found in the file.

`nts-ke-config.yaml` is the NTS-KE server's configuration file and `ntp-config.yaml` is the NTP server's configuration file. `ntp-upstream-config.yaml` is not utilized in this project.

**DO NOT EDIT** `num-clients`, `num-aux-clients`, or `reqs-per-second` unless you are deeply familiar with their intended purpose, as they are automatically populated by the benchmarking quite to maintain state through power cycling.

In addition, the runtime scripts need to be updated to contain the IP addresses of each machine in the experiment setup.

These include `clear_results.sh`, `fetch_results.sh`, `gather_measurements.sh`, `orchestrate.sh`, `reboot_aux.sh`, and `update_aux.sh`.

Ensure the NTS Client and Server are online and reachable by the Arbiter and execute `./scripts/orchestrate.sh` on the Arbiter to gather results.

Upon completion of the experiment parameters, the NTS Arbiter will be rebooted and results are ready for collection and evaluation. Do so with `fetch_results.sh` and `plot.py`, ensuring the correct resultPath in `plot.py`.



A number of helpful scripts are also available.

`clear_results.sh` will remove all local results and reset the number of aux clients utilized.  

`reboot_aux.sh` will reboot all aux clients specified in the file.

`update_aux.sh` will cause all aux clients specified to pull the latest version of the Git repository and rebuild all binaries necessary for execution.


**Running default CFNTS**

Run the NTS client using `./target/release/cfnts client [--4 | --6] [-p <server-port>] [-c <trusted-cert>] [-n <other name>]  <server-hostname>`

Default port is `4460`. 

Using `-4` forces the use of ipv4 for all connections to the server, and using `-6` forces the use of ipv6. 
These two arguments are mutually exclusive. If neither of them is used, then the client will use whichever one
is supported by the server (preference for ipv6 if supported).

To run a server you will need a memcached compatible server, together with a script based on fill-memcached.py that will write
a new random key into /nts/nts-keys/ every hour and delete old ones. Then you can run the ntp server and the nts server.

This split and use of memcached exists to enable deployments where a small dedicated device serves NTP, while a bigger server carries
out the key exchange.

**Examples**:

1. `./target/release/cfnts client time.cloudflare.com`
2. `./target/release/cfnts client kong.rellim.com -p 123`