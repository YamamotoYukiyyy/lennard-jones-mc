#!/usr/bin/env python3
"""
Benchmark: Exact Diagonalization vs DMRG for 1D Ising chain.

Compares execution time for finding ground state energy.
"""

import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCRIPT_DIR = Path(__file__).resolve().parent


def run_exact_diagonalization(N: int, python_cmd: str = "python") -> tuple[float, float]:
    """Run exact diagonalization, return (energy, time_seconds)."""
    cmd = [python_cmd, "exact_diagonalization.py", str(N)]
    t0 = time.perf_counter()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=SCRIPT_DIR,
        timeout=300,
    )
    elapsed = time.perf_counter() - t0

    if result.returncode != 0:
        print(f"ED failed for N={N}: {result.stderr}", file=sys.stderr)
        return float("nan"), float("nan")

    energy = float("nan")
    for line in result.stdout.splitlines():
        if line.startswith("ENERGY:"):
            energy = float(line.split(":")[1].strip())
            break

    return energy, elapsed


def run_dmrg(N: int, dmrg_path: str = "./ising_dmrg") -> tuple[float, float]:
    """Run DMRG, return (energy, time_seconds)."""
    if not Path(dmrg_path).exists():
        print(f"Error: {dmrg_path} not found. Run 'make' first.", file=sys.stderr)
        return float("nan"), float("nan")

    cmd = [dmrg_path, str(N)]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=SCRIPT_DIR,
        timeout=300,
    )

    if result.returncode != 0:
        print(f"DMRG failed for N={N}: {result.stderr}", file=sys.stderr)
        return float("nan"), float("nan")

    energy = float("nan")
    elapsed = float("nan")
    for line in result.stdout.splitlines():
        if line.startswith("ENERGY:"):
            energy = float(line.split(":")[1].strip())
        elif line.startswith("TIME_SECONDS:"):
            elapsed = float(line.split(":")[1].strip())

    return energy, elapsed


def run_benchmark(
    n_values: list[int],
    python_cmd: str = "python",
) -> tuple[list[int], list[float], list[float], list[float], list[float]]:
    """Run both methods for each N. Returns (N_list, ed_times, dmrg_times, ed_energies, dmrg_energies)."""
    ed_times = []
    dmrg_times = []
    ed_energies = []
    dmrg_energies = []

    for N in n_values:
        print(f"Running N={N}...", flush=True)

        e_ed, t_ed = run_exact_diagonalization(N, python_cmd)
        ed_energies.append(e_ed)
        ed_times.append(t_ed)

        e_dmrg, t_dmrg = run_dmrg(N)
        dmrg_energies.append(e_dmrg)
        dmrg_times.append(t_dmrg)

        print(f"  ED:   {t_ed:.3f}s, E={e_ed:.6f}")
        print(f"  DMRG: {t_dmrg:.3f}s, E={e_dmrg:.6f}")

    return n_values, ed_times, dmrg_times, ed_energies, dmrg_energies


def plot_results(
    n_values: list[int],
    ed_times: list[float],
    dmrg_times: list[float],
    output_path: str = "benchmark_comparison.png",
):
    """Plot execution time comparison."""
    fig, ax = plt.subplots(figsize=(8, 5))

    n_arr = np.array(n_values)
    ed_arr = np.array(ed_times)
    dmrg_arr = np.array(dmrg_times)

    # Filter out NaN for plotting
    valid_ed = ~np.isnan(ed_arr)
    valid_dmrg = ~np.isnan(dmrg_arr)

    ax.semilogy(
        n_arr[valid_ed],
        ed_arr[valid_ed],
        "o-",
        label="Exact Diagonalization",
        color="#e74c3c",
        linewidth=2,
        markersize=8,
    )
    ax.semilogy(
        n_arr[valid_dmrg],
        dmrg_arr[valid_dmrg],
        "s-",
        label="DMRG",
        color="#3498db",
        linewidth=2,
        markersize=8,
    )

    ax.set_xlabel("Number of sites N", fontsize=12)
    ax.set_ylabel("Execution time (seconds)", fontsize=12)
    ax.set_title("1D Ising Chain: Ground State Computation Time", fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, which="both", alpha=0.3)
    ax.set_xlim(min(n_values) - 0.5, max(n_values) + 0.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\nPlot saved to {output_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Benchmark ED vs DMRG")
    parser.add_argument(
        "--python",
        default="python",
        help="Python interpreter (e.g. python3 or path to venv)",
    )
    parser.add_argument(
        "--max-n",
        type=int,
        default=20,
        help="Maximum N for ED (DMRG runs for same N values)",
    )
    parser.add_argument(
        "--min-n",
        type=int,
        default=4,
        help="Minimum N",
    )
    parser.add_argument(
        "--step",
        type=int,
        default=2,
        help="Step for N values",
    )
    args = parser.parse_args()

    n_values = list(range(args.min_n, args.max_n + 1, args.step))
    if not n_values:
        n_values = [args.min_n]

    print("=" * 50)
    print("Benchmark: Exact Diagonalization vs DMRG")
    print("=" * 50)
    print(f"N values: {n_values}")
    print()

    n_list, ed_times, dmrg_times, ed_energies, dmrg_energies = run_benchmark(
        n_values, args.python
    )

    # Summary table
    print()
    print("Summary:")
    print(f"{'N':>4} {'ED (s)':>10} {'DMRG (s)':>10} {'E_ED':>12} {'E_DMRG':>12}")
    print("-" * 52)
    for i, N in enumerate(n_list):
        print(f"{N:>4} {ed_times[i]:>10.4f} {dmrg_times[i]:>10.4f} "
              f"{ed_energies[i]:>12.6f} {dmrg_energies[i]:>12.6f}")

    plot_results(n_list, ed_times, dmrg_times)


if __name__ == "__main__":
    main()
