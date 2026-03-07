#!/usr/bin/env python3
"""
2D Lennard-Jones Molecular Monte Carlo Simulation
メトロポリス・モンテカルロ法による2次元LJ流体のシミュレーション
"""

import numpy as np
import matplotlib.pyplot as plt
import japanize_matplotlib  # グラフタイトル等の日本語表示用
from pathlib import Path
from matplotlib.animation import FuncAnimation

from lj_core import (
    build_neighbor_state,
    calc_energy,
    init_positions,
    normalize_neighbor_options,
    validate_common_parameters,
    validate_initial_density,
    update_neighbor_state_after_move,
    wrap_positions,
)

# ============== パラメータ（ここで変更可能） ==============
T = 1.0              # 温度（無次元）
N_STEPS = 10_000     # モンテカルロステップ数
DELTA_MAX = 0.2      # 粒子の最大移動距離
BOX_SIZE = 10.0      # シミュレーション箱のサイズ
N = 32               # 粒子数
EPSILON = 1.0        # LJポテンシャルのε
SIGMA = 1.0          # LJポテンシャルのσ
VISUALIZE_INTERVAL = 100   # 可視化の更新間隔（ステップ）
SAVE_ANIMATION = False     # Trueでアニメーションをファイルに保存
SAVE_FINAL_IMAGE = True    # Trueで最終配置をPNGに保存
INTERACTIVE = True         # FalseでGUI表示をスキップ（画像保存のみ、CI等で使用）
USE_CUTOFF = False         # Trueでcutoffを使う
CUTOFF_RADIUS = 3.0        # cutoff半径（sigma=1単位系）
USE_CELL_LIST = False      # Trueでcell listを使う
CELL_SIZE = 3.0            # cell listのセルサイズ
# ========================================================

OUTPUT_DIR = Path(__file__).resolve().parent


def validate_parameters():
    """実行前に主要パラメータの妥当性を確認する"""
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
        raise ValueError(f'VISUALIZE_INTERVAL must be positive, got {VISUALIZE_INTERVAL}')

    # 密度の妥当性: ランダム配置が物理的に可能かチェック
    min_init_distance = 0.9 * SIGMA
    validate_initial_density(
        n_particles=N,
        box_size=BOX_SIZE,
        min_distance=min_init_distance,
        dim=2,
    )
    normalize_neighbor_options(
        box_size=BOX_SIZE,
        use_cutoff=USE_CUTOFF,
        cutoff_radius=CUTOFF_RADIUS,
        use_cell_list=USE_CELL_LIST,
        cell_size=CELL_SIZE,
    )


def mc_step(pos: np.ndarray, box_size: float, T: float, delta_max: float,
            epsilon: float, sigma: float, rng: np.random.Generator, neighbor_state) -> tuple[float, bool]:
    """
    1回のメトロポリス・モンテカルロステップ
    ランダムに粒子を1つ選び、ランダム変位で移動を試行
    返り値: (エネルギー差 ΔE, 受理したか)
    """
    n = len(pos)
    i = rng.integers(0, n)

    # 移動前のエネルギー
    E_old = calc_energy(pos, i, box_size, epsilon, sigma, neighbor_state=neighbor_state)

    # ランダム変位
    delta = rng.uniform(-delta_max, delta_max, size=2)
    pos_old = pos[i].copy()
    pos[i] += delta

    # 周期境界条件: 箱の外に出たら折り返す
    pos[i] = wrap_positions(pos[i], box_size)
    update_neighbor_state_after_move(neighbor_state, i, pos_old, pos[i], box_size)

    # 移動後のエネルギー
    E_new = calc_energy(pos, i, box_size, epsilon, sigma, neighbor_state=neighbor_state)
    dE = E_new - E_old

    # メトロポリス判定
    if dE <= 0:
        return dE, True
    if rng.random() < np.exp(-dE / T):
        return dE, True

    # 不採用: 元の位置に戻す
    pos_new = pos[i].copy()
    pos[i] = pos_old
    update_neighbor_state_after_move(neighbor_state, i, pos_new, pos_old, box_size)
    return 0.0, False


def run_simulation():
    """メインシミュレーション実行"""
    rng = np.random.default_rng(42)

    # 初期化
    min_init_distance = 0.9 * SIGMA
    pos = init_positions(BOX_SIZE, N, min_init_distance, rng, dim=2)
    neighbor_state = build_neighbor_state(
        pos,
        BOX_SIZE,
        use_cutoff=USE_CUTOFF,
        cutoff_radius=CUTOFF_RADIUS,
        use_cell_list=USE_CELL_LIST,
        cell_size=CELL_SIZE,
    )
    energy_history = []
    pos_history = [pos.copy()]

    # メインループ
    n_accepted = 0
    current_energy = sum(calc_energy(pos, i, BOX_SIZE, EPSILON, SIGMA, neighbor_state=neighbor_state) for i in range(N)) / 2
    for step in range(N_STEPS):
        dE, accepted = mc_step(pos, BOX_SIZE, T, DELTA_MAX, EPSILON, SIGMA, rng, neighbor_state)
        if accepted:
            n_accepted += 1
        current_energy += dE
        energy_history.append(current_energy)

        if (step + 1) % VISUALIZE_INTERVAL == 0:
            pos_history.append(pos.copy())

    # N_STEPS が VISUALIZE_INTERVAL の倍数でない場合、最終状態を追加
    if N_STEPS % VISUALIZE_INTERVAL != 0:
        pos_history.append(pos.copy())

    return np.array(pos_history), np.array(energy_history), n_accepted


def visualize(pos_history: np.ndarray, energy_history: np.ndarray):
    """粒子配置の可視化（アニメーションまたは最終状態）"""
    n_frames = len(pos_history)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # 左: 粒子配置
    scatter = ax1.scatter(pos_history[0][:, 0], pos_history[0][:, 1], s=50, c='steelblue', alpha=0.8)
    ax1.set_xlim(0, BOX_SIZE)
    ax1.set_ylim(0, BOX_SIZE)
    ax1.set_aspect('equal')
    ax1.set_xlabel('x')
    ax1.set_ylabel('y')
    ax1.set_title('2D Lennard-Jones MC: 粒子配置')

    # 右: エネルギー履歴
    step_indices = np.arange(len(energy_history))
    energy_line, = ax2.plot(step_indices, energy_history, 'b-', linewidth=0.5)
    ax2.set_xlabel('MC Step')
    ax2.set_ylabel('Energy')
    ax2.set_title('エネルギー履歴')
    ax2.grid(True, alpha=0.3)

    def update(frame):
        scatter.set_offsets(pos_history[frame])
        # エネルギー履歴は該当ステップまで表示
        idx = min(frame * VISUALIZE_INTERVAL, len(energy_history))
        if idx > 0:
            energy_line.set_data(step_indices[:idx], energy_history[:idx])
            ax2.set_xlim(0, max(idx, 100))
        return scatter, energy_line

    if SAVE_ANIMATION and n_frames > 1:
        anim = FuncAnimation(fig, update, frames=n_frames, interval=50, blit=False)
        animation_path = OUTPUT_DIR / 'lennard_jones_animation.gif'
        anim.save(animation_path, writer='pillow', fps=20)
        print(f'アニメーションを {animation_path} に保存しました')
    elif n_frames > 1 and INTERACTIVE:
        anim = FuncAnimation(fig, update, frames=n_frames, interval=50, blit=False)
        plt.show()
    elif INTERACTIVE:
        plt.show()
    plt.close(fig)

    if SAVE_FINAL_IMAGE:
        fig2, ax = plt.subplots(figsize=(6, 6))
        ax.scatter(pos_history[-1][:, 0], pos_history[-1][:, 1], s=50, c='steelblue', alpha=0.8)
        ax.set_xlim(0, BOX_SIZE)
        ax.set_ylim(0, BOX_SIZE)
        ax.set_aspect('equal')
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_title(f'2D Lennard-Jones MC: 最終配置 (T={T}, N={N_STEPS} steps)')
        final_image_path = OUTPUT_DIR / 'lennard_jones_final.png'
        fig2.savefig(final_image_path, dpi=150, bbox_inches='tight')
        plt.close(fig2)
        print(f'最終配置を {final_image_path} に保存しました')


def main():
    validate_parameters()
    print('2D Lennard-Jones Monte Carlo Simulation')
    print(f'  温度 T = {T}, 粒子数 N = {N}, ステップ数 = {N_STEPS}')
    print(f'  box_size = {BOX_SIZE}, delta_max = {DELTA_MAX}')
    print(f'  use_cutoff = {USE_CUTOFF}, cutoff_radius = {CUTOFF_RADIUS}')
    print(f'  use_cell_list = {USE_CELL_LIST}, cell_size = {CELL_SIZE}')
    print('シミュレーション実行中...')

    pos_history, energy_history, n_accepted = run_simulation()

    acceptance_ratio = n_accepted / N_STEPS
    print(f'最終エネルギー: {energy_history[-1]:.4f}')
    print(f'受理率 (Acceptance Ratio): {acceptance_ratio:.2%} ({n_accepted}/{N_STEPS})')
    print('可視化を表示します...')

    visualize(pos_history, energy_history)


if __name__ == '__main__':
    main()
