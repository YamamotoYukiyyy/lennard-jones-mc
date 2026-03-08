# Lennard-Jones Monte Carlo Simulation

A comprehensive suite of Monte Carlo simulations for Lennard-Jones systems, implementing both Python and Rust versions with benchmarking capabilities.

## Overview

This repository contains three main implementations for Lennard-Jones Monte Carlo simulations:

### 1. **lennard_jones_mc** - Python Implementation
Pure Python implementation of Lennard-Jones Monte Carlo simulations with support for:
- Standard MC simulations
- 3D simulations
- Grand Canonical Ensemble (GEMC)
- Flexible cutoff and cell list implementations
- Analysis tools for phase diagrams and VLE calculations

### 2. **lennard_jones_mc_rs** - Rust Implementation
High-performance Rust implementation offering:
- Fast and efficient simulations
- Same algorithms as Python version
- Benchmarking against Python implementation
- Native performance optimizations

### 3. **lennard_jones_mc_benchmark** - Benchmarking Suite
Comprehensive benchmarking tools for:
- Performance comparison between Python and Rust
- Scaling analysis
- Memory usage profiling
- Result validation

## Getting Started

### Python Version
```bash
cd lennard_jones_mc
# Follow instructions in lennard_jones_mc/README.md
```

### Rust Version
```bash
cd lennard_jones_mc_rs
# Follow instructions in lennard_jones_mc_rs/README.md
```

### Benchmarking
```bash
cd lennard_jones_mc_benchmark
# Follow instructions in lennard_jones_mc_benchmark/README.md
```

## Features

- **Monte Carlo Simulations**: NVT and Grand Canonical Ensemble implementations
- **3D Simulations**: Full 3D support for realistic systems
- **Performance**: Both optimized Python and high-speed Rust versions
- **Analysis Tools**: Phase diagram generation, VLE calculations
- **Benchmarking**: Detailed performance comparison and profiling
- **Flexible Parameters**: Customizable cutoff, cell lists, and system parameters

## Repository Structure

```
.
├── lennard_jones_mc/              # Python implementation
├── lennard_jones_mc_rs/           # Rust implementation
└── lennard_jones_mc_benchmark/    # Benchmarking tools
```

## License

This project is provided as-is for research and educational purposes.

## Documentation

For detailed documentation and usage instructions, please refer to the README files in each subdirectory:
- [Python Implementation Guide](lennard_jones_mc/README.md)
- [Rust Implementation Guide](lennard_jones_mc_rs/README.md)
- [Benchmarking Guide](lennard_jones_mc_benchmark/README.md)
