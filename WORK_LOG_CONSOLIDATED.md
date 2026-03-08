# 統合ログ：CompPhysHack プロジェクト

- 作成日: 2026-03-08
- 更新日: 2026-03-08
- 対象: Lennard-Jones MC / GEMC の開発・検証・比較

---

## 1. プロジェクト全体の構成

```
CompPhysHack/
├── exercise/
│   ├── lennard_jones_mc/          # Python 版（2D MC, 3D MC, 3D GEMC）
│   ├── lennard_jones_mc_rs/       # Rust 版（移植 + argon 専用バイナリ）
│   ├── lennard_jones_mc_rs_before_fix/  # 修正前 Rust 版の計算結果
│   ├── classical-mc-simple/       # 古典 MC（Ising, XY 模型）
│   ├── ising_chain/              # 1D Ising 鎖
│   └── ITensor/                  # テンソルネットワーク
├── lecture/                      # 講義資料
└── codex-work/                   # 作業用
```

---

## 2. ディレクトリ別ログ

### 2.1 `exercise/lennard_jones_mc/` — Python 版

| 項目 | 内容 |
|------|------|
| **目的** | Lennard-Jones 流体の 2D/3D MC および GEMC の教育用実装 |
| **主なファイル** | `lennard_jones_mc.py` (2D), `lennard_jones_mc_3d.py` (3D), `lennard_jones_gemc_3d.py` (GEMC), `lj_core.py` (共通部), `argon_gemc_run.py` (アルゴン実行) |
| **実行** | `argon_gemc_run.py` で N=500, C=10000, cutoff=3σ の文献条件で実行 |
| **実施したこと** | 3D MC 追加 → GEMC 追加 → cutoff/cell list 導入 → アルゴン VLE 1 点試算 → 進捗表示・単位変換・生産相平均 |

### 2.2 `exercise/lennard_jones_mc_rs/` — Rust 版（メイン）

| 項目 | 内容 |
|------|------|
| **目的** | Python 版の Rust 移植。計算速度の大幅向上（約 50〜100 倍） |
| **主なファイル** | `src/gemc_3d.rs`, `src/bin/argon.rs`, `argon_compare.rs`, `argon_vle.rs` |
| **実施したこと** | cell list 重複排除バグ修正、生産相平均出力、進捗表示、単位変換、複数温度 VLE |
| **実行** | `cargo run --bin argon_vle` で複数温度の気液共存を計算 |

### 2.3 `exercise/lennard_jones_mc_rs/N30000/` — 30,000 サイクル結果

| 項目 | 内容 |
|------|------|
| **目的** | cycles=30,000 で複数温度の気液共存を計算した結果の保存 |
| **含まれるファイル** | `argon_vle_multitemp_rs.csv`, `argon_vle_density_history_T*K.csv`, `plot_argon_density.py`, `plot_vapor_pressure_curve.py`, `plot_production_average.py` |
| **実施したこと** | 各温度の密度履歴を CSV 保存、蒸気圧曲線のプロット、生産相平均のプロット |

### 2.4 `exercise/lennard_jones_mc_rs/N40000/` — 40,000 サイクル結果

| 項目 | 内容 |
|------|------|
| **目的** | cycles=40,000 で複数温度の気液共存を計算した結果の保存 |
| **含まれるファイル** | `argon_vle_multitemp_rs.csv`, `argon_vle_density_history_T*K.csv`, `plot_argon_density.py`, `plot_production_average.py` |
| **実施したこと** | 全温度の密度履歴プロット（単位 g/cm³）、生産相平均プロット |

### 2.4b `exercise/lennard_jones_mc_benchmark/` — Python/Rust ベンチマーク

| 項目 | 内容 |
|------|------|
| **目的** | T=114 K, N=20〜100, cycles=40000 で Python と Rust の計算時間・液相密度を比較 |
| **含まれるファイル** | `benchmark_python_rust.py`, `run_benchmark.sh`, `README.md` |
| **出力** | `benchmark_python_rust_T114K.png`, `benchmark_results.csv` |

### 2.5 `exercise/lennard_jones_mc_rs/without_cutoff/` — cutoff なし結果

| 項目 | 内容 |
|------|------|
| **目的** | cutoff なし（全粒子総当たり）で複数温度の気液共存を計算 |
| **含まれるファイル** | `argon_vle_multitemp_rs.csv`, `argon_vle_density_history_T*K.csv`, `argon_gemc_T136K_nocutoff_*`, T125K/T130K の密度履歴 PNG |
| **実施したこと** | 文献とのずれの原因調査（cutoff あり vs なし）のため T=136 K での単点計算も実施 |

### 2.6 `exercise/lennard_jones_mc_rs/temperature_variation/` — 文献比較

| 項目 | 内容 |
|------|------|
| **目的** | Chialvo & Horita (2003) 論文との実装比較 |
| **含まれるファイル** | `CHIALVO_HORITA_2003_comparison.md`, `plot_vapor_pressure_curve.py`, `plot_argon_density.py` |
| **実施したこと** | 論文との相違点・長距離補正の欠如などを文書化 |

### 2.7 `exercise/lennard_jones_mc_rs/rust_prefix_results/` — 修正前 Rust 版の結果

| 項目 | 内容 |
|------|------|
| **目的** | cell list の重複排除バグ修正**前**の Rust 版で計算した結果を分離保存 |
| **含まれるファイル** | `argon_gemc_summary_*_rs_prefix.json`, `argon_gemc_density_history_*_rs_prefix.csv` |
| **注意** | Volume 受理率が極端に低く（約 1–2%）、エネルギー計算に誤りあり |

### 2.8 `exercise/lennard_jones_mc_rs_before_fix/` — 修正前 Rust 版ソース

| 項目 | 内容 |
|------|------|
| **目的** | 修正前の Rust ソースコードを保存（比較・参照用） |
| **含まれるファイル** | `src/`, `bin/` の Rust ソースコード |

---

## 3. 進捗の時系列（PROGRESS シリーズ）

| No. | ファイル | 内容 |
|-----|----------|------|
| 01 | PROGRESS_01_3D_MC | 3D Lennard-Jones MC 追加 |
| 02 | PROGRESS_02_GEMC | 3D GEMC 追加 |
| 03 | PROGRESS_03_CUTOFF_CELLLIST | Cutoff + Cell List 導入 |
| 04 | PROGRESS_04_ARGON_VLE | アルゴン VLE 1 点試算 |
| 05 | PROGRESS_05_N100_C5000 | N=100, cycles=5000 の実行 |
| 06 | PROGRESS_06_RUST_MIGRATION | Rust 移行 |
| 07 | PROGRESS_07_ADDITIONAL_FEATURES | 追加機能（進捗表示・単位変換・複数温度 VLE） |

---

## 4. 主な機能・実装の一覧

| 機能 | Python | Rust |
|------|--------|------|
| 生産相平均 | `argon_gemc_run.py` で equilibration 30% 捨て、70% で平均 | `production_average_phase_density()` |
| 進捗表示 | 1000 サイクルごと、0-based | `progress_interval` |
| 単位変換 | rho* と g/cm³ の両方で表示 | `rho_lj_to_g_cm3()` |
| 複数温度 VLE | — | `argon_vle.rs` で 84 K〜148 K |
| 密度履歴 CSV | — | 各温度ごとに `argon_vle_density_history_T*K.csv` を保存 |

---

## 5. 文献との相違点（文献比較の要約）

| 項目 | 文献 | 現在の実装 |
|------|------|------------|
| 長距離補正（LRC） | 適用 | **未実装** |
| サイクル数 | 30,000 | 10,000〜200,000（argon_vle は 200,000） |
| 受理率制御 | 適応的に Δ_max, Δ_V_max を調整 | 固定値 |
| cutoff | r_c ≥ 3σ | 3σ または cutoff なし |

---

## 6. 実行方法のまとめ

| 目的 | コマンド |
|------|----------|
| Python 単一温度 GEMC | `python exercise/lennard_jones_mc/argon_gemc_run.py` |
| Rust 単一温度 GEMC | `cargo run --bin argon_compare` |
| Rust 複数温度 VLE | `cargo run --bin argon_vle`（実行ディレクトリで CSV が出力される） |
| 生産相平均プロット | `python exercise/lennard_jones_mc_rs/N30000/plot_production_average.py` |
| 蒸気圧曲線プロット | `python exercise/lennard_jones_mc_rs/N30000/plot_vapor_pressure_curve.py` |
| ベンチマーク | `python exercise/lennard_jones_mc_benchmark/benchmark_python_rust.py` |

---

## 7. セッションログ（直近の変更）

| 日付 | 変更内容 |
|------|----------|
| 2026-03-08 | N40000/plot_argon_density.py: 全温度でプロット、密度を g/cm³ に変換、単位を軸に明記 |
| 2026-03-08 | lennard_jones_mc_benchmark: ベンチマーク用ディレクトリを新設、benchmark_python_rust.py, run_benchmark.sh, README.md を配置 |
| 2026-03-08 | argon_vle.rs: サイクル数を 200,000 に統一（全温度） |
| 2026-03-08 | argon_bench.rs: ベンチマーク用 Rust バイナリを追加（--n, --cycles, --t-k で CLI 指定） |

---

## 8. 関連ドキュメント

- `exercise/PROGRESS_00_INDEX.md` — 進捗ログのインデックス
- `exercise/COMPARISON_PYTHON_RUST.md` — Python と Rust の計算結果比較
- `exercise/lennard_jones_mc_rs/temperature_variation/CHIALVO_HORITA_2003_comparison.md` — 文献との実装比較
