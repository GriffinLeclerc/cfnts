// This file is part of cfnts.
// Copyright (c) 2019, Cloudflare. All rights reserved.
// See LICENSE for licensing information.

//! The client subcommand.

use slog::debug;

use std::fs;
use std::io::BufReader;
use std::process;

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

use crate::SERVER_KE_S;
use crate::SERVER_NTP_S;

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

    // Params for load testing
    // for a single client:
    //      let min_clients = 1;
    //      let max_clients = 1;
    //      let step_size = 1;

    let min_clients = 1;
    let max_clients = 1;
    let step_size = 1;

    let mut num_clients = min_clients;

    while num_clients <= max_clients {

        SERVER_NTP_S.get().clone().unwrap().send(format!("{} client(s)", num_clients)).expect("unable to write to channel.");
        SERVER_KE_S.get().clone().unwrap().send(format!("{} client(s)", num_clients)).expect("unable to write to channel.");

        CLIENT_NTP_S.get().clone().unwrap().send(format!("{} client(s)", num_clients)).expect("unable to write to channel.");
        CLIENT_KE_S.get().clone().unwrap().send(format!("{} client(s)", num_clients)).expect("unable to write to channel.");

        println!("{} client(s)", num_clients);

        // track the threads to join them later
        let mut join_handles: Vec<thread::JoinHandle<()>> = Vec::new();

        for _ in 0..num_clients {
            // run a new client in each thread

            let host = host.clone();
            let port = port.clone();
            let trusted_cert = trusted_cert.clone();

            join_handles.push(std::thread::spawn(move || {

                // This should return the clone of `logger` in the main function.
                let logger = slog_scope::logger();

                let client_config = ClientConfig {
                    host,
                    port,
                    trusted_cert,
                    use_ipv4,
                };

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

                debug!(logger, "running UDP client with state {:x?}", state);

                // NTP
                let start = Instant::now();

                let res = run_nts_ntp_client(&logger, state.clone());

                let end = Instant::now();
                let time_meas_nanos = (end - start).as_nanos().to_string();

                CLIENT_NTP_S.get().clone().unwrap().send(time_meas_nanos).expect("unable to write to channel.");


                match res {
                    Err(err) => {
                        eprintln!("failure of client: {}", err);
                        process::exit(1)
                    }
                    Ok(result) => {
                        println!("stratum: {:}", result.stratum);
                        println!("offset: {:.6}", result.time_diff);
                    }
                }
            }));

        };

        // wait for the clients
        for handle in join_handles.into_iter() { 
            handle.join().unwrap();
        }
        
        // step
        num_clients += step_size;
    }


    // Gather multiple measurements using the same key

    // for _ in 1..30000 {
    //     let res = run_nts_ntp_client(&logger, state.clone());
    //     match res {
    //         Err(err) => {
    //             eprintln!("failure of client: {}", err);
    //             process::exit(1)
    //         }
    //         Ok(result) => {
    //             println!("stratum: {:}", result.stratum);
    //             println!("offset: {:.6}", result.time_diff);
    //         }
    //     }
    // }



}
