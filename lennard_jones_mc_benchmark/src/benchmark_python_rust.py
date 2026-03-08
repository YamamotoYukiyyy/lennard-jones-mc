#!/usr/bin/env python3
"""
Python / Rust GEMC ベンチマーク比較
T=114 K, N=20〜100（20刻み）, cycles=40000 で計算時間と液相密度を比較

実行: このディレクトリで python benchmark_python_rust.py
出力: benchmark_python_rust_T114K.png, benchmark_results.csv
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

# ベンチマークディレクトリを基準にパスを設定
BENCHMARK_DIR = Path(__file__).resolve().parent
EXERCISE_DIR = BENCHMARK_DIR.parent
PYTHON_MC_DIR = EXERCISE_DIR / "lennard_jones_mc"
RUST_MC_DIR = EXERCISE_DIR / "lennard_jones_mc_rs"

sys.path.insert(0, str(PYTHON_MC_DIR))

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
import numpy as np

import lennard_jones_gemc_3d as gemc

# アルゴン単位変換（Chialvo & Horita 2003）
ARGON_SIGMA_CM = 3.374e-8
ARGON_EPSILON_K = 114.5
ARGON_MOLAR_MASS = 39.948
N_AVOGADRO = 6.02214076e23
EQUILIBRATION_FRACTION = 0.3
T_K = 114.0
N_VALUES = [20, 40, 60, 80, 100]
CYCLES = 40_000


def rho_lj_to_g_cm3(rho_star: float) -> float:
    """LJ 無次元密度を g/cm³ に変換"""
    return rho_star * (ARGON_MOLAR_MASS / N_AVOGADRO) / (ARGON_SIGMA_CM**3)


def run_python_gemc(n: int) -> tuple[float, float]:
    """Python GEMC を実行し、(elapsed_s, rho_liq_g_cm3) を返す"""
    gemc.N_TOTAL = n
    gemc.N_CYCLES = CYCLES
    gemc.TEMPERATURE = T_K / ARGON_EPSILON_K
    gemc.DISPLACEMENT_TRIES_PER_CYCLE = n
    gemc.TRANSFER_TRIES_PER_CYCLE = max(1, int(0.3 * n))
    gemc.USE_CUTOFF = False
    gemc.USE_CELL_LIST = False
    gemc.SAVE_FINAL_IMAGE = False
    gemc.INTERACTIVE = False
    gemc.RNG_SEED = 123

    gemc.validate_parameters()
    t0 = time.perf_counter()
    box1, box2, histories, _ = gemc.run_simulation(progress_interval=0)
    elapsed = time.perf_counter() - t0

    rho_liq_arr = np.maximum(histories["rho1"], histories["rho2"])
    n_cycles = len(rho_liq_arr)
    start = int(n_cycles * EQUILIBRATION_FRACTION)
    rho_liq_avg = float(np.mean(rho_liq_arr[start:])) if start < n_cycles else float(rho_liq_arr[-1])
    rho_liq_g = rho_lj_to_g_cm3(rho_liq_avg)

    return elapsed, rho_liq_g


def run_rust_gemc(n: int) -> tuple[float, float]:
    """Rust GEMC を実行し、(elapsed_s, rho_liq_g_cm3) を返す"""
    result = subprocess.run(
        [
            "cargo",
            "run",
            "--release",
            "--bin",
            "argon_bench",
            "--",
            "--n",
            str(n),
            "--cycles",
            str(CYCLES),
            "--t-k",
            str(int(T_K)),
        ],
        cwd=RUST_MC_DIR,
        capture_output=True,
        text=True,
        timeout=3600,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Rust 実行失敗: {result.stderr}")

    data = json.loads(result.stdout.strip())
    return data["elapsed_s"], data["rho_liq"]


def main():
    print("=== Python / Rust GEMC ベンチマーク (T=114 K, cycles={}) ===\n".format(CYCLES))
    print(f"N のリスト: {N_VALUES}\n")
    print(f"出力先: {BENCHMARK_DIR}\n")

    n_list = []
    py_elapsed = []
    py_rho_liq = []
    rs_elapsed = []
    rs_rho_liq = []

    for n in N_VALUES:
        print(f"--- N = {n} ---")
        # Python
        print("  Python 実行中...")
        try:
            e, r = run_python_gemc(n)
            py_elapsed.append(e)
            py_rho_liq.append(r)
            print(f"    elapsed = {e:.2f} s, rho_liq = {r:.4f} g/cm³")
        except Exception as ex:
            print(f"    Python エラー: {ex}")
            py_elapsed.append(float("nan"))
            py_rho_liq.append(float("nan"))

        # Rust
        print("  Rust 実行中...")
        try:
            e, r = run_rust_gemc(n)
            rs_elapsed.append(e)
            rs_rho_liq.append(r)
            print(f"    elapsed = {e:.2f} s, rho_liq = {r:.4f} g/cm³")
        except Exception as ex:
            print(f"    Rust エラー: {ex}")
            rs_elapsed.append(float("nan"))
            rs_rho_liq.append(float("nan"))

        n_list.append(n)
        print()

    # CSV に結果を保存
    csv_path = BENCHMARK_DIR / "benchmark_results.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("N,py_elapsed_s,py_rho_liq_g_cm3,rs_elapsed_s,rs_rho_liq_g_cm3\n")
        for i, n in enumerate(n_list):
            f.write(
                f"{n},{py_elapsed[i]:.6f},{py_rho_liq[i]:.6f},"
                f"{rs_elapsed[i]:.6f},{rs_rho_liq[i]:.6f}\n"
            )
    print(f"結果を {csv_path} に保存しました")

    # プロット
    try:
        import japanize_matplotlib
    except ImportError:
        pass

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

    ax1.plot(n_list, py_elapsed, "o-", label="Python", color="tab:blue", markersize=6)
    ax1.plot(n_list, rs_elapsed, "s-", label="Rust", color="tab:orange", markersize=6)
    ax1.set_xlabel("N")
    ax1.set_ylabel("計算時間 [秒]")
    ax1.set_title("計算時間")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(n_list, py_rho_liq, "o-", label="Python", color="tab:blue", markersize=6)
    ax2.plot(n_list, rs_rho_liq, "s-", label="Rust", color="tab:orange", markersize=6)
    ax2.set_xlabel("N")
    ax2.set_ylabel("液相密度 ρ_liq [g/cm³]")
    ax2.set_title("液相密度（生産相平均）")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    fig.suptitle(f"Argon GEMC ベンチマーク (T={T_K} K, cycles={CYCLES})")
    fig.tight_layout()

    output_path = BENCHMARK_DIR / "benchmark_python_rust_T114K.png"
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"グラフを {output_path} に保存しました")
    plt.close(fig)


if __name__ == "__main__":
    main()
