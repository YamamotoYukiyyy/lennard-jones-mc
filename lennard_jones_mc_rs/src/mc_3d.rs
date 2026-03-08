//! 3D Lennard-Jones 単箱 Monte Carlo
//! Python lennard_jones_mc_3d.py の Rust 移植

use rand::{Rng, SeedableRng};
use std::time::Instant;

use crate::lj_core::{self, NeighborState, Vec3};

/// 3D MC のパラメータ
#[derive(Clone)]
pub struct McParams {
    pub temperature: f64,
    pub n_steps: usize,
    pub delta_max: f64,
    pub box_size: f64,
    pub n_particles: usize,
    pub epsilon: f64,
    pub sigma: f64,
    pub use_cutoff: bool,
    pub cutoff_radius: Option<f64>,
    pub use_cell_list: bool,
    pub cell_size: Option<f64>,
    pub rng_seed: u64,
}

impl Default for McParams {
    fn default() -> Self {
        Self {
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
        }
    }
}

/// 1 MC ステップ（粒子変位）
fn mc_step(
    pos: &mut [Vec3],
    box_size: f64,
    temperature: f64,
    delta_max: f64,
    epsilon: f64,
    sigma: f64,
    state: &mut NeighborState,
    rng: &mut impl Rng,
) -> (f64, bool) {
    let n = pos.len();
    if n == 0 {
        return (0.0, false);
    }

    let idx = rng.gen_range(0..n);
    let e_old = lj_core::calc_energy(pos, idx, box_size, epsilon, sigma, state);

    let delta: Vec3 = [
        rng.gen_range(-delta_max..=delta_max),
        rng.gen_range(-delta_max..=delta_max),
        rng.gen_range(-delta_max..=delta_max),
    ];
    let pos_old = pos[idx];
    pos[idx] = lj_core::wrap_positions(
        [
            pos[idx][0] + delta[0],
            pos[idx][1] + delta[1],
            pos[idx][2] + delta[2],
        ],
        box_size,
    );
    lj_core::update_neighbor_state_after_move(state, idx, pos_old, pos[idx], box_size);

    let e_new = lj_core::calc_energy(pos, idx, box_size, epsilon, sigma, state);
    let d_e = e_new - e_old;

    if d_e <= 0.0 {
        return (d_e, true);
    }
    if rng.gen::<f64>() < (-d_e / temperature).exp() {
        return (d_e, true);
    }

    let pos_new = pos[idx];
    pos[idx] = pos_old;
    lj_core::update_neighbor_state_after_move(state, idx, pos_new, pos_old, box_size);
    (0.0, false)
}

/// 3D 単箱 MC を実行
pub fn run_mc(params: &McParams) -> Result<McResult, String> {
    let mut rng = rand::rngs::StdRng::seed_from_u64(params.rng_seed);

    let pos = lj_core::init_positions(
        params.box_size,
        params.n_particles,
        0.9 * params.sigma,
        &mut rng,
        10_000,
        1_000,
    )?;

    let mut state = lj_core::build_neighbor_state(
        &pos,
        params.box_size,
        params.use_cutoff,
        params.cutoff_radius,
        params.use_cell_list,
        params.cell_size,
    )?;

    let mut pos = pos;
    let mut current_energy = lj_core::total_energy(
        &pos,
        params.box_size,
        params.epsilon,
        params.sigma,
        &state,
    );

    let mut n_accepted = 0;
    let mut energy_history = Vec::with_capacity(params.n_steps);

    let start = Instant::now();

    for _ in 0..params.n_steps {
        let (d_e, accepted) = mc_step(
            &mut pos,
            params.box_size,
            params.temperature,
            params.delta_max,
            params.epsilon,
            params.sigma,
            &mut state,
            &mut rng,
        );
        if accepted {
            n_accepted += 1;
        }
        current_energy += d_e;
        energy_history.push(current_energy);
    }

    let elapsed = start.elapsed();

    Ok(McResult {
        final_pos: pos,
        energy_history,
        n_accepted,
        n_steps: params.n_steps,
        elapsed_secs: elapsed.as_secs_f64(),
    })
}

/// MC 実行結果
pub struct McResult {
    pub final_pos: Vec<Vec3>,
    pub energy_history: Vec<f64>,
    pub n_accepted: usize,
    pub n_steps: usize,
    pub elapsed_secs: f64,
}
