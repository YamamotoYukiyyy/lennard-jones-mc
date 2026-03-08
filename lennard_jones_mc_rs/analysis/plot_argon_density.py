#!/usr/bin/env python3
"""Argon GEMC 密度履歴のグラフ作成"""

import csv
import os

# 非GUIバックエンド（表示なしで保存のみ）
os.environ.setdefault("MPLBACKEND", "Agg")

from pathlib import Path

import matplotlib.pyplot as plt

try:
    import japanize_matplotlib
except ImportError:
    pass

CSV_PATH = Path(__file__).parent.parent / "results" / "N30000" / "argon_vle_density_history_T148K.csv"
OUTPUT_PATH = Path(__file__).parent.parent / "results" / "N30000" / "argon_vle_density_history_T148K.png"


def main():
    cycles = []
    rho1 = []
    rho2 = []
    rho_liq = []
    rho_vap = []

    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cycles.append(int(row["cycle"]))
            rho1.append(float(row["rho1"]))
            rho2.append(float(row["rho2"]))
            rho_liq.append(float(row["rho_liq"]))
            rho_vap.append(float(row["rho_vap"]))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # 上段: Box density (rho1, rho2)
    ax1.plot(cycles, rho1, label="rho1", alpha=0.8, linewidth=0.8)
    ax1.plot(cycles, rho2, label="rho2", alpha=0.8, linewidth=0.8)
    ax1.set_ylabel("Box density")
    ax1.set_ylim(0.0, 0.8)
    ax1.legend(loc="upper right")
    ax1.grid(True, alpha=0.3)

    # 下段: Phase density (rho_liq, rho_vap)
    ax2.plot(cycles, rho_liq, label="rho_liq", alpha=0.8, linewidth=0.8)
    ax2.plot(cycles, rho_vap, label="rho_vap", alpha=0.8, linewidth=0.8)
    ax2.set_xlabel("Cycle")
    ax2.set_ylabel("Phase density")
    ax2.set_ylim(0.0, 0.8)
    ax2.legend(loc="upper right")
    ax2.grid(True, alpha=0.3)

    fig.suptitle("Argon GEMC density history (N=500, cycles=30000, r_c=3σ, Chialvo & Horita 2003)")
    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
    print(f"グラフを {OUTPUT_PATH} に保存しました")
    plt.close(fig)


if __name__ == "__main__":
    main()
