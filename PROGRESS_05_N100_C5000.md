# 進捗ログ 05: N=100, cycles=5000 の実行

- 日付: 2026-03-07
- 参照: `lennard_jones_mc/WORK_LOG_PROGRESS_SUMMARY_2026-03-07.md`

## 概要

cutoff + cell list を用いて N=100, cycles=5000 でアルゴン GEMC を実行し、収束グラフとデータを保存した。

## 実行条件

- T = 100 K, T* = 0.87336
- N_total = 100, N_cycles = 5000
- use_cutoff = True, cutoff_radius = 1.5, cell_size = 1.5

## 結果

- 計算時間: 716.19 s（0.143 s/cycle）
- 最終状態: Box 1 N=69 rho=0.25, Box 2 N=31 rho=0.51
- rho_liq = 0.51, rho_vap = 0.25
- 受理率: displacement 0.46, volume 0.45, transfer 0.07

## 保存した出力

- `argon_gemc_convergence_N100_C5000_cutoff_celllist.png`
- `argon_gemc_density_history_N100_C5000_cutoff_celllist.csv`
- `argon_gemc_summary_N100_C5000_cutoff_celllist.json`

## 文献条件との差

- 文献: r_c ≈ 3.0 σ
- 本実行: cutoff_radius = 1.5（軽量設定）
