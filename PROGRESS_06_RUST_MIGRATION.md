# 進捗ログ 06: Rust 移行

- 日付: 2026-03-07
- 参照: `lennard_jones_mc_rs/WORK_LOG_RUST_MIGRATION_2026-03-07.md`

## 概要

Python 版 lennard_jones_mc を Rust に移植し、計算速度の向上を図った。

## プロジェクト構成

```
lennard_jones_mc_rs/
├── Cargo.toml
├── src/
│   ├── lib.rs, lj_core.rs, mc_3d.rs, gemc_3d.rs
│   ├── main.rs
│   └── bin/
│       ├── argon.rs
│       ├── argon_compare.rs
│       └── argon_vle.rs
└── plot_argon_density.py
```

## 移植対応

| Python | Rust |
|--------|------|
| lj_core.py | lj_core.rs |
| lennard_jones_mc_3d.py | mc_3d.rs |
| lennard_jones_gemc_3d.py | gemc_3d.rs |

## 不具合修正: cell list の重複カウント

- **現象**: Volume 受理率が 1〜2%（Python は約 45%）
- **原因**: n_cells=1 のとき候補インデックスが重複し、エネルギーが約 27 倍に計算
- **修正**: HashSet で重複排除
- **結果**: Volume 受理率が約 55% に改善

## 文献条件への準拠

- N_total: 500, n_cycles: 30,000
- cutoff_radius: 3.0, cell_size: 3.0
- epsilon/k = 114.5 K, sigma = 3.374 Å
