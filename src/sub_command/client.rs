// This file is part of cfnts.
// Copyright (c) 2019, Cloudflare. All rights reserved.
// See LICENSE for licensing information.

//! The client subcommand.

use slog::debug;

use std::fs;
use std::io::BufReader;
use std::process;
use std::thread::sleep;

use rustls::{
    internal::pemfile::certs,
    Certificate,
};

use crate::error::WrapError;
use crate::ntp::client::run_nts_ntp_client;
use crate::nts_ke::client::run_nts_ke_client;

use std::time::Instant;
use std::thread;

use crate::CLIENT_KE_S;
use crate::CLIENT_NTP_S;

use std::sync::{Arc, Barrier};
use std::convert::TryInto;
use std::fs::File;
use std::io::{Read, Write};

#[derive(Debug)]
pub struct ClientConfig {
    pub host: String,
    pub port: Option<String>,
    pub trusted_cert: Option<Certificate>,
    pub use_ipv4: Option<bool>
}

pub fn load_tls_certs(path: String) -> Result<Vec<Certificate>, config::ConfigError> {
    certs(&mut BufReader::new(fs::File::open(&path).wrap_err()?))
        .map_err(|()| config::ConfigError::Message(
            format!("could not load certificate from {}", &path)
        ))
}

/// The entry point of `client`.
pub fn run<'a>(matches: &clap::ArgMatches<'a>) {
    let host = matches
        .value_of("host")
        .map(String::from)
        .unwrap();
    let port = matches.value_of("port").map(String::from);
    let cert_file = matches.value_of("cert").map(String::from);

    // This should return the clone of `logger` in the main function.
    let logger = slog_scope::logger();

    // By default, use_ipv4 is None (no preference for using either ipv4 or ipv6
    // so client sniffs which one to use based on support)
    // However, if a user specifies the ipv4 flag, we set use_ipv4 = Some(true)
    // If they specify ipv6 (only one can be specified as they are mutually exclusive
    // args), set use_ipv4 = Some(false)
    let ipv4 = matches.is_present("ipv4");
    let mut use_ipv4 = None;
    if ipv4 {
        use_ipv4 = Some(true);
    } else {
        // Now need to check whether ipv6 is being used, since ipv4 has not been mandated
        if matches.is_present("ipv6") {
            use_ipv4 = Some(false);
        }
    }
    
    let mut trusted_cert = None;
    if let Some(file) = cert_file {
        if let Ok(certs) = load_tls_certs(file) {
            trusted_cert = Some(certs[0].clone());
        }
    }   

    let experiment_config = config::Config::builder()
            .add_source(config::File::with_name("tests/experiment.yaml")).build().expect("Unable to build ntp server config.");

    // Warm up the connection
    let warmup_runs = experiment_config.get_string("warmup_runs").unwrap().parse::<i32>().unwrap();

    for _ in 0..warmup_runs {
        let host = host.clone();
        let port = port.clone();
        let trusted_cert = trusted_cert.clone();

        let client_config = ClientConfig {
            host,
            port,
            trusted_cert,
            use_ipv4,
        };

        let res = run_nts_ke_client(&logger, client_config);

        match res {
            Err(err) => {
                eprintln!("failure of tls stage: {}", err);
                process::exit(1)
            }
            Ok(_) => {}
        }
        let state = res.unwrap();
        //debug!(logger, "running UDP client with state {:x?}", state);
        let res = run_nts_ntp_client(&logger, state);
        match res {
            Err(err) => {
                eprintln!("failure of client: {}", err);
                process::exit(1)
            }
            Ok(_result) => {
                // println!("stratum: {:}", _result.stratum);
                // println!("offset: {:.6}", _result.time_diff);
            }
        }
    }
    
    // Params for load testing
    // for a single client:
    //      let min_clients = 1;
    //      let max_clients = 1;
    //      let step_size = 1;

    let num_runs = experiment_config.get_string("num_runs").unwrap().parse::<i32>().unwrap();
    let exchanges_per_cookie = experiment_config.get_string("exchanges_per_cookie").unwrap().parse::<i32>().unwrap();
 
    let step_size = experiment_config.get_string("step_size").unwrap().parse::<i32>().unwrap();

    let mut file = File::open("tests/num_clients").unwrap();
    let mut tmp = String::new();
    file.read_to_string(&mut tmp).expect("Unable to read next number of clients");
    let mut num_clients = tmp.parse::<i32>().unwrap();

    // Begin experiment
    CLIENT_NTP_S.get().clone().unwrap().send(format!("{} client(s)", num_clients)).expect("unable to write to channel.");
    CLIENT_KE_S.get().clone().unwrap().send(format!("{} client(s)", num_clients)).expect("unable to write to channel.");

    // run multiple times
    for _ in 0..num_runs {
        // track the threads to join them later
        let mut join_handles: Vec<thread::JoinHandle<()>> = Vec::new();

        let barrier = Arc::new(Barrier::new(num_clients.try_into().unwrap()));

        // using multiple clients
        for _ in 0..num_clients {
            // need to clone these for thread lifetimes
            let host = host.clone();
            let port = port.clone();
            let trusted_cert = trusted_cert.clone();

            let my_barrier = Arc::clone(&barrier);

            // run a new client in each thread
            join_handles.push(std::thread::spawn(move || {

                // This should return the clone of `logger` in the main function.
                let logger = slog_scope::logger();

                let client_config = ClientConfig {
                    host,
                    port,
                    trusted_cert,
                    use_ipv4,
                };

                // wait on the barrier
                my_barrier.wait();

                // KE
                let start = Instant::now();

                let ke_res = run_nts_ke_client(&logger, client_config);

                match ke_res {
                    Err(err) => {
                        eprintln!("failure of tls stage: {}", err);
                        process::exit(1)
                    }
                    Ok(_) => {}
                }

                let state = ke_res.unwrap();

                let end = Instant::now();
                let time_meas_nanos = (end - start).as_nanos().to_string();

                CLIENT_KE_S.get().clone().unwrap().send(time_meas_nanos).expect("unable to write to channel.");

                //debug!(logger, "running UDP client with state {:x?}", state);

                // wait on the barrier
                my_barrier.wait();

                // NTP
                // allow for multiple time transfers per cookie
                for _ in 0..exchanges_per_cookie {
                    let start = Instant::now();

                    let res = run_nts_ntp_client(&logger, state.clone());

                    let end = Instant::now();
                    let time_meas_nanos = (end - start).as_nanos().to_string();

                    CLIENT_NTP_S.get().clone().unwrap().send(time_meas_nanos).expect("unable to write to channel.");

                    // match res {
                    //     Err(err) => {
                    //         eprintln!("failure of client: {}", err);
                    //         process::exit(1)
                    //     }
                    //     Ok(_) => {
                    //         // no prints, assume proper
                    //         // println!("stratum: {:}", _result.stratum);
                    //         // println!("offset: {:.6}", _result.time_diff);
                    //     }
                    // }
                }
            }));

        };

        // wait for the clients
        for handle in join_handles.into_iter() { 
            handle.join().unwrap();
        }
    }

    // step
    let mut file = File::create("tests/num_clients").unwrap();
    num_clients += step_size;
    file.write_all(num_clients.to_string().as_bytes()).expect("Unable to write next run");
    
}
