//! ベンチマーク用: N, cycles, T を CLI で指定し、JSON で elapsed_s と rho_liq を出力

use lennard_jones_mc_rs::{production_average_phase_density, rho_lj_to_g_cm3, run_gemc, GemcParams};
use std::env;

const ARGON_EPSILON_K: f64 = 114.5;
const ARGON_SIGMA_CM: f64 = 3.374e-8;
const ARGON_MOLAR_MASS: f64 = 39.948;
const EQUILIBRATION_FRACTION: f64 = 0.3;

fn parse_arg(name: &str, default: &str) -> String {
    let args: Vec<String> = env::args().collect();
    for i in 0..args.len().saturating_sub(1) {
        if args[i] == name {
            return args[i + 1].clone();
        }
    }
    default.to_string()
}

fn main() {
    let n: usize = parse_arg("--n", "100").parse().unwrap_or(100);
    let cycles: usize = parse_arg("--cycles", "40000").parse().unwrap_or(40000);
    let t_k: f64 = parse_arg("--t-k", "114").parse().unwrap_or(114.0);
    let t_star = t_k / ARGON_EPSILON_K;

    let disp_tries = n;
    let transfer_tries = (0.3 * n as f64).max(1.0) as usize;

    let params = GemcParams {
        temperature: t_star,
        n_total: n,
        n_cycles: cycles,
        delta_max: 0.25,
        delta_v_max: 8.0,
        total_density: 0.30,
        initial_particle_fraction_box1: 0.70,
        initial_volume_fraction_box1: 0.50,
        epsilon: 1.0,
        sigma: 1.0,
        displacement_tries_per_cycle: disp_tries,
        transfer_tries_per_cycle: transfer_tries,
        use_cutoff: false,
        cutoff_radius: None,
        use_cell_list: false,
        cell_size: None,
        rng_seed: 123,
        progress_interval: 0,
        sigma_cm: Some(ARGON_SIGMA_CM),
        molar_mass_g: Some(ARGON_MOLAR_MASS),
    };

    match run_gemc(&params) {
        Ok(result) => {
            let (rho_liq_avg, _rho_vap_avg) =
                production_average_phase_density(&result, EQUILIBRATION_FRACTION);
            let rho_liq_g = rho_lj_to_g_cm3(rho_liq_avg, ARGON_SIGMA_CM, ARGON_MOLAR_MASS);
            println!(
                r#"{{"elapsed_s":{},"rho_liq":{}}}"#,
                result.elapsed_secs, rho_liq_g
            );
        }
        Err(e) => {
            eprintln!("エラー: {}", e);
            std::process::exit(1);
        }
    }
}
