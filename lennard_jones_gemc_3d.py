#!/usr/bin/env python3
"""
3D Lennard-Jones Gibbs Ensemble Monte Carlo Simulation
3次元 Lennard-Jones 流体に対する Gibbs Ensemble Monte Carlo の実装
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from lj_core import (
    build_neighbor_state,
    calc_energy,
    init_positions,
    insertion_energy,
    normalize_neighbor_options,
    rebuild_neighbor_state,
    total_energy,
    validate_common_parameters,
    validate_initial_density,
    update_neighbor_state_after_move,
    wrap_positions,
)


# ============== パラメータ（ここで変更可能） ==============
TEMPERATURE = 1.15
N_TOTAL = 64
N_CYCLES = 2_000
DELTA_MAX = 0.25
DELTA_V_MAX = 8.0
TOTAL_DENSITY = 0.30
INITIAL_PARTICLE_FRACTION_BOX1 = 0.75
INITIAL_VOLUME_FRACTION_BOX1 = 0.50
EPSILON = 1.0
SIGMA = 1.0
DISPLACEMENT_TRIES_PER_CYCLE = N_TOTAL
TRANSFER_TRIES_PER_CYCLE = max(1, int(0.3 * N_TOTAL))
SAVE_FINAL_IMAGE = True
INTERACTIVE = True
RNG_SEED = 123
USE_CUTOFF = False
CUTOFF_RADIUS = 2.0
USE_CELL_LIST = False
CELL_SIZE = 3.0
# ========================================================

OUTPUT_DIR = Path(__file__).resolve().parent


@dataclass
class BoxState:
    pos: np.ndarray
    box_size: float
    energy: float
    neighbor_state: object | None = None

    @property
    def volume(self) -> float:
        return self.box_size**3

    @property
    def n_particles(self) -> int:
        return len(self.pos)

    @property
    def density(self) -> float:
        return self.n_particles / self.volume


def validate_parameters() -> None:
    """GEMC の主要パラメータを検証する。"""
    validate_common_parameters(
        temperature=TEMPERATURE,
        n_particles=N_TOTAL,
        n_steps=N_CYCLES,
        delta_max=DELTA_MAX,
        box_size=1.0,
        epsilon=EPSILON,
        sigma=SIGMA,
    )
    if DELTA_V_MAX <= 0:
        raise ValueError(f"DELTA_V_MAX must be positive, got {DELTA_V_MAX}")
    if TOTAL_DENSITY <= 0:
        raise ValueError(f"TOTAL_DENSITY must be positive, got {TOTAL_DENSITY}")
    if not 0.0 < INITIAL_PARTICLE_FRACTION_BOX1 < 1.0:
        raise ValueError("INITIAL_PARTICLE_FRACTION_BOX1 must be between 0 and 1.")
    if not 0.0 < INITIAL_VOLUME_FRACTION_BOX1 < 1.0:
        raise ValueError("INITIAL_VOLUME_FRACTION_BOX1 must be between 0 and 1.")
    if DISPLACEMENT_TRIES_PER_CYCLE <= 0:
        raise ValueError("DISPLACEMENT_TRIES_PER_CYCLE must be positive.")
    if TRANSFER_TRIES_PER_CYCLE <= 0:
        raise ValueError("TRANSFER_TRIES_PER_CYCLE must be positive.")
    normalize_neighbor_options(
        box_size=(N_TOTAL / TOTAL_DENSITY) ** (1.0 / 3.0),
        use_cutoff=USE_CUTOFF,
        cutoff_radius=CUTOFF_RADIUS,
        use_cell_list=USE_CELL_LIST,
        cell_size=CELL_SIZE,
    )


def build_initial_boxes(rng: np.random.Generator) -> tuple[BoxState, BoxState]:
    """初期の2箱を構築する。"""
    total_volume = N_TOTAL / TOTAL_DENSITY
    volume1 = INITIAL_VOLUME_FRACTION_BOX1 * total_volume
    volume2 = total_volume - volume1
    box_size1 = volume1 ** (1.0 / 3.0)
    box_size2 = volume2 ** (1.0 / 3.0)

    if USE_CUTOFF and CUTOFF_RADIUS >= 0.5 * min(box_size1, box_size2):
        raise ValueError(
            "Initial GEMC boxes are too small for the requested cutoff radius. "
            f"Got cutoff_radius={CUTOFF_RADIUS}, min_box_size={min(box_size1, box_size2)}."
        )

    n1 = int(round(INITIAL_PARTICLE_FRACTION_BOX1 * N_TOTAL))
    n1 = max(1, min(N_TOTAL - 1, n1))
    n2 = N_TOTAL - n1

    min_distance = 0.9 * SIGMA
    validate_initial_density(n_particles=n1, box_size=box_size1, min_distance=min_distance, dim=3)
    validate_initial_density(n_particles=n2, box_size=box_size2, min_distance=min_distance, dim=3)

    pos1 = init_positions(box_size1, n1, min_distance, rng, dim=3)
    pos2 = init_positions(box_size2, n2, min_distance, rng, dim=3)

    return (
        BoxState(
            pos=pos1,
            box_size=box_size1,
            energy=total_energy(
                pos1,
                box_size1,
                EPSILON,
                SIGMA,
                use_cutoff=USE_CUTOFF,
                cutoff_radius=CUTOFF_RADIUS,
                use_cell_list=USE_CELL_LIST,
                cell_size=CELL_SIZE,
            ),
            neighbor_state=build_neighbor_state(
                pos1,
                box_size1,
                use_cutoff=USE_CUTOFF,
                cutoff_radius=CUTOFF_RADIUS,
                use_cell_list=USE_CELL_LIST,
                cell_size=CELL_SIZE,
            ),
        ),
        BoxState(
            pos=pos2,
            box_size=box_size2,
            energy=total_energy(
                pos2,
                box_size2,
                EPSILON,
                SIGMA,
                use_cutoff=USE_CUTOFF,
                cutoff_radius=CUTOFF_RADIUS,
                use_cell_list=USE_CELL_LIST,
                cell_size=CELL_SIZE,
            ),
            neighbor_state=build_neighbor_state(
                pos2,
                box_size2,
                use_cutoff=USE_CUTOFF,
                cutoff_radius=CUTOFF_RADIUS,
                use_cell_list=USE_CELL_LIST,
                cell_size=CELL_SIZE,
            ),
        ),
    )


def displacement_move(box: BoxState, rng: np.random.Generator) -> bool:
    """箱内の 1 粒子変位 move を試行する。"""
    if box.n_particles == 0:
        return False

    idx = int(rng.integers(0, box.n_particles))
    e_old = calc_energy(box.pos, idx, box.box_size, EPSILON, SIGMA, neighbor_state=box.neighbor_state)

    delta = rng.uniform(-DELTA_MAX, DELTA_MAX, size=3)
    pos_old = box.pos[idx].copy()
    box.pos[idx] = wrap_positions(box.pos[idx] + delta, box.box_size)
    update_neighbor_state_after_move(box.neighbor_state, idx, pos_old, box.pos[idx], box.box_size)

    e_new = calc_energy(box.pos, idx, box.box_size, EPSILON, SIGMA, neighbor_state=box.neighbor_state)
    dE = e_new - e_old

    if dE <= 0.0 or rng.random() < np.exp(-dE / TEMPERATURE):
        box.energy += dE
        return True

    pos_new = box.pos[idx].copy()
    box.pos[idx] = pos_old
    update_neighbor_state_after_move(box.neighbor_state, idx, pos_new, pos_old, box.box_size)
    return False


def volume_exchange_move(box1: BoxState, box2: BoxState, rng: np.random.Generator) -> bool:
    """全体積一定のまま 2 箱間で体積交換を試行する。"""
    volume1_old = box1.volume
    volume2_old = box2.volume
    dV = float(rng.uniform(-DELTA_V_MAX, DELTA_V_MAX))
    volume1_new = volume1_old + dV
    volume2_new = volume2_old - dV

    min_volume = (0.5 * SIGMA) ** 3
    if volume1_new <= min_volume or volume2_new <= min_volume:
        return False

    scale1 = (volume1_new / volume1_old) ** (1.0 / 3.0)
    scale2 = (volume2_new / volume2_old) ** (1.0 / 3.0)

    pos1_new = box1.pos * scale1
    pos2_new = box2.pos * scale2
    box_size1_new = box1.box_size * scale1
    box_size2_new = box2.box_size * scale2

    if USE_CUTOFF and CUTOFF_RADIUS >= 0.5 * min(box_size1_new, box_size2_new):
        return False

    neighbor_state1_new = build_neighbor_state(
        pos1_new,
        box_size1_new,
        use_cutoff=USE_CUTOFF,
        cutoff_radius=CUTOFF_RADIUS,
        use_cell_list=USE_CELL_LIST,
        cell_size=CELL_SIZE,
    )
    neighbor_state2_new = build_neighbor_state(
        pos2_new,
        box_size2_new,
        use_cutoff=USE_CUTOFF,
        cutoff_radius=CUTOFF_RADIUS,
        use_cell_list=USE_CELL_LIST,
        cell_size=CELL_SIZE,
    )

    energy1_new = total_energy(pos1_new, box_size1_new, EPSILON, SIGMA, neighbor_state=neighbor_state1_new)
    energy2_new = total_energy(pos2_new, box_size2_new, EPSILON, SIGMA, neighbor_state=neighbor_state2_new)
    dE = (energy1_new + energy2_new) - (box1.energy + box2.energy)

    ln_acc = (
        -dE / TEMPERATURE
        + box1.n_particles * np.log(volume1_new / volume1_old)
        + box2.n_particles * np.log(volume2_new / volume2_old)
    )

    if np.log(rng.random()) < min(0.0, ln_acc):
        box1.pos = pos1_new
        box2.pos = pos2_new
        box1.box_size = box_size1_new
        box2.box_size = box_size2_new
        box1.energy = energy1_new
        box2.energy = energy2_new
        box1.neighbor_state = neighbor_state1_new
        box2.neighbor_state = neighbor_state2_new
        return True

    return False


def particle_transfer_move(source: BoxState, dest: BoxState, rng: np.random.Generator) -> bool:
    """source から dest への粒子交換を 1 回試行する。"""
    if source.n_particles == 0:
        return False

    idx = int(rng.integers(0, source.n_particles))
    candidate = rng.uniform(0.0, dest.box_size, size=3)

    removal_energy = calc_energy(source.pos, idx, source.box_size, EPSILON, SIGMA, neighbor_state=source.neighbor_state)
    insert_energy = insertion_energy(dest.pos, candidate, dest.box_size, EPSILON, SIGMA, neighbor_state=dest.neighbor_state)
    dE = insert_energy - removal_energy

    acc_ratio = (source.n_particles * dest.volume) / ((dest.n_particles + 1) * source.volume)
    ln_acc = np.log(acc_ratio) - dE / TEMPERATURE

    if np.log(rng.random()) < min(0.0, ln_acc):
        removed = np.delete(source.pos, idx, axis=0)
        inserted = candidate.reshape(1, 3)
        dest.pos = inserted if dest.n_particles == 0 else np.vstack([dest.pos, inserted])
        source.pos = removed
        source.energy -= removal_energy
        dest.energy += insert_energy
        source.neighbor_state = rebuild_neighbor_state(source.neighbor_state, source.pos, source.box_size)
        dest.neighbor_state = rebuild_neighbor_state(dest.neighbor_state, dest.pos, dest.box_size)
        return True

    return False


def run_simulation() -> tuple[BoxState, BoxState, dict[str, np.ndarray], dict[str, int]]:
    """3D GEMC を実行し、最終状態と履歴を返す。"""
    rng = np.random.default_rng(RNG_SEED)
    box1, box2 = build_initial_boxes(rng)

    histories: dict[str, list[float]] = {
        "n1": [],
        "n2": [],
        "rho1": [],
        "rho2": [],
        "e1": [],
        "e2": [],
        "v1": [],
        "v2": [],
    }
    move_counts = {"disp_accept": 0, "disp_total": 0, "vol_accept": 0, "vol_total": 0, "transfer_accept": 0, "transfer_total": 0}

    for _ in range(N_CYCLES):
        for _ in range(DISPLACEMENT_TRIES_PER_CYCLE):
            target = box1 if rng.random() < 0.5 else box2
            move_counts["disp_total"] += 1
            if displacement_move(target, rng):
                move_counts["disp_accept"] += 1

        move_counts["vol_total"] += 1
        if volume_exchange_move(box1, box2, rng):
            move_counts["vol_accept"] += 1

        for _ in range(TRANSFER_TRIES_PER_CYCLE):
            move_counts["transfer_total"] += 1
            if rng.random() < 0.5:
                accepted = particle_transfer_move(box1, box2, rng)
            else:
                accepted = particle_transfer_move(box2, box1, rng)
            if accepted:
                move_counts["transfer_accept"] += 1

        histories["n1"].append(box1.n_particles)
        histories["n2"].append(box2.n_particles)
        histories["rho1"].append(box1.density)
        histories["rho2"].append(box2.density)
        histories["e1"].append(box1.energy)
        histories["e2"].append(box2.energy)
        histories["v1"].append(box1.volume)
        histories["v2"].append(box2.volume)

    return box1, box2, {key: np.array(values) for key, values in histories.items()}, move_counts


def visualize(box1: BoxState, box2: BoxState, histories: dict[str, np.ndarray]) -> None:
    """最終 2 箱配置と密度・粒子数履歴を可視化する。"""
    fig = plt.figure(figsize=(14, 10))
    ax1 = fig.add_subplot(2, 2, 1, projection="3d")
    ax2 = fig.add_subplot(2, 2, 2, projection="3d")
    ax3 = fig.add_subplot(2, 2, 3)
    ax4 = fig.add_subplot(2, 2, 4)

    if box1.n_particles > 0:
        ax1.scatter(box1.pos[:, 0], box1.pos[:, 1], box1.pos[:, 2], s=28, c="tab:blue", alpha=0.75)
    ax1.set_xlim(0, box1.box_size)
    ax1.set_ylim(0, box1.box_size)
    ax1.set_zlim(0, box1.box_size)
    ax1.set_title("Box 1 final configuration")
    ax1.set_xlabel("x")
    ax1.set_ylabel("y")
    ax1.set_zlabel("z")

    if box2.n_particles > 0:
        ax2.scatter(box2.pos[:, 0], box2.pos[:, 1], box2.pos[:, 2], s=28, c="tab:orange", alpha=0.75)
    ax2.set_xlim(0, box2.box_size)
    ax2.set_ylim(0, box2.box_size)
    ax2.set_zlim(0, box2.box_size)
    ax2.set_title("Box 2 final configuration")
    ax2.set_xlabel("x")
    ax2.set_ylabel("y")
    ax2.set_zlabel("z")

    cycle = np.arange(1, len(histories["rho1"]) + 1)
    ax3.plot(cycle, histories["rho1"], label="rho1")
    ax3.plot(cycle, histories["rho2"], label="rho2")
    ax3.set_xlabel("Cycle")
    ax3.set_ylabel("Density")
    ax3.set_title("Density history")
    ax3.grid(True, alpha=0.3)
    ax3.legend()

    ax4.plot(cycle, histories["n1"], label="N1")
    ax4.plot(cycle, histories["n2"], label="N2")
    ax4.set_xlabel("Cycle")
    ax4.set_ylabel("Particles")
    ax4.set_title("Particle-number history")
    ax4.grid(True, alpha=0.3)
    ax4.legend()

    fig.tight_layout()

    if SAVE_FINAL_IMAGE:
        path = OUTPUT_DIR / "lennard_jones_gemc_3d_final.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        print(f"最終状態を {path} に保存しました")

    if INTERACTIVE:
        plt.show()
    plt.close(fig)


def main() -> None:
    validate_parameters()
    print("3D Lennard-Jones Gibbs Ensemble Monte Carlo Simulation")
    print(f"  T = {TEMPERATURE}, N_total = {N_TOTAL}, cycles = {N_CYCLES}")
    print(f"  total density = {TOTAL_DENSITY}, delta_max = {DELTA_MAX}, delta_V_max = {DELTA_V_MAX}")
    print(f"  use_cutoff = {USE_CUTOFF}, cutoff_radius = {CUTOFF_RADIUS}")
    print(f"  use_cell_list = {USE_CELL_LIST}, cell_size = {CELL_SIZE}")
    print("シミュレーション実行中...")

    box1, box2, histories, move_counts = run_simulation()

    print("最終状態:")
    print(f"  Box 1: N = {box1.n_particles}, V = {box1.volume:.3f}, rho = {box1.density:.4f}, E = {box1.energy:.4f}")
    print(f"  Box 2: N = {box2.n_particles}, V = {box2.volume:.3f}, rho = {box2.density:.4f}, E = {box2.energy:.4f}")
    print(f"  Displacement acceptance = {move_counts['disp_accept'] / move_counts['disp_total']:.2%}")
    print(f"  Volume acceptance = {move_counts['vol_accept'] / move_counts['vol_total']:.2%}")
    print(f"  Transfer acceptance = {move_counts['transfer_accept'] / move_counts['transfer_total']:.2%}")

    visualize(box1, box2, histories)


if __name__ == "__main__":
    main()
