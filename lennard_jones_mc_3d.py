#!/usr/bin/env python3
"""
3D Lennard-Jones Molecular Monte Carlo Simulation
メトロポリス・モンテカルロ法による3次元LJ流体のシミュレーション
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from lj_core import (
    build_neighbor_state,
    calc_energy,
    init_positions,
    normalize_neighbor_options,
    total_energy,
    validate_common_parameters,
    validate_initial_density,
    update_neighbor_state_after_move,
    wrap_positions,
)


# ============== パラメータ（ここで変更可能） ==============
T = 1.2               # 温度（無次元）
N_STEPS = 10_000      # モンテカルロステップ数
DELTA_MAX = 0.25      # 粒子の最大移動距離
BOX_SIZE = 8.0        # シミュレーション箱の一辺
N = 64                # 粒子数
EPSILON = 1.0         # LJポテンシャルのε
SIGMA = 1.0           # LJポテンシャルのσ
VISUALIZE_INTERVAL = 100
SAVE_FINAL_IMAGE = True
INTERACTIVE = True
RNG_SEED = 42
USE_CUTOFF = False
CUTOFF_RADIUS = 3.0
USE_CELL_LIST = False
CELL_SIZE = 3.0
# ========================================================

OUTPUT_DIR = Path(__file__).resolve().parent


def validate_parameters() -> None:
    """実行前に主要パラメータの妥当性を確認する。"""
    validate_common_parameters(
        temperature=T,
        n_particles=N,
        n_steps=N_STEPS,
        delta_max=DELTA_MAX,
        box_size=BOX_SIZE,
        epsilon=EPSILON,
        sigma=SIGMA,
    )
    if VISUALIZE_INTERVAL <= 0:
        raise ValueError(f"VISUALIZE_INTERVAL must be positive, got {VISUALIZE_INTERVAL}")

    validate_initial_density(
        n_particles=N,
        box_size=BOX_SIZE,
        min_distance=0.9 * SIGMA,
        dim=3,
    )
    normalize_neighbor_options(
        box_size=BOX_SIZE,
        use_cutoff=USE_CUTOFF,
        cutoff_radius=CUTOFF_RADIUS,
        use_cell_list=USE_CELL_LIST,
        cell_size=CELL_SIZE,
    )


def mc_step(
    pos: np.ndarray,
    box_size: float,
    temperature: float,
    delta_max: float,
    epsilon: float,
    sigma: float,
    rng: np.random.Generator,
    neighbor_state,
) -> tuple[float, bool]:
    """3次元箱内で 1 粒子変位の MC 試行を 1 回行う。"""
    n_particles = len(pos)
    idx = int(rng.integers(0, n_particles))

    e_old = calc_energy(pos, idx, box_size, epsilon, sigma, neighbor_state=neighbor_state)

    delta = rng.uniform(-delta_max, delta_max, size=3)
    pos_old = pos[idx].copy()
    pos[idx] = wrap_positions(pos[idx] + delta, box_size)
    update_neighbor_state_after_move(neighbor_state, idx, pos_old, pos[idx], box_size)

    e_new = calc_energy(pos, idx, box_size, epsilon, sigma, neighbor_state=neighbor_state)
    dE = e_new - e_old

    if dE <= 0.0:
        return dE, True
    if rng.random() < np.exp(-dE / temperature):
        return dE, True

    pos_new = pos[idx].copy()
    pos[idx] = pos_old
    update_neighbor_state_after_move(neighbor_state, idx, pos_new, pos_old, box_size)
    return 0.0, False


def run_simulation() -> tuple[np.ndarray, np.ndarray, int]:
    """3次元単箱 MC を実行し、履歴を返す。"""
    rng = np.random.default_rng(RNG_SEED)

    pos = init_positions(BOX_SIZE, N, 0.9 * SIGMA, rng, dim=3)
    neighbor_state = build_neighbor_state(
        pos,
        BOX_SIZE,
        use_cutoff=USE_CUTOFF,
        cutoff_radius=CUTOFF_RADIUS,
        use_cell_list=USE_CELL_LIST,
        cell_size=CELL_SIZE,
    )
    pos_history = [pos.copy()]
    energy_history: list[float] = []

    n_accepted = 0
    current_energy = total_energy(
        pos,
        BOX_SIZE,
        EPSILON,
        SIGMA,
        neighbor_state=neighbor_state,
    )

    for step in range(N_STEPS):
        dE, accepted = mc_step(pos, BOX_SIZE, T, DELTA_MAX, EPSILON, SIGMA, rng, neighbor_state)
        if accepted:
            n_accepted += 1
        current_energy += dE
        energy_history.append(current_energy)

        if (step + 1) % VISUALIZE_INTERVAL == 0:
            pos_history.append(pos.copy())

    if N_STEPS % VISUALIZE_INTERVAL != 0:
        pos_history.append(pos.copy())

    return np.array(pos_history), np.array(energy_history), n_accepted


def visualize(pos_history: np.ndarray, energy_history: np.ndarray) -> None:
    """最終配置の3D散布図とエネルギー履歴を表示・保存する。"""
    final_pos = pos_history[-1]

    fig = plt.figure(figsize=(12, 5))
    ax1 = fig.add_subplot(1, 2, 1, projection="3d")
    ax2 = fig.add_subplot(1, 2, 2)

    ax1.scatter(final_pos[:, 0], final_pos[:, 1], final_pos[:, 2], s=32, c="steelblue", alpha=0.8)
    ax1.set_xlim(0, BOX_SIZE)
    ax1.set_ylim(0, BOX_SIZE)
    ax1.set_zlim(0, BOX_SIZE)
    ax1.set_xlabel("x")
    ax1.set_ylabel("y")
    ax1.set_zlabel("z")
    ax1.set_title("3D Lennard-Jones MC: Final configuration")

    step_indices = np.arange(len(energy_history))
    ax2.plot(step_indices, energy_history, "b-", linewidth=0.6)
    ax2.set_xlabel("MC Step")
    ax2.set_ylabel("Energy")
    ax2.set_title("Energy history")
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()

    if SAVE_FINAL_IMAGE:
        final_image_path = OUTPUT_DIR / "lennard_jones_3d_final.png"
        fig.savefig(final_image_path, dpi=150, bbox_inches="tight")
        print(f"最終配置を {final_image_path} に保存しました")

    if INTERACTIVE:
        plt.show()
    plt.close(fig)


def main() -> None:
    validate_parameters()
    print("3D Lennard-Jones Monte Carlo Simulation")
    print(f"  温度 T = {T}, 粒子数 N = {N}, ステップ数 = {N_STEPS}")
    print(f"  box_size = {BOX_SIZE}, delta_max = {DELTA_MAX}")
    print(f"  use_cutoff = {USE_CUTOFF}, cutoff_radius = {CUTOFF_RADIUS}")
    print(f"  use_cell_list = {USE_CELL_LIST}, cell_size = {CELL_SIZE}")
    print("シミュレーション実行中...")

    pos_history, energy_history, n_accepted = run_simulation()

    acceptance_ratio = n_accepted / N_STEPS
    print(f"最終エネルギー: {energy_history[-1]:.4f}")
    print(f"受理率 (Acceptance Ratio): {acceptance_ratio:.2%} ({n_accepted}/{N_STEPS})")

    visualize(pos_history, energy_history)


if __name__ == "__main__":
    main()
