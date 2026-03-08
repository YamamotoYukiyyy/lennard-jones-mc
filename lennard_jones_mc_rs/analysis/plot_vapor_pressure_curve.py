#!/usr/bin/env python3
"""argon_vle_multitemp_rs.csv から蒸気圧曲線（気液共存曲線）を描画"""

import csv
import os

os.environ.setdefault("MPLBACKEND", "Agg")

from pathlib import Path

import matplotlib.pyplot as plt

try:
    import japanize_matplotlib
except ImportError:
    pass

SCRIPT_DIR = Path(__file__).resolve().parent
CSV_PATH = SCRIPT_DIR.parent / "results" / "argon_vle_multitemp_rs.csv"
OUTPUT_PATH = SCRIPT_DIR.parent / "results" / "argon_vle_vapor_pressure_curve.png"


def main():
    t_k = []
    rho_liq_g = []
    rho_vap_g = []

    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t_k.append(float(row["T_K"]))
            rho_liq_g.append(float(row["rho_liq_g_cm3"]))
            rho_vap_g.append(float(row["rho_vap_g_cm3"]))

    fig, ax = plt.subplots(figsize=(7, 6))

    # 横軸: 密度 [g/cm³], 縦軸: 温度 [K]
    ax.plot(rho_liq_g, t_k, "o-", label="液相", color="tab:blue", markersize=6)
    ax.plot(rho_vap_g, t_k, "s-", label="気相", color="tab:orange", markersize=6)
    ax.set_xlabel("ρ [g/cm³]")
    ax.set_ylabel("T [K]")
    ax.set_title("Argon GEMC 蒸気圧曲線 (N=500, cycles=10000, r_c=3σ)")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
    print(f"グラフを {OUTPUT_PATH} に保存しました")
    plt.close(fig)


if __name__ == "__main__":
    main()
