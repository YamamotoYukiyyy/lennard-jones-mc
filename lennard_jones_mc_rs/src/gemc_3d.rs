//! 3D Lennard-Jones Gibbs Ensemble Monte Carlo
//! Python lennard_jones_gemc_3d.py の Rust 移植

use rand::{Rng, SeedableRng};
use std::time::Instant;

use crate::lj_core::{self, NeighborState, Vec3};
/// GEMC の箱状態
pub struct BoxState {
    pub pos: Vec<Vec3>,
    pub box_size: f64,
    pub energy: f64,
    pub neighbor_state: Option<NeighborState>,
}

impl BoxState {
    pub fn volume(&self) -> f64 {
        self.box_size * self.box_size * self.box_size
    }

    pub fn n_particles(&self) -> usize {
        self.pos.len()
    }

    pub fn density(&self) -> f64 {
        if self.volume() > 0.0 {
            self.n_particles() as f64 / self.volume()
        } else {
            0.0
        }
    }
}

/// GEMC のパラメータ
#[derive(Clone)]
pub struct GemcParams {
    pub temperature: f64,
    pub n_total: usize,
    pub n_cycles: usize,
    pub delta_max: f64,
    pub delta_v_max: f64,
    pub total_density: f64,
    pub initial_particle_fraction_box1: f64,
    pub initial_volume_fraction_box1: f64,
    pub epsilon: f64,
    pub sigma: f64,
    pub displacement_tries_per_cycle: usize,
    pub transfer_tries_per_cycle: usize,
    pub use_cutoff: bool,
    pub cutoff_radius: Option<f64>,
    pub use_cell_list: bool,
    pub cell_size: Option<f64>,
    pub rng_seed: u64,
    /// 進捗表示間隔（0 のとき表示しない）
    pub progress_interval: usize,
    /// SI 単位変換用: σ [cm]（密度 g/cm³ 変換に使用）
    pub sigma_cm: Option<f64>,
    /// SI 単位変換用: 分子量 [g/mol]
    pub molar_mass_g: Option<f64>,
}

impl Default for GemcParams {
    fn default() -> Self {
        let n_total = 64;
        Self {
            temperature: 1.15,
            n_total,
            n_cycles: 2_000,
            delta_max: 0.25,
            delta_v_max: 8.0,
            total_density: 0.30,
            initial_particle_fraction_box1: 0.75,
            initial_volume_fraction_box1: 0.50,
            epsilon: 1.0,
            sigma: 1.0,
            displacement_tries_per_cycle: n_total,
            transfer_tries_per_cycle: (0.3 * n_total as f64).max(1.0) as usize,
            use_cutoff: false,
            cutoff_radius: None,
            use_cell_list: false,
            cell_size: None,
            rng_seed: 123,
            progress_interval: 0,
            sigma_cm: None,
            molar_mass_g: None,
        }
    }
}

/// LJ 無次元密度を g/cm³ に変換（アルゴン等）
pub fn rho_lj_to_g_cm3(rho_star: f64, sigma_cm: f64, molar_mass_g: f64) -> f64 {
    const N_AVOGADRO: f64 = 6.02214076e23;
    rho_star * (molar_mass_g / N_AVOGADRO) / (sigma_cm * sigma_cm * sigma_cm)
}

fn build_initial_boxes(
    params: &GemcParams,
    rng: &mut impl Rng,
) -> Result<(BoxState, BoxState), String> {
    let total_volume = params.n_total as f64 / params.total_density;
    let volume1 = params.initial_volume_fraction_box1 * total_volume;
    let volume2 = total_volume - volume1;
    let box_size1 = volume1.cbrt();
    let box_size2 = volume2.cbrt();

    if params.use_cutoff {
        if let Some(rc) = params.cutoff_radius {
            if rc >= 0.5 * box_size1.min(box_size2) {
                return Err("Initial GEMC boxes too small for cutoff radius".to_string());
            }
        }
    }

    let mut n1 = (params.initial_particle_fraction_box1 * params.n_total as f64).round() as usize;
    n1 = n1.max(1).min(params.n_total - 1);
    let n2 = params.n_total - n1;

    let min_distance = 0.9 * params.sigma;

    let pos1 = lj_core::init_positions(
        box_size1,
        n1,
        min_distance,
        rng,
        10_000,
        1_000,
    )?;
    let pos2 = lj_core::init_positions(
        box_size2,
        n2,
        min_distance,
        rng,
        10_000,
        1_000,
    )?;

    let ns1 = lj_core::build_neighbor_state(
        &pos1,
        box_size1,
        params.use_cutoff,
        params.cutoff_radius,
        params.use_cell_list,
        params.cell_size,
    )?;
    let ns2 = lj_core::build_neighbor_state(
        &pos2,
        box_size2,
        params.use_cutoff,
        params.cutoff_radius,
        params.use_cell_list,
        params.cell_size,
    )?;

    let e1 = lj_core::total_energy(&pos1, box_size1, params.epsilon, params.sigma, &ns1);
    let e2 = lj_core::total_energy(&pos2, box_size2, params.epsilon, params.sigma, &ns2);

    Ok((
        BoxState {
            pos: pos1,
            box_size: box_size1,
            energy: e1,
            neighbor_state: Some(ns1),
        },
        BoxState {
            pos: pos2,
            box_size: box_size2,
            energy: e2,
            neighbor_state: Some(ns2),
        },
    ))
}

fn displacement_move(
    box_state: &mut BoxState,
    params: &GemcParams,
    rng: &mut impl Rng,
) -> bool {
    if box_state.n_particles() == 0 {
        return false;
    }

    let idx = rng.gen_range(0..box_state.n_particles());
    let state = box_state.neighbor_state.as_ref().unwrap();
    let e_old = lj_core::calc_energy(
        &box_state.pos,
        idx,
        box_state.box_size,
        params.epsilon,
        params.sigma,
        state,
    );

    let delta: Vec3 = [
        rng.gen_range(-params.delta_max..=params.delta_max),
        rng.gen_range(-params.delta_max..=params.delta_max),
        rng.gen_range(-params.delta_max..=params.delta_max),
    ];
    let pos_old = box_state.pos[idx];
    box_state.pos[idx] = lj_core::wrap_positions(
        [
            box_state.pos[idx][0] + delta[0],
            box_state.pos[idx][1] + delta[1],
            box_state.pos[idx][2] + delta[2],
        ],
        box_state.box_size,
    );

    if let Some(ref mut ns) = box_state.neighbor_state {
        lj_core::update_neighbor_state_after_move(ns, idx, pos_old, box_state.pos[idx], box_state.box_size);
    }

    let state = box_state.neighbor_state.as_ref().unwrap();
    let e_new = lj_core::calc_energy(
        &box_state.pos,
        idx,
        box_state.box_size,
        params.epsilon,
        params.sigma,
        state,
    );
    let d_e = e_new - e_old;

    if d_e <= 0.0 || rng.gen::<f64>() < (-d_e / params.temperature).exp() {
        box_state.energy += d_e;
        return true;
    }

    box_state.pos[idx] = pos_old;
    if let Some(ref mut ns) = box_state.neighbor_state {
        lj_core::update_neighbor_state_after_move(ns, idx, box_state.pos[idx], pos_old, box_state.box_size);
    }
    false
}

fn volume_exchange_move(
    box1: &mut BoxState,
    box2: &mut BoxState,
    params: &GemcParams,
    rng: &mut impl Rng,
) -> bool {
    let v1_old = box1.volume();
    let v2_old = box2.volume();
    let d_v = rng.gen_range(-params.delta_v_max..=params.delta_v_max);
    let v1_new = v1_old + d_v;
    let v2_new = v2_old - d_v;

    let min_volume = (0.5 * params.sigma).powi(3);
    if v1_new <= min_volume || v2_new <= min_volume {
        return false;
    }

    let scale1 = (v1_new / v1_old).cbrt();
    let scale2 = (v2_new / v2_old).cbrt();

    let box_size1_new = box1.box_size * scale1;
    let box_size2_new = box2.box_size * scale2;
    let pos1_new: Vec<Vec3> = box1
        .pos
        .iter()
        .map(|p| lj_core::wrap_positions([p[0] * scale1, p[1] * scale1, p[2] * scale1], box_size1_new))
        .collect();
    let pos2_new: Vec<Vec3> = box2
        .pos
        .iter()
        .map(|p| lj_core::wrap_positions([p[0] * scale2, p[1] * scale2, p[2] * scale2], box_size2_new))
        .collect();

    if params.use_cutoff {
        if let Some(rc) = params.cutoff_radius {
            if rc >= 0.5 * box_size1_new.min(box_size2_new) {
                return false;
            }
        }
    }

    let ns1_new = match lj_core::build_neighbor_state(
        &pos1_new,
        box_size1_new,
        params.use_cutoff,
        params.cutoff_radius,
        params.use_cell_list,
        params.cell_size,
    ) {
        Ok(s) => s,
        Err(_) => return false,
    };
    let ns2_new = match lj_core::build_neighbor_state(
        &pos2_new,
        box_size2_new,
        params.use_cutoff,
        params.cutoff_radius,
        params.use_cell_list,
        params.cell_size,
    ) {
        Ok(s) => s,
        Err(_) => return false,
    };

    let e1_new = lj_core::total_energy(
        &pos1_new,
        box_size1_new,
        params.epsilon,
        params.sigma,
        &ns1_new,
    );
    let e2_new = lj_core::total_energy(
        &pos2_new,
        box_size2_new,
        params.epsilon,
        params.sigma,
        &ns2_new,
    );
    let d_e = (e1_new + e2_new) - (box1.energy + box2.energy);

    let ln_acc = -d_e / params.temperature
        + box1.n_particles() as f64 * (v1_new / v1_old).ln()
        + box2.n_particles() as f64 * (v2_new / v2_old).ln();

    if rng.gen::<f64>().ln() < ln_acc.min(0.0) {
        box1.pos = pos1_new;
        box2.pos = pos2_new;
        box1.box_size = box_size1_new;
        box2.box_size = box_size2_new;
        box1.energy = e1_new;
        box2.energy = e2_new;
        box1.neighbor_state = Some(ns1_new);
        box2.neighbor_state = Some(ns2_new);
        return true;
    }
    false
}

fn particle_transfer_move(
    source: &mut BoxState,
    dest: &mut BoxState,
    params: &GemcParams,
    rng: &mut impl Rng,
) -> bool {
    if source.n_particles() == 0 {
        return false;
    }

    let idx = rng.gen_range(0..source.n_particles());
    let candidate: Vec3 = [
        rng.gen_range(0.0..dest.box_size),
        rng.gen_range(0.0..dest.box_size),
        rng.gen_range(0.0..dest.box_size),
    ];

    let state_s = source.neighbor_state.as_ref().unwrap();
    let removal_energy = lj_core::calc_energy(
        &source.pos,
        idx,
        source.box_size,
        params.epsilon,
        params.sigma,
        state_s,
    );
    let state_d = dest.neighbor_state.as_ref().unwrap();
    let insert_energy = lj_core::insertion_energy(
        &dest.pos,
        candidate,
        dest.box_size,
        params.epsilon,
        params.sigma,
        state_d,
    );
    let d_e = insert_energy - removal_energy;

    let acc_ratio = (source.n_particles() as f64 * dest.volume())
        / ((dest.n_particles() + 1) as f64 * source.volume());
    let ln_acc = acc_ratio.ln() - d_e / params.temperature;

    if rng.gen::<f64>().ln() < ln_acc.min(0.0) {
        source.pos.remove(idx);
        dest.pos.push(candidate);

        source.energy -= removal_energy;
        dest.energy += insert_energy;

        source.neighbor_state = lj_core::rebuild_neighbor_state(
            source.neighbor_state.as_ref(),
            &source.pos,
            source.box_size,
        );
        dest.neighbor_state = lj_core::rebuild_neighbor_state(
            dest.neighbor_state.as_ref(),
            &dest.pos,
            dest.box_size,
        );
        return true;
    }
    false
}

/// GEMC 実行結果
pub struct GemcResult {
    pub box1: BoxState,
    pub box2: BoxState,
    pub n1_history: Vec<usize>,
    pub n2_history: Vec<usize>,
    pub rho1_history: Vec<f64>,
    pub rho2_history: Vec<f64>,
    pub v1_history: Vec<f64>,
    pub v2_history: Vec<f64>,
    pub e1_history: Vec<f64>,
    pub e2_history: Vec<f64>,
    pub move_counts: GemcMoveCounts,
    pub elapsed_secs: f64,
}

pub struct GemcMoveCounts {
    pub disp_accept: usize,
    pub disp_total: usize,
    pub vol_accept: usize,
    pub vol_total: usize,
    pub transfer_accept: usize,
    pub transfer_total: usize,
}

/// 生産相（equilibration_fraction 以降）の rho_liq, rho_vap 平均を返す
pub fn production_average_phase_density(
    result: &GemcResult,
    equilibration_fraction: f64,
) -> (f64, f64) {
    let n = result.rho1_history.len();
    let start = (n as f64 * equilibration_fraction) as usize;
    if start >= n {
        return (0.0, 0.0);
    }
    let mut sum_liq = 0.0;
    let mut sum_vap = 0.0;
    for i in start..n {
        let r1 = result.rho1_history[i];
        let r2 = result.rho2_history[i];
        sum_liq += r1.max(r2);
        sum_vap += r1.min(r2);
    }
    let count = (n - start) as f64;
    (sum_liq / count, sum_vap / count)
}

/// GEMC を実行
pub fn run_gemc(params: &GemcParams) -> Result<GemcResult, String> {
    let mut rng = rand::rngs::StdRng::seed_from_u64(params.rng_seed);

    let (mut box1, mut box2) = build_initial_boxes(params, &mut rng)?;

    let mut n1_history = Vec::with_capacity(params.n_cycles);
    let mut n2_history = Vec::with_capacity(params.n_cycles);
    let mut rho1_history = Vec::with_capacity(params.n_cycles);
    let mut rho2_history = Vec::with_capacity(params.n_cycles);
    let mut v1_history = Vec::with_capacity(params.n_cycles);
    let mut v2_history = Vec::with_capacity(params.n_cycles);
    let mut e1_history = Vec::with_capacity(params.n_cycles);
    let mut e2_history = Vec::with_capacity(params.n_cycles);

    let mut move_counts = GemcMoveCounts {
        disp_accept: 0,
        disp_total: 0,
        vol_accept: 0,
        vol_total: 0,
        transfer_accept: 0,
        transfer_total: 0,
    };

    let start = Instant::now();

    for cycle in 0..params.n_cycles {
        for _ in 0..params.displacement_tries_per_cycle {
            let target = if rng.gen::<f64>() < 0.5 {
                &mut box1
            } else {
                &mut box2
            };
            move_counts.disp_total += 1;
            if displacement_move(target, params, &mut rng) {
                move_counts.disp_accept += 1;
            }
        }

        move_counts.vol_total += 1;
        if volume_exchange_move(&mut box1, &mut box2, params, &mut rng) {
            move_counts.vol_accept += 1;
        }

        for _ in 0..params.transfer_tries_per_cycle {
            move_counts.transfer_total += 1;
            let accepted = if rng.gen::<f64>() < 0.5 {
                particle_transfer_move(&mut box1, &mut box2, params, &mut rng)
            } else {
                particle_transfer_move(&mut box2, &mut box1, params, &mut rng)
            };
            if accepted {
                move_counts.transfer_accept += 1;
            }
        }

        n1_history.push(box1.n_particles());
        n2_history.push(box2.n_particles());
        rho1_history.push(box1.density());
        rho2_history.push(box2.density());
        v1_history.push(box1.volume());
        v2_history.push(box2.volume());
        e1_history.push(box1.energy);
        e2_history.push(box2.energy);

        if params.progress_interval > 0 && cycle % params.progress_interval == 0 {
            let elapsed = start.elapsed().as_secs_f64();
            let rho_liq = box1.density().max(box2.density());
            let rho_vap = box1.density().min(box2.density());
            if let (Some(sigma_cm), Some(molar_mass)) = (params.sigma_cm, params.molar_mass_g) {
                println!(
                    "  cycle {}/{}, elapsed {:.1}s, rho_liq* = {:.3} ({:.3} g/cm³), rho_vap* = {:.3} ({:.3} g/cm³)",
                    cycle,
                    params.n_cycles,
                    elapsed,
                    rho_liq,
                    rho_lj_to_g_cm3(rho_liq, sigma_cm, molar_mass),
                    rho_vap,
                    rho_lj_to_g_cm3(rho_vap, sigma_cm, molar_mass)
                );
            } else {
                println!(
                    "  cycle {}/{}, elapsed {:.1}s, rho_liq* = {:.3}, rho_vap* = {:.3}",
                    cycle, params.n_cycles, elapsed, rho_liq, rho_vap
                );
            }
        }
    }

    let elapsed = start.elapsed();

    Ok(GemcResult {
        box1,
        box2,
        n1_history,
        n2_history,
        rho1_history,
        rho2_history,
        v1_history,
        v2_history,
        e1_history,
        e2_history,
        move_counts,
        elapsed_secs: elapsed.as_secs_f64(),
    })
}
