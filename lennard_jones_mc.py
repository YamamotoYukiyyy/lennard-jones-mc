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
# ========================================================

OUTPUT_DIR = Path(__file__).resolve().parent


def validate_parameters():
    """実行前に主要パラメータの妥当性を確認する"""
    if T <= 0:
        raise ValueError(f'T must be positive, got {T}')
    if N <= 0:
        raise ValueError(f'N must be positive, got {N}')
    if N_STEPS <= 0:
        raise ValueError(f'N_STEPS must be positive, got {N_STEPS}')
    if DELTA_MAX <= 0:
        raise ValueError(f'DELTA_MAX must be positive, got {DELTA_MAX}')
    if BOX_SIZE <= 0:
        raise ValueError(f'BOX_SIZE must be positive, got {BOX_SIZE}')
    if EPSILON < 0:
        raise ValueError(f'EPSILON must be non-negative, got {EPSILON}')
    if SIGMA <= 0:
        raise ValueError(f'SIGMA must be positive, got {SIGMA}')
    if VISUALIZE_INTERVAL <= 0:
        raise ValueError(f'VISUALIZE_INTERVAL must be positive, got {VISUALIZE_INTERVAL}')

    # 密度の妥当性: ランダム配置が物理的に可能かチェック
    min_init_distance = 0.9 * SIGMA
    area_per_particle = np.pi * (min_init_distance / 2) ** 2
    total_required = N * area_per_particle
    # ランダム配置では packing fraction ~0.5 が限界の目安
    if total_required > 0.8 * (BOX_SIZE**2):
        raise ValueError(
            f'Density too high: N={N} particles with min_distance={min_init_distance:.3f} '
            f'require area ~{total_required:.1f}, but box has {BOX_SIZE**2:.1f}. '
            'Increase BOX_SIZE or decrease N.'
        )


def init_positions(box_size: float, n: int, min_distance: float,
                   rng: np.random.Generator, max_trials: int = 10_000,
                   max_global_retries: int = 1000) -> np.ndarray:
    """粒子をランダムに初期配置し、詰まった場合は全体を作り直す"""
    min_distance_sq = min_distance ** 2

    for _ in range(max_global_retries):
        pos = np.empty((n, 2), dtype=float)

        for idx in range(n):
            for _ in range(max_trials):
                candidate = rng.uniform(0.0, box_size, size=2)
                if idx == 0:
                    pos[idx] = candidate
                    break

                delta = candidate - pos[:idx]
                delta -= box_size * np.round(delta / box_size)
                distances_sq = np.sum(delta * delta, axis=1)
                if np.all(distances_sq >= min_distance_sq):
                    pos[idx] = candidate
                    break
            else:
                # 局所的に詰まった場合は、初期配置全体を最初から引き直す。
                break
        else:
            return pos

    raise ValueError(
        f'Failed to place {n} particles with min_distance={min_distance:.3f} '
        f'in box_size={box_size} after {max_global_retries} attempts. '
        'Density may be too high.'
    )


def calc_energy(pos: np.ndarray, i: int, box_size: float, epsilon: float, sigma: float) -> float:
    """
    粒子iの、他の全粒子とのLJ相互作用エネルギーの総和を計算
    周期境界条件（Minimum Image Convention）を適用
    """
    energy = 0.0
    xi, yi = pos[i, 0], pos[i, 1]
    n = len(pos)

    for j in range(n):
        if i == j:
            continue
        xj, yj = pos[j, 0], pos[j, 1]

        # 周期境界条件: Minimum Image Convention
        dx = xi - xj
        dy = yi - yj
        dx = dx - box_size * np.round(dx / box_size)
        dy = dy - box_size * np.round(dy / box_size)

        r = np.sqrt(dx * dx + dy * dy)
        if r < 1e-10:  # 同一位置の回避
            continue

        # Lennard-Jones 12-6: V(r) = 4ε[(σ/r)^12 - (σ/r)^6]
        sr = sigma / r
        sr6 = sr ** 6
        sr12 = sr6 ** 2
        energy += 4.0 * epsilon * (sr12 - sr6)

    return energy


def mc_step(pos: np.ndarray, box_size: float, T: float, delta_max: float,
            epsilon: float, sigma: float, rng: np.random.Generator) -> tuple[float, bool]:
    """
    1回のメトロポリス・モンテカルロステップ
    ランダムに粒子を1つ選び、ランダム変位で移動を試行
    返り値: (エネルギー差 ΔE, 受理したか)
    """
    n = len(pos)
    i = rng.integers(0, n)

    # 移動前のエネルギー
    E_old = calc_energy(pos, i, box_size, epsilon, sigma)

    # ランダム変位
    delta = rng.uniform(-delta_max, delta_max, size=2)
    pos_old = pos[i].copy()
    pos[i] += delta

    # 周期境界条件: 箱の外に出たら折り返す
    pos[i] = pos[i] % box_size

    # 移動後のエネルギー
    E_new = calc_energy(pos, i, box_size, epsilon, sigma)
    dE = E_new - E_old

    # メトロポリス判定
    if dE <= 0:
        return dE, True
    if rng.random() < np.exp(-dE / T):
        return dE, True

    # 不採用: 元の位置に戻す
    pos[i] = pos_old
    return 0.0, False


def run_simulation():
    """メインシミュレーション実行"""
    rng = np.random.default_rng(42)

    # 初期化
    min_init_distance = 0.9 * SIGMA
    pos = init_positions(BOX_SIZE, N, min_init_distance, rng)
    energy_history = []
    pos_history = [pos.copy()]

    # メインループ
    n_accepted = 0
    for step in range(N_STEPS):
        dE, accepted = mc_step(pos, BOX_SIZE, T, DELTA_MAX, EPSILON, SIGMA, rng)
        if accepted:
            n_accepted += 1
        if step == 0:
            E = sum(calc_energy(pos, i, BOX_SIZE, EPSILON, SIGMA) for i in range(N)) / 2
        else:
            E = energy_history[-1] + dE
        energy_history.append(E)

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
    print('シミュレーション実行中...')

    pos_history, energy_history, n_accepted = run_simulation()

    acceptance_ratio = n_accepted / N_STEPS
    print(f'最終エネルギー: {energy_history[-1]:.4f}')
    print(f'受理率 (Acceptance Ratio): {acceptance_ratio:.2%} ({n_accepted}/{N_STEPS})')
    print('可視化を表示します...')

    visualize(pos_history, energy_history)


if __name__ == '__main__':
    main()
