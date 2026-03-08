# 進捗ログ 04: アルゴン VLE 1 点試算

- 日付: 2026-03-07
- 参照: `lennard_jones_mc/WORK_LOG_ARGON_VLE_CHECK_2026-03-07.md`

## 概要

文献 Chialvo & Horita (2003) を意識して、アルゴンの気液共存域に相当する 1 点を試算し、計算時間と収束の度合いを確認した。

## 文献パラメータ

- epsilon/k = 114.5 K
- sigma = 3.374 Å
- T = 100 K → T* = 100/114.5 ≈ 0.87336

## 実行条件（総当たり版）

- N_total = 64, N_cycles = 2000
- cutoff なし

## 結果

- 計算時間: 192.83 s（0.0964 s/cycle）
- 最終状態: Box 1 N=61 rho=0.69, Box 2 N=3 rho=0.02
- 受理率: displacement 0.50, volume 0.35, transfer 0.005

## 解釈

- 気液分離は確認できた
- 2000 cycle では完全収束とは言いにくい
- 粒子交換受理率が低く、長時間計算または高速化が必要
- 論文条件 N=500, 3e4 cycles を純 Python にそのまま適用するのは重い
