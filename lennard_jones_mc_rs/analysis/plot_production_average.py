#!/usr/bin/env python3
"""N30000 の密度履歴から生産相平均を計算し、蒸気圧曲線をプロット"""

import csv
import os
import re

os.environ.setdefault("MPLBACKEND", "Agg")

from pathlib import Path

import matplotlib.pyplot as plt

try:
    import japanize_matplotlib
except ImportError:
    pass

# アルゴン単位変換（Chialvo & Horita 2003）
ARGON_SIGMA_CM = 3.374e-8
ARGON_MOLAR_MASS = 39.948
N_AVOGADRO = 6.02214076e23
EQUILIBRATION_FRACTION = 0.3


def rho_lj_to_g_cm3(rho_star: float) -> float:
    """LJ 無次元密度を g/cm³ に変換"""
    return rho_star * (ARGON_MOLAR_MASS / N_AVOGADRO) / (ARGON_SIGMA_CM**3)


def main():
    script_dir = Path(__file__).resolve().parent
    results_dir = script_dir.parent / "results"
    
    history_files = []
    for n_dir in ["N30000", "N40000"]:
        n_path = results_dir / n_dir
        if n_path.exists():
            history_files.extend(sorted(n_path.glob("argon_vle_density_history_T*K.csv")))

    t_k_list = []
    rho_liq_avg_g = []
    rho_vap_avg_g = []

    for path in history_files:
        m = re.search(r"T(\d+(?:\.\d+)?)K", path.stem)
        if not m:
            continue
        t_k = float(m.group(1))

        cycles = []
        rho_liq = []
        rho_vap = []

        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cycles.append(int(row["cycle"]))
                rho_liq.append(float(row["rho_liq"]))
                rho_vap.append(float(row["rho_vap"]))

        n = len(rho_liq)
        start = int(n * EQUILIBRATION_FRACTION)
        if start >= n:
            continue

        rho_liq_avg = sum(rho_liq[start:]) / (n - start)
        rho_vap_avg = sum(rho_vap[start:]) / (n - start)

        t_k_list.append(t_k)
        rho_liq_avg_g.append(rho_lj_to_g_cm3(rho_liq_avg))
        rho_vap_avg_g.append(rho_lj_to_g_cm3(rho_vap_avg))

    if not t_k_list:
        print("密度履歴ファイルが見つかりません")
        return

    fig, ax = plt.subplots(figsize=(7, 6))

    ax.plot(rho_liq_avg_g, t_k_list, "o", label="液相", color="tab:blue", markersize=6)
    ax.plot(rho_vap_avg_g, t_k_list, "s", label="気相", color="tab:orange", markersize=6)
    ax.set_xlabel("ρ [g/cm³]")
    ax.set_ylabel("T [K]")
    ax.set_title("Argon GEMC 蒸気圧曲線（N=500, cycles=30000, cutoff なし）")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    fig.tight_layout()

    output_path = (script_dir.parent / "results") / "argon_vle_production_average.png"
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"グラフを {output_path} に保存しました")
    plt.close(fig)


if __name__ == "__main__":
    main()
