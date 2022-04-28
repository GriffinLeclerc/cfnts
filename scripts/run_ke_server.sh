#!/bin/bash

memcached &

python3 scripts/fill-memcached.py

RUST_BACKTRACE=1 ./target/release/cfnts ke-server -f tests/nts-ke-config.yaml