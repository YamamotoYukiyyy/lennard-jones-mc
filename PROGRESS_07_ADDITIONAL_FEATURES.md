# 進捗ログ 07: 追加機能

- 日付: 2026-03-07

## 概要

進捗表示、単位変換、複数温度 VLE 計算などの追加機能を実装した。

## 1. 1000 サイクルごとの進捗表示

- **Python**: `run_simulation(progress_interval=1000, progress_callback=...)` を追加
- **Rust**: `GemcParams.progress_interval` を追加、cycle % 1000 == 0 で標準出力に進捗表示
- サイクルは 0-based で表示

## 2. SI 単位系 + LJ 単位系の併記

- 密度を rho* (LJ) と g/cm³ (SI) の両方で表示
- アルゴン: ρ [g/cm³] = ρ* × (M/N_A) / σ³ ≈ ρ* × 1.727
- **Python**: `argon_gemc_run.py` に `rho_lj_to_g_cm3()`, `format_density()` を追加
- **Rust**: `rho_lj_to_g_cm3()` を公開、`GemcParams` に `sigma_cm`, `molar_mass_g` を追加

## 3. Python / Rust 比較（N500, C10000）

- 同一条件（cutoff 3.0, cell_size 3.0, T*=0.873）で両方実行
- Rust: 約 528 秒、rho_liq≈0.73, rho_vap≈0.008
- Python: 長時間要するため、ターミナルで直接実行を推奨

## 4. 複数温度 VLE 計算（argon_vle）

- 温度: 84, 90, 102, 114, 125, 130, 136, 142, 148 K
- 文献条件: N=500, cycles=10,000, r_c=3σ
- 出力: `argon_vle_multitemp_rs.csv`（T_K, T_star, rho_liq, rho_vap, g/cm³）
