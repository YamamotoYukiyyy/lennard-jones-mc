#!/usr/bin/env python3
"""
一次元イジング鎖 DMRG の結果を可視化するスクリプト

使い方:
  1. ./ising_dmrg を実行して ising_data.csv を生成
  2. python visualize.py で可視化
"""

import csv

import numpy as np
import matplotlib
matplotlib.use("Agg")  # ディスプレイ不要で画像保存
import matplotlib.pyplot as plt
from pathlib import Path

# フォント設定（数式はデフォルトで表示可能）
plt.rcParams["font.family"] = "sans-serif"


def load_data(filepath="ising_data.csv"):
    """ising_data.csv を読み込む"""
    if not Path(filepath).exists():
        print(f"Error: {filepath} not found.")
        print("Run ./ising_dmrg first.")
        return None

    with open(filepath, encoding="utf-8") as f:
        reader = csv.reader(f)

        # N, J, energy
        next(reader)  # header
        row = next(reader)
        N, J, energy = int(row[0]), float(row[1]), float(row[2])

        # site, Sz
        next(reader)  # header
        sites = []
        sz_vals = []
        for row in reader:
            if row[0] == "correlation_matrix":
                break
            sites.append(int(row[0]))
            sz_vals.append(float(row[1]))

        # correlation matrix
        corr = []
        for row in reader:
            corr.append([float(x) for x in row])

    return {
        "N": N,
        "J": J,
        "energy": energy,
        "sites": np.array(sites),
        "sz": np.array(sz_vals),
        "correlation": np.array(corr) if corr else None,
    }


def visualize(data):
    """データを可視化"""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))

    sites = data["sites"]
    sz = data["sz"]
    N = data["N"]
    J = data["J"]
    energy = data["energy"]
    corr = data["correlation"]

    # 1. 磁化プロファイル ⟨S^z⟩
    ax1 = axes[0]
    colors = np.where(sz > 0, "#e74c3c", "#3498db")  # 上向き: 赤, 下向き: 青
    ax1.bar(sites, sz, color=colors, edgecolor="black", linewidth=0.5)
    ax1.axhline(y=0, color="gray", linestyle="--", linewidth=0.8)
    ax1.set_xlabel("Site $i$")
    ax1.set_ylabel(r"$\langle S^z_i \rangle$")
    ax1.set_title("Magnetization profile")
    ax1.set_xlim(0, N + 1)
    ax1.set_ylim(-0.6, 0.6)

    # 2. 中心サイトとの相関 ⟨S^z_center S^z_j⟩
    ax2 = axes[1]
    center = N // 2
    if corr is not None and corr.size > 0:
        corr_center = corr[center - 1, :]  # 1-based center
        ax2.plot(sites, corr_center, "o-", color="#2ecc71", markersize=4)
        ax2.axhline(y=0, color="gray", linestyle="--", linewidth=0.8)
        ax2.axvline(x=center, color="orange", linestyle=":", alpha=0.7, label=f"Center (i={center})")
        ax2.set_xlabel("Site $j$")
        ax2.set_ylabel(r"$\langle S^z_{" + str(center) + r"} S^z_j \rangle$")
        ax2.set_title("Correlation with center site")
        ax2.legend()

    # 3. 相関行列のヒートマップ
    ax3 = axes[2]
    if corr is not None and corr.size > 0:
        im = ax3.imshow(
            corr,
            extent=[1, N, N, 1],
            aspect="auto",
            cmap="RdBu_r",
            vmin=-0.3,
            vmax=0.3,
        )
        ax3.set_xlabel("Site $i$")
        ax3.set_ylabel("Site $j$")
        ax3.set_title(r"Correlation matrix $\langle S^z_i S^z_j \rangle$")
        plt.colorbar(im, ax=ax3, label=r"$\langle S^z_i S^z_j \rangle$")

    fig.suptitle(
        f"1D Ising chain (N={N}, J={J:.1f}) ground state\n"
        f"Energy E = {energy:.6f}",
        fontsize=12,
    )
    plt.tight_layout()
    plt.savefig("ising_visualization.png", dpi=150, bbox_inches="tight")
    print("Saved to ising_visualization.png")


def main():
    data = load_data()
    if data is not None:
        visualize(data)


if __name__ == "__main__":
    main()
