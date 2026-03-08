# Presentation Script (English, 2–3 minutes)

---

## Slide 1: Monte Carlo Simulation

I performed a Monte Carlo simulation of Lennard-Jones fluids.

First, I ran a two-dimensional simulation under the Lennard-Jones potential. The molecular motion looked reasonable, but I wanted to verify that the implementation was correct. So I decided to calculate the argon vapor pressure curve.

---

## Slide 2: Argon Vapor Pressure Curve — Implementation

To compute the vapor pressure curve, I implemented a three-dimensional Gibbs Ensemble Monte Carlo, or GEMC, in Python. GEMC simulates vapor–liquid coexistence using two boxes that exchange particles and volume.

The Python implementation worked, but it was too slow. So I migrated the code to Rust. As you can see in this table, for N equals 20 particles and 40,000 steps at 114 Kelvin, Python took about 273 seconds, while Rust took only 0.3 seconds. That’s a speedup of about 910 times.

---

## Slide 3: Argon Vapor Pressure Curve — Results

After the migration, I ran the simulation at multiple temperatures and obtained the vapor pressure curve. This plot shows the liquid and gas phase densities as a function of temperature. The results agree well with prior studies.

---

## Slide 4: Comparison with Experimental Data

This final plot compares our Lennard-Jones model with experimental data from Vargaftik. As you can see, the simulation and experiment match closely across the temperature range. This confirms that our implementation is correct.

Thank you for your attention.

---

## Timing Guide

| Slide | Approx. duration |
|-------|------------------|
| 1 | 30–40 sec |
| 2 | 50–60 sec |
| 3 | 25–30 sec |
| 4 | 25–30 sec |
| **Total** | **2–3 min** |

---

## Word Count

~320 words (at ~120 words/min ≈ 2.5 min)
