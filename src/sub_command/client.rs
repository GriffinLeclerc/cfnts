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
use rand_distr::{Distribution, Normal, NormalError};
use rand::thread_rng;
use std::time::Duration;
use std::sync::atomic::{AtomicI32, Ordering, AtomicUsize};
use threadpool::ThreadPool;

pub static TRUE_KE: std::sync::atomic::AtomicI32 = AtomicI32::new(0);
pub static TRUE_NTP: std::sync::atomic::AtomicI32 = AtomicI32::new(0);

pub static NUM_FAILURES: std::sync::atomic::AtomicI32 = AtomicI32::new(0);

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

    // Begin experiment augmentation

    let experiment_config = config::Config::builder()
            .add_source(config::File::with_name("tests/experiment.yaml")).build().expect("Unable to build ntp server config.");

    // Warm up the connection
    let warmup_runs = experiment_config.get_string("warmup_runs").unwrap().parse::<i32>().unwrap();
    
    let total_requests = experiment_config.get_string("total_requests").unwrap().parse::<i32>().unwrap();
    let exchanges_per_cookie = experiment_config.get_string("exchanges_per_cookie").unwrap().parse::<i32>().unwrap();
 
    let step_size = experiment_config.get_string("step_size").unwrap().parse::<i32>().unwrap();

    // let iterations_per_client = experiment_config.get_string("iterations_per_client").unwrap().parse::<i32>().unwrap();

    let mut file = File::open("tests/reqs_per_second").unwrap();
    let mut tmp = String::new();
    file.read_to_string(&mut tmp).expect("Unable to requests per second");
    let mut reqs_per_second = tmp.parse::<i32>().unwrap();

    let mut file = File::open("tests/num_clients").unwrap();
    let mut tmp = String::new();
    file.read_to_string(&mut tmp).expect("Unable to number of clients");
    let mut num_clients = tmp.parse::<i32>().unwrap();

    let aux_yaml = experiment_config.get_string("is_aux_client").unwrap();
    let is_aux_client = aux_yaml.contains("true"); 
    let aux_req_rate = experiment_config.get_string("aux_req_rate").unwrap().parse::<i32>().unwrap();

    let mut file = File::open("tests/num_aux_clients").unwrap();
    let mut tmp = String::new();
    file.read_to_string(&mut tmp).expect("Unable to aux client count");
    let num_aux_clients = tmp.parse::<i32>().unwrap();

    // aux clients get one thread
    if is_aux_client {
        num_clients = 1;
        reqs_per_second = aux_req_rate;
    }

    let inter_request_time: f64 = f64::from((1.0/reqs_per_second as f64) * 1000.0); // ms

    // keep it to one client for now
    // if inter_request_time < 4.0 {
    //     // increase the number of clients for the next run
    //     let mut file = File::create("tests/num_clients").unwrap();
    //     num_clients += step_size;
    //     file.write_all(num_clients.to_string().as_bytes()).expect("Unable to increase the number of clients");
    // }

    let additional_external_requests = aux_req_rate * num_aux_clients;

    println!("num_client threads {}", num_clients);
    println!("local reqs_per_second {}", reqs_per_second);
    println!("IRT {}", inter_request_time);

    println!("num_aux_clients {}", num_aux_clients);
    println!("Total requests per second {}", additional_external_requests + reqs_per_second);   

    // Begin experiment
    CLIENT_NTP_S.get().clone().unwrap().send(format!("{} total request(s) per second", (reqs_per_second * &exchanges_per_cookie) + (&additional_external_requests * &exchanges_per_cookie))).expect("unable to write to channel.");
    CLIENT_KE_S.get().clone().unwrap().send(format!("{} total request(s) per second", reqs_per_second + &additional_external_requests)).expect("unable to write to channel.");

    // let true_start = Instant::now();

    // Spawn a new thread from the pool for each inter request time
    let pool = ThreadPool::new(num_clients as usize);

    // aux clients should just serve the desired num reqs forever
    if is_aux_client {
        println!("This is an aux client.");
        loop {
            let host = host.clone();
            let port = port.clone();
            let trusted_cert = trusted_cert.clone();
            thread::sleep(Duration::from_millis(inter_request_time.round() as u64));

            // run a new client in each thread
            pool.execute(move || {
                let host = host.clone();
                let port = port.clone();
                let trusted_cert = trusted_cert.clone();
                let logger = slog_scope::logger();

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
                        return;
                        // process::exit(1)
                    }
                    Ok(_) => {}
                }

                let state = res.unwrap();
                //debug!(logger, "running UDP client with state {:x?}", state);
                let res = run_nts_ntp_client(&logger, state);
                match res {
                    Err(err) => {
                        eprintln!("failure of client: {}", err);
                        // process::exit(1)
                    }
                    Ok(_result) => {
                        // println!("stratum: {:}", _result.stratum);
                        // println!("offset: {:.6}", _result.time_diff);
                    }
                }
            });
        }

    }

    // Warmup if not an aux client
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
                NUM_FAILURES.fetch_add(1, Ordering::SeqCst);
                return;
            }
            Ok(_) => {}
        }
        let state = res.unwrap();
        //debug!(logger, "running UDP client with state {:x?}", state);
        let res = run_nts_ntp_client(&logger, state);
        match res {
            Err(err) => {
                eprintln!("failure of client: {}", err);
                NUM_FAILURES.fetch_add(1, Ordering::SeqCst);
            }
            Ok(_result) => {
                // println!("stratum: {:}", _result.stratum);
                // println!("offset: {:.6}", _result.time_diff);
            }
        }
    }

    // using multiple clients
    for _ in 0..total_requests {
        thread::sleep(Duration::from_millis(inter_request_time.round() as u64));

        for _ in 0..num_clients {
            // need to clone these for thread lifetimes
            let host = host.clone();
            let port = port.clone();
            let trusted_cert = trusted_cert.clone();

            // run a new client in each thread
            pool.execute(move || {
                // This should return the clone of `logger` in the main function.
                let logger = slog_scope::logger();

                // Begin load experiment
                let client_config = ClientConfig {
                    host: host.clone(),
                    port: port.clone(),
                    trusted_cert: trusted_cert.clone(),
                    use_ipv4: use_ipv4.clone(),
                };

                // KE
                let start = Instant::now();

                let ke_res = run_nts_ke_client(&logger, client_config);
                // TRUE_KE.fetch_add(1, Ordering::SeqCst);

                match ke_res {
                    Err(err) => {
                        eprintln!("failure of tls stage: {}", err);
                        NUM_FAILURES.fetch_add(1, Ordering::SeqCst);
                        return;
                    }
                    Ok(_) => {}
                }

                let state = ke_res.unwrap();

                let end = Instant::now();
                let time_meas = end - start;
                let time_meas_nanos = time_meas.as_nanos();

                CLIENT_KE_S.get().clone().unwrap().send(time_meas_nanos.to_string()).expect("unable to write to channel.");

                //debug!(logger, "running UDP client with state {:x?}", state);

                // NTP
                // allow for multiple time transfers per cookie
                for _ in 0..exchanges_per_cookie {
                    let start = Instant::now();

                    let res = run_nts_ntp_client(&logger, state.clone());
                    // TRUE_NTP.fetch_add(1, Ordering::SeqCst);

                    let end = Instant::now();
                    let time_meas = end - start;
                    let time_meas_nanos = time_meas.as_nanos();

                    CLIENT_NTP_S.get().clone().unwrap().send(time_meas_nanos.to_string()).expect("unable to write to channel.");

                    match res {
                        Err(err) => {
                            eprintln!("failure of client: {}", err);
                            NUM_FAILURES.fetch_add(1, Ordering::SeqCst);
                        }
                        Ok(_) => {
                            // no output, assume proper
                            // println!("stratum: {:}", _result.stratum);
                            // println!("offset: {:.6}", _result.time_diff);
                        }
                    }
                }
            
            });
        }

    };

    // wait for the clients
    pool.join();

    // let true_end = Instant::now();
    // let true_diff = ((true_end - true_start).as_millis() as f64) / 1000.0;

    // let true_ke_per_second = (TRUE_KE.load(Ordering::SeqCst) as f64) / true_diff;
    // CLIENT_KE_S.get().clone().unwrap().send(format!("TRUE REQS PER SECOND {}", true_ke_per_second)).expect("unable to write to channel.");

    // let true_ntp_per_second = (TRUE_NTP.load(Ordering::SeqCst) as f64) / true_diff;
    // CLIENT_NTP_S.get().clone().unwrap().send(format!("TRUE REQS PER SECOND {}", true_ntp_per_second)).expect("unable to write to channel.");

    // write the number of failures
    CLIENT_KE_S.get().clone().unwrap().send(format!("Errors: {}", NUM_FAILURES.load(Ordering::SeqCst))).expect("unable to write to channel.");
    CLIENT_NTP_S.get().clone().unwrap().send(format!("Errors: {}", NUM_FAILURES.load(Ordering::SeqCst))).expect("unable to write to channel.");

    // step
    let mut file = File::create("tests/reqs_per_second").unwrap();
    reqs_per_second += step_size;
    file.write_all(reqs_per_second.to_string().as_bytes()).expect("Unable to write next run");
}
