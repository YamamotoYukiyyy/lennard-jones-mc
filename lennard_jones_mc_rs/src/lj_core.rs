//! Lennard-Jones 12-6 ポテンシャルと周期境界条件の共通計算
//! Python lj_core.py の Rust 移植

use rand::Rng;
use std::collections::{HashMap, HashSet};

/// 3次元ベクトル
pub type Vec3 = [f64; 3];

/// 近傍探索状態（cutoff / cell list）
#[derive(Clone)]
pub struct NeighborState {
    pub use_cutoff: bool,
    pub cutoff_radius: Option<f64>,
    pub use_cell_list: bool,
    pub cell_size: Option<f64>,
    pub n_cells: Option<i32>,
    pub cells: Option<HashMap<(i32, i32, i32), Vec<usize>>>,
    pub particle_cells: Option<Vec<(i32, i32, i32)>>,
}

impl NeighborState {
    pub fn new(
        use_cutoff: bool,
        cutoff_radius: Option<f64>,
        use_cell_list: bool,
        cell_size: Option<f64>,
    ) -> Self {
        Self {
            use_cutoff,
            cutoff_radius,
            use_cell_list,
            cell_size,
            n_cells: None,
            cells: None,
            particle_cells: None,
        }
    }
}

/// Minimum Image Convention
#[inline]
pub fn minimum_image(delta: Vec3, box_size: f64) -> Vec3 {
    [
        delta[0] - box_size * (delta[0] / box_size).round(),
        delta[1] - box_size * (delta[1] / box_size).round(),
        delta[2] - box_size * (delta[2] / box_size).round(),
    ]
}

/// 周期境界で座標を箱内に折り返す
#[inline]
pub fn wrap_positions(pos: Vec3, box_size: f64) -> Vec3 {
    [
        pos[0].rem_euclid(box_size),
        pos[1].rem_euclid(box_size),
        pos[2].rem_euclid(box_size),
    ]
}

/// 2点間の差ベクトル（minimum image）
#[inline]
pub fn delta_minimum_image(a: Vec3, b: Vec3, box_size: f64) -> Vec3 {
    let d = [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
    minimum_image(d, box_size)
}

/// ベクトルのノルム
#[inline]
pub fn norm(v: Vec3) -> f64 {
    (v[0] * v[0] + v[1] * v[1] + v[2] * v[2]).sqrt()
}

/// Lennard-Jones 12-6 ペアエネルギー
#[inline]
pub fn lj_pair_energy(
    r: f64,
    epsilon: f64,
    sigma: f64,
    use_cutoff: bool,
    cutoff_radius: Option<f64>,
) -> f64 {
    if r < 1e-10 {
        return 0.0;
    }
    if use_cutoff {
        if let Some(rc) = cutoff_radius {
            if r >= rc {
                return 0.0;
            }
        }
    }
    let sr = sigma / r;
    let sr6 = sr * sr * sr * sr * sr * sr;
    let sr12 = sr6 * sr6;
    4.0 * epsilon * (sr12 - sr6)
}

fn cell_index(point: Vec3, box_size: f64, n_cells: i32) -> (i32, i32, i32) {
    let scale = n_cells as f64 / box_size;
    let ix = ((point[0] * scale).floor() as i32).rem_euclid(n_cells);
    let iy = ((point[1] * scale).floor() as i32).rem_euclid(n_cells);
    let iz = ((point[2] * scale).floor() as i32).rem_euclid(n_cells);
    (ix, iy, iz)
}

fn neighbor_cells(cell: (i32, i32, i32), n_cells: i32) -> Vec<(i32, i32, i32)> {
    let mut result = Vec::with_capacity(27);
    for dx in -1..=1 {
        for dy in -1..=1 {
            for dz in -1..=1 {
                result.push((
                    (cell.0 + dx).rem_euclid(n_cells),
                    (cell.1 + dy).rem_euclid(n_cells),
                    (cell.2 + dz).rem_euclid(n_cells),
                ));
            }
        }
    }
    result
}

/// cutoff / cell list の正規化
pub fn normalize_neighbor_options(
    box_size: f64,
    use_cutoff: bool,
    cutoff_radius: Option<f64>,
    use_cell_list: bool,
    cell_size: Option<f64>,
) -> Result<(bool, Option<f64>, bool, Option<f64>), String> {
    let effective_use_cutoff = use_cutoff;
    let mut effective_cutoff = cutoff_radius;
    let effective_use_cell_list = use_cutoff && use_cell_list;
    let mut effective_cell_size = cell_size;

    if effective_use_cutoff {
        let rc = effective_cutoff.ok_or("cutoff_radius must be provided when use_cutoff=true")?;
        if rc <= 0.0 {
            return Err(format!("cutoff_radius must be positive, got {}", rc));
        }
        if rc >= 0.5 * box_size {
            return Err(format!(
                "cutoff_radius must be smaller than half the box size. Got {}",
                rc
            ));
        }
    } else {
        effective_cutoff = None;
    }

    if effective_use_cell_list {
        if effective_cell_size.is_none() {
            effective_cell_size = effective_cutoff;
        }
        if effective_cell_size.map_or(true, |s| s <= 0.0) {
            return Err("cell_size must be positive".to_string());
        }
    } else {
        effective_cell_size = None;
    }

    Ok((effective_use_cutoff, effective_cutoff, effective_use_cell_list, effective_cell_size))
}

/// 近傍探索状態を構築
pub fn build_neighbor_state(
    pos: &[Vec3],
    box_size: f64,
    use_cutoff: bool,
    cutoff_radius: Option<f64>,
    use_cell_list: bool,
    cell_size: Option<f64>,
) -> Result<NeighborState, String> {
    let (_, eff_cutoff, eff_use_cl, eff_cell_size) =
        normalize_neighbor_options(box_size, use_cutoff, cutoff_radius, use_cell_list, cell_size)?;

    let mut state = NeighborState::new(use_cutoff, eff_cutoff, eff_use_cl, eff_cell_size);

    if !eff_use_cl {
        return Ok(state);
    }

    let cell_size_val = eff_cell_size.unwrap();
    let n_cells = (box_size / cell_size_val).floor().max(1.0) as i32;
    state.n_cells = Some(n_cells);
    state.cells = Some(HashMap::new());
    state.particle_cells = Some(Vec::with_capacity(pos.len()));

    for (idx, &point) in pos.iter().enumerate() {
        let cell = cell_index(point, box_size, n_cells);
        state.particle_cells.as_mut().unwrap().push(cell);
        state
            .cells
            .as_mut()
            .unwrap()
            .entry(cell)
            .or_default()
            .push(idx);
    }

    Ok(state)
}

/// 1粒子変位後の cell list 差分更新
pub fn update_neighbor_state_after_move(
    state: &mut NeighborState,
    idx: usize,
    old_pos: Vec3,
    new_pos: Vec3,
    box_size: f64,
) {
    if state.cells.is_none()
        || state.particle_cells.is_none()
        || state.n_cells.is_none()
    {
        return;
    }

    let n_cells = state.n_cells.unwrap();
    let old_cell = cell_index(old_pos, box_size, n_cells);
    let new_cell = cell_index(new_pos, box_size, n_cells);

    if old_cell == new_cell {
        return;
    }

    let cells = state.cells.as_mut().unwrap();
    if let Some(list) = cells.get_mut(&old_cell) {
        list.retain(|&i| i != idx);
        if list.is_empty() {
            cells.remove(&old_cell);
        }
    }
    cells.entry(new_cell).or_default().push(idx);
    state.particle_cells.as_mut().unwrap()[idx] = new_cell;
}

/// 同じ設定で近傍探索状態を再構築（粒子追加・削除後用）
pub fn rebuild_neighbor_state(
    state: Option<&NeighborState>,
    pos: &[Vec3],
    box_size: f64,
) -> Option<NeighborState> {
    let s = state?;
    build_neighbor_state(
        pos,
        box_size,
        s.use_cutoff,
        s.cutoff_radius,
        s.use_cell_list,
        s.cell_size,
    )
    .ok()
}

fn candidate_indices_for_particle(
    pos: &[Vec3],
    i: usize,
    _box_size: f64,
    state: &NeighborState,
) -> Vec<usize> {
    if state.cells.is_none()
        || state.particle_cells.is_none()
        || state.n_cells.is_none()
    {
        return (0..pos.len()).collect();
    }

    let cell = state.particle_cells.as_ref().unwrap()[i];
    let n_cells = state.n_cells.unwrap();
    let cells = state.cells.as_ref().unwrap();
    let mut seen = HashSet::new();
    for neighbor in neighbor_cells(cell, n_cells) {
        if let Some(list) = cells.get(&neighbor) {
            for &idx in list {
                seen.insert(idx);
            }
        }
    }
    seen.into_iter().collect()
}

fn candidate_indices_for_point(
    candidate: Vec3,
    pos: &[Vec3],
    box_size: f64,
    state: &NeighborState,
) -> Vec<usize> {
    if state.cells.is_none() || state.n_cells.is_none() {
        return (0..pos.len()).collect();
    }

    let n_cells = state.n_cells.unwrap();
    let cell = cell_index(candidate, box_size, n_cells);
    let cells = state.cells.as_ref().unwrap();
    let mut seen = HashSet::new();
    for neighbor in neighbor_cells(cell, n_cells) {
        if let Some(list) = cells.get(&neighbor) {
            for &idx in list {
                seen.insert(idx);
            }
        }
    }
    seen.into_iter().collect()
}

/// 粒子 i と他粒子の LJ 相互作用エネルギー
pub fn calc_energy(
    pos: &[Vec3],
    i: usize,
    box_size: f64,
    epsilon: f64,
    sigma: f64,
    state: &NeighborState,
) -> f64 {
    let use_cutoff = state.use_cutoff;
    let cutoff_radius = state.cutoff_radius;

    let mut energy = 0.0;
    for &j in &candidate_indices_for_particle(pos, i, box_size, state) {
        if i == j {
            continue;
        }
        let delta = delta_minimum_image(pos[i], pos[j], box_size);
        let r = norm(delta);
        energy += lj_pair_energy(r, epsilon, sigma, use_cutoff, cutoff_radius);
    }
    energy
}

/// 全粒子系の全エネルギー
pub fn total_energy(
    pos: &[Vec3],
    box_size: f64,
    epsilon: f64,
    sigma: f64,
    state: &NeighborState,
) -> f64 {
    let mut sum = 0.0;
    for i in 0..pos.len() {
        sum += calc_energy(pos, i, box_size, epsilon, sigma, state);
    }
    sum / 2.0
}

/// ランダム初期配置（min_distance 以上離して配置）
pub fn init_positions(
    box_size: f64,
    n_particles: usize,
    min_distance: f64,
    rng: &mut impl Rng,
    max_trials: usize,
    max_global_retries: usize,
) -> Result<Vec<Vec3>, String> {
    let min_distance_sq = min_distance * min_distance;

    for _ in 0..max_global_retries {
        let mut pos = Vec::with_capacity(n_particles);

        for idx in 0..n_particles {
            let mut placed = false;
            for _ in 0..max_trials {
                let candidate: Vec3 = [
                    rng.gen_range(0.0..box_size),
                    rng.gen_range(0.0..box_size),
                    rng.gen_range(0.0..box_size),
                ];

                if idx == 0 {
                    pos.push(candidate);
                    placed = true;
                    break;
                }

                let mut ok = true;
                for &p in &pos {
                    let delta = delta_minimum_image(candidate, p, box_size);
                    let r_sq = delta[0] * delta[0] + delta[1] * delta[1] + delta[2] * delta[2];
                    if r_sq < min_distance_sq {
                        ok = false;
                        break;
                    }
                }
                if ok {
                    pos.push(candidate);
                    placed = true;
                    break;
                }
            }
            if !placed {
                break;
            }
        }
        if pos.len() == n_particles {
            return Ok(pos);
        }
    }

    Err(format!(
        "Failed to place {} particles with min_distance={} in box_size={}",
        n_particles, min_distance, box_size
    ))
}

/// 候補位置に1粒子を挿入したときの相互作用エネルギー
pub fn insertion_energy(
    pos: &[Vec3],
    candidate: Vec3,
    box_size: f64,
    epsilon: f64,
    sigma: f64,
    state: &NeighborState,
) -> f64 {
    if pos.is_empty() {
        return 0.0;
    }

    let use_cutoff = state.use_cutoff;
    let cutoff_radius = state.cutoff_radius;

    let mut energy = 0.0;
    for &idx in &candidate_indices_for_point(candidate, pos, box_size, state) {
        let delta = delta_minimum_image(candidate, pos[idx], box_size);
        let r = norm(delta);
        energy += lj_pair_energy(r, epsilon, sigma, use_cutoff, cutoff_radius);
    }
    energy
}
