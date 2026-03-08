#!/usr/bin/env python3
"""
Exact diagonalization for 1D Ising chain ground state.

Hamiltonian: H = -J sum_i S^z_i S^z_{i+1}

For the Ising model, H is diagonal in the S^z product basis.
We enumerate all 2^N states and compute eigenvalues directly.
"""

import numpy as np
import time


def sz_at_site(state: int, site: int) -> float:
    """S^z at site (1-indexed). state is bitstring: bit 0 = site 1, etc."""
    bit = (state >> (site - 1)) & 1
    return 0.5 if bit else -0.5  # up=+1/2, down=-1/2


def energy_of_state(state: int, N: int, J: float) -> float:
    """Energy of basis state |state> for H = -J sum S^z_i S^z_{i+1}."""
    e = 0.0
    for i in range(1, N):
        sz_i = sz_at_site(state, i)
        sz_ip1 = sz_at_site(state, i + 1)
        e -= J * sz_i * sz_ip1
    return e


def exact_diagonalization(N: int, J: float = 1.0):
    """
    Find ground state energy and wave function by exact diagonalization.

    Returns:
        energy: Ground state energy
        ground_state: Ground state vector (2^N array)
        elapsed: Computation time in seconds
    """
    t0 = time.perf_counter()

    dim = 2**N
    energies = np.empty(dim)

    for state in range(dim):
        energies[state] = energy_of_state(state, N, J)

    gs_idx = np.argmin(energies)
    energy = energies[gs_idx]

    ground_state = np.zeros(dim)
    ground_state[gs_idx] = 1.0

    elapsed = time.perf_counter() - t0
    return energy, ground_state, elapsed


def magnetization_profile(ground_state: np.ndarray, N: int) -> np.ndarray:
    """Compute <S^z> at each site for a product state (single basis state)."""
    # Find the non-zero component
    idx = np.argmax(np.abs(ground_state))
    sz_vals = np.zeros(N)
    for j in range(1, N + 1):
        sz_vals[j - 1] = sz_at_site(idx, j)
    return sz_vals


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Exact diagonalization for Ising chain")
    parser.add_argument("N", type=int, nargs="?", default=12, help="Number of sites")
    parser.add_argument("-J", type=float, default=1.0, help="Coupling constant")
    args = parser.parse_args()

    N = args.N
    J = args.J

    if N > 24:
        print(f"Warning: N={N} may use significant memory (2^{N} = {2**N} states)")

    energy, ground_state, elapsed = exact_diagonalization(N, J)

    # Exact value for ferromagnetic
    E_exact = -J * (N - 1) / 4.0

    print(f"N={N}, J={J}")
    print(f"Ground state energy: {energy:.12f}")
    print(f"Exact (ferromagnetic): {E_exact:.12f}")
    print(f"Error: {abs(energy - E_exact):.2e}")
    print(f"Time: {elapsed:.4f} s")
    print(f"TIME_SECONDS: {elapsed}")
    print(f"ENERGY: {energy}")


if __name__ == "__main__":
    main()
