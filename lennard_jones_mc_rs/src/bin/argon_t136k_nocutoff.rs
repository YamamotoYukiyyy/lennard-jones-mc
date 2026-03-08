//! T=136 K, cutoff なしのテスト実行

use lennard_jones_mc_rs::{run_gemc, rho_lj_to_g_cm3, GemcParams};
use std::fs::File;
use std::io::Write;

const ARGON_EPSILON_K: f64 = 114.5;
const ARGON_SIGMA_CM: f64 = 3.374e-8;
const ARGON_MOLAR_MASS: f64 = 39.948;

fn main() {
    let t_k = 136.0;
    let t_star = t_k / ARGON_EPSILON_K;

    let params = GemcParams {
        temperature: t_star,
        n_total: 500,
        n_cycles: 10_000,
        delta_max: 0.25,
        delta_v_max: 8.0,
        total_density: 0.30,
        initial_particle_fraction_box1: 0.70,
        initial_volume_fraction_box1: 0.50,
        epsilon: 1.0,
        sigma: 1.0,
        displacement_tries_per_cycle: 500,
        transfer_tries_per_cycle: 150,
        use_cutoff: false,
        cutoff_radius: None,
        use_cell_list: false,
        cell_size: None,
        rng_seed: 123,
        progress_interval: 1000,
        sigma_cm: Some(ARGON_SIGMA_CM),
        molar_mass_g: Some(ARGON_MOLAR_MASS),
    };

    println!("=== Argon GEMC T=136 K, cutoff なし === ");
    println!("  N=500, cycles=10000, T*={:.6}\n", t_star);

    match run_gemc(&params) {
        Ok(result) => {
            let rho_liq = result.rho1_history.last().unwrap().max(*result.rho2_history.last().unwrap());
            let rho_vap = result.rho1_history.last().unwrap().min(*result.rho2_history.last().unwrap());
            let mc = &result.move_counts;

            println!("\n最終状態:");
            println!("  rho_liq* = {:.6} ({:.6} g/cm³)", rho_liq, rho_lj_to_g_cm3(rho_liq, ARGON_SIGMA_CM, ARGON_MOLAR_MASS));
            println!("  rho_vap* = {:.6} ({:.6} g/cm³)", rho_vap, rho_lj_to_g_cm3(rho_vap, ARGON_SIGMA_CM, ARGON_MOLAR_MASS));
            println!("受理率: disp={:.4}, vol={:.4}, transfer={:.4}",
                mc.disp_accept as f64 / mc.disp_total as f64,
                mc.vol_accept as f64 / mc.vol_total as f64,
                mc.transfer_accept as f64 / mc.transfer_total as f64);
            println!("計算時間: {:.3} 秒", result.elapsed_secs);

            let csv_path = "argon_gemc_T136K_nocutoff_density_history.csv";
            if let Ok(mut f) = File::create(csv_path) {
                let _ = writeln!(f, "cycle,rho1,rho2,rho_liq,rho_vap,n1,n2,v1,v2,e1,e2");
                for i in 0..result.rho1_history.len() {
                    let r1 = result.rho1_history[i];
                    let r2 = result.rho2_history[i];
                    let rl = r1.max(r2);
                    let rv = r1.min(r2);
                    let _ = writeln!(f, "{},{:.16},{:.16},{:.16},{:.16},{},{},{:.16},{:.16},{:.16},{:.16}",
                        i + 1, r1, r2, rl, rv, result.n1_history[i], result.n2_history[i],
                        result.v1_history[i], result.v2_history[i], result.e1_history[i], result.e2_history[i]);
                }
                println!("保存: {}", csv_path);
            }

            let json_path = "argon_gemc_T136K_nocutoff_summary.json";
            if let Ok(mut f) = File::create(json_path) {
                let _ = writeln!(f, "{{");
                let _ = writeln!(f, r#"  "mode": {{ "use_cutoff": false, "use_cell_list": false }},"#);
                let _ = writeln!(f, r#"  "temperature_reduced": {}, "temperature_K": {},"#, t_star, t_k);
                let _ = writeln!(f, r#"  "N_total": {}, "cycles": {},"#, params.n_total, params.n_cycles);
                let _ = writeln!(f, r#"  "elapsed_s": {},"#, result.elapsed_secs);
                let _ = writeln!(f, r#"  "final_box1": {{ "N": {}, "V": {}, "rho": {}, "E": {} }},"#,
                    result.box1.n_particles(), result.box1.volume(), result.box1.density(), result.box1.energy);
                let _ = writeln!(f, r#"  "final_box2": {{ "N": {}, "V": {}, "rho": {}, "E": {} }},"#,
                    result.box2.n_particles(), result.box2.volume(), result.box2.density(), result.box2.energy);
                let _ = writeln!(f, r#"  "final_phase_density": {{ "rho_liq": {}, "rho_vap": {} }},"#,
                    rho_liq, rho_vap);
                let _ = writeln!(f, r#"  "move_acceptance": {{ "displacement": {}, "volume": {}, "transfer": {} }}"#,
                    mc.disp_accept as f64 / mc.disp_total as f64,
                    mc.vol_accept as f64 / mc.vol_total as f64,
                    mc.transfer_accept as f64 / mc.transfer_total as f64);
                let _ = writeln!(f, "}}");
                println!("保存: {}", json_path);
            }
        }
        Err(e) => println!("エラー: {}", e),
    }
}
