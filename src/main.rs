// This file is part of cfnts.
// Copyright (c) 2019, Cloudflare. All rights reserved.
// See LICENSE for licensing information.
#![feature(min_const_generics)]

extern crate lazy_static;
extern crate log;
extern crate prometheus;
extern crate slog;
extern crate slog_scope;
extern crate slog_stdlog;
extern crate sloggers;
extern crate time;

mod cfsock;
mod cmd;
mod cookie;
mod error;
mod key_rotator;
mod metrics;
mod ntp;
mod nts_ke;
mod sub_command;

use sloggers::terminal::{Destination, TerminalLoggerBuilder};
use sloggers::types::Severity;
use sloggers::Build;

use crossbeam_channel::unbounded;

use std::fs::OpenOptions;
use std::io::Write;
use std::{thread};

use once_cell::sync::OnceCell;

use std::process;

pub static CLIENT_KE_S: OnceCell<crossbeam_channel::Sender<String>> = OnceCell::new();
pub static CLIENT_NTP_S: OnceCell<crossbeam_channel::Sender<String>> = OnceCell::new();
pub static CLIENT_ERR_S: OnceCell<crossbeam_channel::Sender<String>> = OnceCell::new();

pub static SERVER_KE_S: OnceCell<crossbeam_channel::Sender<String>> = OnceCell::new();
pub static SERVER_NTP_S: OnceCell<crossbeam_channel::Sender<String>> = OnceCell::new();
pub static SERVER_NTS_S: OnceCell<crossbeam_channel::Sender<String>> = OnceCell::new();

/// Create a logger to be used throughout cfnts.
fn create_logger<'a>(matches: &clap::ArgMatches<'a>) -> slog::Logger {
    let mut builder = TerminalLoggerBuilder::new();

    // Default severity level is info.
    builder.level(Severity::Info);
    // Write all logs to stderr.
    builder.destination(Destination::Stdout); // FIXME write to stdErr

    // If in debug mode, change severity level to debug.
    if matches.is_present("debug") {
        builder.level(Severity::Debug);
    }

    // According to `sloggers-0.3.2` source code, the function doesn't return an error at all.
    // There should be no problem unwrapping here. It has a return type `Result` because it's a
    // signature for `sloggers::Build` trait.
    builder.build().expect("BUG: TerminalLoggerBuilder::build shouldn't return an error.")
}

/// The entry point of cfnts.
fn main() {
    // According to the documentation of `get_matches`, if the parsing fails, an error will be
    // displayed to the user and the process will exit with an error code.
    let matches = cmd::create_clap_command().get_matches();

    let logger = create_logger(&matches);

    // After calling this, slog_stdlog will forward all the `log` crate logging to
    // `slog_scope::logger()`.
    //
    // The returned error type is `SetLoggerError` which, according to the lib doc, will be
    // returned only when `set_logger` has been called already which should be our bug if it
    // has already been called.
    //
    slog_stdlog::init().expect("BUG: `set_logger` has already been called");

    // _scope_guard can be used to reset the global logger. You can do it by just dropping it.
    let _scope_guard = slog_scope::set_global_logger(logger.clone());

    if matches.subcommand.is_none() {
        eprintln!("please specify a valid subcommand: only client, ke-server, and ntp-server \
                   are supported.");
        process::exit(1);
    }

    if let Some(ke_server_matches) = matches.subcommand_matches("ke-server") {
        // Server KE
        // create the channel
        let (server_ke_s, server_ke_r) = unbounded();
        // populate the once cell
        SERVER_KE_S.set(server_ke_s).expect("unable to fill once cell.");
        // make a thread for writing client_ke meas
        thread::spawn(move || {
            let mut f = OpenOptions::new()
            .write(true)
            .append(true)
            .open("results/server_ke_create")
            .expect("Unable to create file");

            loop {
                // get and write measurements
                let value = server_ke_r.recv().unwrap();
                writeln!(f, "{}", value).expect("Unable to write file");
            }
        });

        sub_command::ke_server::run(ke_server_matches);
    }
    if let Some(ntp_server_matches) = matches.subcommand_matches("ntp-server") {
        // Server NTP
        // create the channel
        let (server_ntp_s, server_ntp_r) = unbounded();
        // populate the once cell
        SERVER_NTP_S.set(server_ntp_s).expect("unable to fill once cell.");
        // make a thread for writing client_ke meas
        thread::spawn(move || {
            let mut f = OpenOptions::new()
            .write(true)
            .append(true)
            .open("results/server_ntp_alone")
            .expect("Unable to create file");

            loop {
                // get and write measurements
                let value = server_ntp_r.recv().unwrap();
                writeln!(f, "{}", value).expect("Unable to write file");
            }
        });

        // Server NTS
        // create the channel
        let (server_nts_s, server_nts_r) = unbounded();
        // populate the once cell
        SERVER_NTS_S.set(server_nts_s).expect("unable to fill once cell.");
        // make a thread for writing client_ke meas
        thread::spawn(move || {
            let mut f = OpenOptions::new()
            .write(true)
            .append(true)
            .open("results/server_nts_auth")
            .expect("Unable to create file");

            loop {
                // get and write measurements
                let value = server_nts_r.recv().unwrap();
                writeln!(f, "{}", value).expect("Unable to write file");
            }
        });
        sub_command::ntp_server::run(ntp_server_matches);
    }
    if let Some(client_matches) = matches.subcommand_matches("client") {
        // Client KE
        // create the channel
        let (client_ke_s, client_ke_r) = unbounded();
        // populate the once cell
        CLIENT_KE_S.set(client_ke_s).expect("unable to fill once cell.");
        // make a thread for writing client_ke meas
        thread::spawn(move || {
            let mut f = OpenOptions::new()
            .write(true)
            .append(true)
            .open("results/client_nts_ke")
            .expect("Unable to create file");

            loop {
                // get and write measurements
                let value = client_ke_r.recv().unwrap();
                writeln!(f, "{}", value).expect("Unable to write file");
            }
        });

        // Client NTP
        // create the channel
        let (client_ntp_s, client_ntp_r) = unbounded();
        // populate the once cell
        CLIENT_NTP_S.set(client_ntp_s).expect("unable to fill once cell.");
        // make a thread for writing client_ke meas
        thread::spawn(move || {
            let mut f = OpenOptions::new()
            .write(true)
            .append(true)
            .open("results/client_nts_ntp")
            .expect("Unable to create file");

            loop {
                // get and write measurements
                let value = client_ntp_r.recv().unwrap();
                writeln!(f, "{}", value).expect("Unable to write file");
            }
        });

        // Client errors
        // create the channel
        let (client_err_s, client_err_r) = unbounded();
        // populate the once cell
        CLIENT_ERR_S.set(client_err_s).expect("unable to fill once cell.");
        // make a thread for writing client_ke meas
        thread::spawn(move || {
            let mut f = OpenOptions::new()
            .write(true)
            .append(true)
            .open("results/client_err")
            .expect("Unable to create file");

            loop {
                // get and write measurements
                let value = client_err_r.recv().unwrap();
                writeln!(f, "{}", value).expect("Unable to write file");
            }
        });

        sub_command::client::run(client_matches);
    }
}
