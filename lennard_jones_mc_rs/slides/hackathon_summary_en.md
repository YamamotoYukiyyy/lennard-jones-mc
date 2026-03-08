---
marp: true
theme: uncover
size: 16:9
paginate: true
header: 'Monte Carlo Simulation | Hackathon Summary'
footer: 'CompPhysHack'
title: Monte Carlo Simulation
style: |
  section { padding: 48px 64px; text-align: left; }
  h1 { font-size: 1.6em; margin-bottom: 0.3em; text-align: left; border-left: 6px solid #0066cc; padding-left: 16px; }
  h1 .sub { font-size: 0.6em; color: #666; font-weight: normal; margin-left: 0.5em; }
  h2 { font-size: 1.2em; color: #333; margin-bottom: 0.4em; text-align: left; }
  ul, table { text-align: left; }
  table { white-space: nowrap; }
  table td, table th { white-space: nowrap; }
  ul { line-height: 1.8; }
  strong { color: #0066cc; }
  .slide1 li:nth-child(3) { white-space: nowrap; }
---

<!-- _class: slide1 -->

# Monte Carlo Simulation

- **Model**: 2D Lennard-Jones potential
- **Result**: Molecular motion looked reasonable
- **Next goal**: Verify implementation correctness<br>　　　　　→ Calculate argon vapor pressure curve

---

# Argon Vapor Pressure Curve

- **GEMC** = Gibbs Ensemble MC (vapor–liquid coexistence)
- Python implementation → too slow → migrated to Rust → speedup

**Computation time comparison (no cutoff, no cell list)**

| Condition | Python (s) | Rust (s) | Speedup |
|:----------|-----------:|---------:|--------:|
| N=20, T=114K<br>40000 steps | 273.3 | 0.30 | ~910× |

---

# Argon Vapor Pressure Curve

- Results agree well with prior studies

![vapor_pressure_curve.png](vapor_pressure_curve.png)

---

# Argon Vapor Pressure Curve

![vapor_pressure_comparison.png](vapor_pressure_comparison.png)
