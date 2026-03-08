//! 3D Lennard-Jones MC / GEMC の実行バイナリ

use lennard_jones_mc_rs::{run_mc, run_gemc, McParams, GemcParams};

fn main() {
    println!("=== 3D Lennard-Jones Monte Carlo (Rust) ===\n");

    // 単箱 MC
    let mc_params = McParams {
        temperature: 1.2,
        n_steps: 10_000,
        delta_max: 0.25,
        box_size: 8.0,
        n_particles: 64,
        epsilon: 1.0,
        sigma: 1.0,
        use_cutoff: false,
        cutoff_radius: None,
        use_cell_list: false,
        cell_size: None,
        rng_seed: 42,
    };

    println!("単箱 MC: T={}, N={}, steps={}", mc_params.temperature, mc_params.n_particles, mc_params.n_steps);
    match run_mc(&mc_params) {
        Ok(result) => {
            println!("  最終エネルギー: {:.4}", result.energy_history.last().unwrap_or(&0.0));
            println!("  受理率: {:.2}% ({}/{})", 
                100.0 * result.n_accepted as f64 / result.n_steps as f64,
                result.n_accepted, result.n_steps);
            println!("  計算時間: {:.3} 秒", result.elapsed_secs);
        }
        Err(e) => println!("  エラー: {}", e),
    }

    println!();

    // GEMC
    let gemc_params = GemcParams {
        temperature: 1.15,
        n_total: 64,
        n_cycles: 2_000,
        delta_max: 0.25,
        delta_v_max: 8.0,
        total_density: 0.30,
        initial_particle_fraction_box1: 0.75,
        initial_volume_fraction_box1: 0.50,
        epsilon: 1.0,
        sigma: 1.0,
        displacement_tries_per_cycle: 64,
        transfer_tries_per_cycle: 19,
        use_cutoff: false,
        cutoff_radius: None,
        use_cell_list: false,
        cell_size: None,
        rng_seed: 123,
        progress_interval: 0,
        sigma_cm: None,
        molar_mass_g: None,
    };

    println!("GEMC: T={}, N_total={}, cycles={}", gemc_params.temperature, gemc_params.n_total, gemc_params.n_cycles);
    match run_gemc(&gemc_params) {
        Ok(result) => {
            println!("  最終状態:");
            println!("    Box 1: N={}, V={:.3}, rho={:.4}, E={:.4}",
                result.box1.n_particles(),
                result.box1.volume(),
                result.box1.density(),
                result.box1.energy);
            println!("    Box 2: N={}, V={:.3}, rho={:.4}, E={:.4}",
                result.box2.n_particles(),
                result.box2.volume(),
                result.box2.density(),
                result.box2.energy);
            let mc = &result.move_counts;
            println!("  Displacement acceptance: {:.2}%", 100.0 * mc.disp_accept as f64 / mc.disp_total as f64);
            println!("  Volume acceptance: {:.2}%", 100.0 * mc.vol_accept as f64 / mc.vol_total as f64);
            println!("  Transfer acceptance: {:.2}%", 100.0 * mc.transfer_accept as f64 / mc.transfer_total as f64);
            println!("  計算時間: {:.3} 秒", result.elapsed_secs);
        }
        Err(e) => println!("  エラー: {}", e),
    }

    println!("\n完了");
}
