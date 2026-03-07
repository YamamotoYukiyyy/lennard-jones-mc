from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import product

import numpy as np


@dataclass
class NeighborState:
    use_cutoff: bool
    cutoff_radius: float | None
    use_cell_list: bool
    cell_size: float | None
    n_cells: int | None = None
    cells: dict[tuple[int, ...], list[int]] | None = None
    particle_cells: list[tuple[int, ...]] | None = None


def validate_common_parameters(
    *,
    temperature: float,
    n_particles: int,
    n_steps: int,
    delta_max: float,
    box_size: float,
    epsilon: float,
    sigma: float,
) -> None:
    """単箱 MC / GEMC で共通の主要パラメータを検証する。"""
    if temperature <= 0:
        raise ValueError(f"T must be positive, got {temperature}")
    if n_particles <= 0:
        raise ValueError(f"N must be positive, got {n_particles}")
    if n_steps <= 0:
        raise ValueError(f"N_STEPS must be positive, got {n_steps}")
    if delta_max <= 0:
        raise ValueError(f"DELTA_MAX must be positive, got {delta_max}")
    if box_size <= 0:
        raise ValueError(f"BOX_SIZE must be positive, got {box_size}")
    if epsilon < 0:
        raise ValueError(f"EPSILON must be non-negative, got {epsilon}")
    if sigma <= 0:
        raise ValueError(f"SIGMA must be positive, got {sigma}")


def exclusion_volume_per_particle(min_distance: float, dim: int) -> float:
    """初期配置チェックに使う 1 粒子あたりの排他体積を返す。"""
    radius = min_distance / 2.0
    if dim == 2:
        return math.pi * radius * radius
    if dim == 3:
        return (4.0 / 3.0) * math.pi * radius**3
    raise ValueError(f"Unsupported dimension: {dim}")


def validate_initial_density(
    *,
    n_particles: int,
    box_size: float,
    min_distance: float,
    dim: int,
    packing_limit: float = 0.8,
) -> None:
    """ランダム初期配置が極端に高密度でないかを確認する。"""
    required_measure = n_particles * exclusion_volume_per_particle(min_distance, dim)
    available_measure = box_size**dim
    if required_measure > packing_limit * available_measure:
        measure_name = "area" if dim == 2 else "volume"
        raise ValueError(
            f"Density too high: N={n_particles} particles with min_distance={min_distance:.3f} "
            f"require {measure_name} ~{required_measure:.3f}, but box has {available_measure:.3f}. "
            "Increase BOX_SIZE or decrease N."
        )


def normalize_neighbor_options(
    *,
    box_size: float,
    use_cutoff: bool,
    cutoff_radius: float | None,
    use_cell_list: bool,
    cell_size: float | None,
) -> tuple[bool, float | None, bool, float | None]:
    """cutoff と cell list の有効設定を正規化する。"""
    effective_use_cutoff = bool(use_cutoff)
    effective_cutoff = cutoff_radius
    effective_use_cell_list = bool(use_cell_list and use_cutoff)
    effective_cell_size = cell_size

    if effective_use_cutoff:
        if effective_cutoff is None:
            raise ValueError("cutoff_radius must be provided when use_cutoff=True.")
        if effective_cutoff <= 0:
            raise ValueError(f"cutoff_radius must be positive, got {effective_cutoff}")
        if effective_cutoff >= 0.5 * box_size:
            raise ValueError(
                f"cutoff_radius must be smaller than half the box size. "
                f"Got cutoff_radius={effective_cutoff}, box_size={box_size}."
            )
    else:
        effective_cutoff = None

    if effective_use_cell_list:
        if effective_cell_size is None:
            effective_cell_size = effective_cutoff
        if effective_cell_size is None or effective_cell_size <= 0:
            raise ValueError(f"cell_size must be positive, got {effective_cell_size}")
    else:
        effective_cell_size = None

    return effective_use_cutoff, effective_cutoff, effective_use_cell_list, effective_cell_size


def minimum_image(delta: np.ndarray, box_size: float) -> np.ndarray:
    """Minimum Image Convention を適用した差ベクトルを返す。"""
    return delta - box_size * np.round(delta / box_size)


def wrap_positions(pos: np.ndarray, box_size: float) -> np.ndarray:
    """周期境界条件で座標を箱内に折り返す。"""
    return pos % box_size


def init_positions(
    box_size: float,
    n_particles: int,
    min_distance: float,
    rng: np.random.Generator,
    *,
    dim: int,
    max_trials: int = 10_000,
    max_global_retries: int = 1_000,
) -> np.ndarray:
    """粒子をランダムに初期配置し、詰まった場合は全体を作り直す。"""
    min_distance_sq = min_distance**2

    for _ in range(max_global_retries):
        pos = np.empty((n_particles, dim), dtype=float)

        for idx in range(n_particles):
            for _ in range(max_trials):
                candidate = rng.uniform(0.0, box_size, size=dim)
                if idx == 0:
                    pos[idx] = candidate
                    break

                delta = candidate - pos[:idx]
                delta = minimum_image(delta, box_size)
                distances_sq = np.sum(delta * delta, axis=1)
                if np.all(distances_sq >= min_distance_sq):
                    pos[idx] = candidate
                    break
            else:
                break
        else:
            return pos

    raise ValueError(
        f"Failed to place {n_particles} particles with min_distance={min_distance:.3f} "
        f"in box_size={box_size} after {max_global_retries} attempts. "
        "Density may be too high."
    )


def _cell_index(point: np.ndarray, box_size: float, n_cells: int) -> tuple[int, ...]:
    scaled = np.floor((point / box_size) * n_cells).astype(int) % n_cells
    return tuple(int(x) for x in scaled)


def build_neighbor_state(
    pos: np.ndarray,
    box_size: float,
    *,
    use_cutoff: bool = False,
    cutoff_radius: float | None = None,
    use_cell_list: bool = False,
    cell_size: float | None = None,
) -> NeighborState:
    """cutoff / cell list 設定に応じた近傍探索状態を構築する。"""
    effective_use_cutoff, effective_cutoff, effective_use_cell_list, effective_cell_size = normalize_neighbor_options(
        box_size=box_size,
        use_cutoff=use_cutoff,
        cutoff_radius=cutoff_radius,
        use_cell_list=use_cell_list,
        cell_size=cell_size,
    )

    state = NeighborState(
        use_cutoff=effective_use_cutoff,
        cutoff_radius=effective_cutoff,
        use_cell_list=effective_use_cell_list,
        cell_size=effective_cell_size,
    )

    if not effective_use_cell_list:
        return state

    assert effective_cell_size is not None
    n_cells = max(1, int(box_size / effective_cell_size))
    state.n_cells = n_cells
    state.cells = {}
    state.particle_cells = []

    for idx, point in enumerate(pos):
        cell = _cell_index(point, box_size, n_cells)
        state.particle_cells.append(cell)
        state.cells.setdefault(cell, []).append(idx)

    return state


def rebuild_neighbor_state(state: NeighborState | None, pos: np.ndarray, box_size: float) -> NeighborState | None:
    """同じ設定のまま近傍探索状態を再構築する。"""
    if state is None:
        return None
    return build_neighbor_state(
        pos,
        box_size,
        use_cutoff=state.use_cutoff,
        cutoff_radius=state.cutoff_radius,
        use_cell_list=state.use_cell_list,
        cell_size=state.cell_size,
    )


def update_neighbor_state_after_move(
    state: NeighborState | None,
    idx: int,
    old_pos: np.ndarray,
    new_pos: np.ndarray,
    box_size: float,
) -> None:
    """1 粒子変位後に cell list のみを差分更新する。"""
    if state is None or not state.use_cell_list or state.cells is None or state.particle_cells is None or state.n_cells is None:
        return

    old_cell = _cell_index(old_pos, box_size, state.n_cells)
    new_cell = _cell_index(new_pos, box_size, state.n_cells)
    if old_cell == new_cell:
        return

    state.cells[old_cell].remove(idx)
    if not state.cells[old_cell]:
        del state.cells[old_cell]
    state.cells.setdefault(new_cell, []).append(idx)
    state.particle_cells[idx] = new_cell


def _neighbor_cells(cell: tuple[int, ...], n_cells: int) -> list[tuple[int, ...]]:
    neighbors: set[tuple[int, ...]] = set()
    for offset in product([-1, 0, 1], repeat=len(cell)):
        neighbors.add(tuple((cell[d] + offset[d]) % n_cells for d in range(len(cell))))
    return list(neighbors)


def _candidate_indices_for_particle(
    pos: np.ndarray,
    i: int,
    box_size: float,
    neighbor_state: NeighborState | None,
) -> list[int]:
    if neighbor_state is None or not neighbor_state.use_cell_list or neighbor_state.cells is None or neighbor_state.particle_cells is None or neighbor_state.n_cells is None:
        return list(range(len(pos)))

    cell = neighbor_state.particle_cells[i]
    candidates: list[int] = []
    for neighbor in _neighbor_cells(cell, neighbor_state.n_cells):
        candidates.extend(neighbor_state.cells.get(neighbor, []))
    return candidates


def _candidate_indices_for_point(
    candidate: np.ndarray,
    pos: np.ndarray,
    box_size: float,
    neighbor_state: NeighborState | None,
) -> list[int]:
    if neighbor_state is None or not neighbor_state.use_cell_list or neighbor_state.cells is None or neighbor_state.n_cells is None:
        return list(range(len(pos)))

    cell = _cell_index(candidate, box_size, neighbor_state.n_cells)
    candidates: list[int] = []
    for neighbor in _neighbor_cells(cell, neighbor_state.n_cells):
        candidates.extend(neighbor_state.cells.get(neighbor, []))
    return candidates


def lj_pair_energy(
    r: float,
    epsilon: float,
    sigma: float,
    *,
    use_cutoff: bool = False,
    cutoff_radius: float | None = None,
) -> float:
    """Lennard-Jones 12-6 ポテンシャル。"""
    if r < 1e-10:
        return 0.0
    if use_cutoff and cutoff_radius is not None and r >= cutoff_radius:
        return 0.0
    sr = sigma / r
    sr6 = sr**6
    sr12 = sr6**2
    return 4.0 * epsilon * (sr12 - sr6)


def calc_energy(
    pos: np.ndarray,
    i: int,
    box_size: float,
    epsilon: float,
    sigma: float,
    *,
    neighbor_state: NeighborState | None = None,
) -> float:
    """粒子 i と他粒子の LJ 相互作用エネルギー総和を返す。"""
    energy = 0.0

    for j in _candidate_indices_for_particle(pos, i, box_size, neighbor_state):
        if i == j:
            continue
        delta = minimum_image(pos[i] - pos[j], box_size)
        r = float(np.linalg.norm(delta))
        energy += lj_pair_energy(
            r,
            epsilon,
            sigma,
            use_cutoff=bool(neighbor_state and neighbor_state.use_cutoff),
            cutoff_radius=neighbor_state.cutoff_radius if neighbor_state else None,
        )

    return energy


def total_energy(
    pos: np.ndarray,
    box_size: float,
    epsilon: float,
    sigma: float,
    *,
    neighbor_state: NeighborState | None = None,
    use_cutoff: bool = False,
    cutoff_radius: float | None = None,
    use_cell_list: bool = False,
    cell_size: float | None = None,
) -> float:
    """全粒子系の全エネルギーを返す。"""
    state = neighbor_state
    if state is None and (use_cutoff or use_cell_list):
        state = build_neighbor_state(
            pos,
            box_size,
            use_cutoff=use_cutoff,
            cutoff_radius=cutoff_radius,
            use_cell_list=use_cell_list,
            cell_size=cell_size,
        )
    return sum(calc_energy(pos, i, box_size, epsilon, sigma, neighbor_state=state) for i in range(len(pos))) / 2.0


def insertion_energy(
    pos: np.ndarray,
    candidate: np.ndarray,
    box_size: float,
    epsilon: float,
    sigma: float,
    *,
    neighbor_state: NeighborState | None = None,
) -> float:
    """候補位置に 1 粒子を挿入したときの相互作用エネルギーを返す。"""
    if len(pos) == 0:
        return 0.0

    energy = 0.0
    for idx in _candidate_indices_for_point(candidate, pos, box_size, neighbor_state):
        delta = minimum_image(candidate - pos[idx], box_size)
        r = float(np.linalg.norm(delta))
        energy += lj_pair_energy(
            r,
            epsilon,
            sigma,
            use_cutoff=bool(neighbor_state and neighbor_state.use_cutoff),
            cutoff_radius=neighbor_state.cutoff_radius if neighbor_state else None,
        )
    return energy
