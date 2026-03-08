# Lennard-Jones Monte Carlo - Rust版（高速実装）

3D Lennard-Jones 流体の Monte Carlo シミュレーション（GEMC）の高速 Rust 実装。
Python版から移植し、計算速度を約50-100倍向上させました。

## ディレクトリ構成

```
lennard_jones_mc_rs/
├── src/                         # Rustソースコード
│   ├── gemc_3d.rs              # 3D GEMC実装（主コア）
│   ├── lib.rs                  # ライブラリ定義
│   └── bin/
│       ├── argon.rs            # 単一温度実行
│       ├── argon_compare.rs    # Python版比較実行
│       ├── argon_vle.rs        # 複数温度VLE計算
│       └── argon_bench.rs      # ベンチマーク用
├── Cargo.toml                   # Rustマニフェスト
├── results/                     # 計算結果（Git除外）
│   ├── direct/                  # 直接実行結果
│   ├── N30000/                  # 30000サイクル結果
│   ├── N40000/                  # 40000サイクル結果
│   ├── archived/                # 修正前結果（参考）
│   ├── without_cutoff/          # cutoff無し実験
│   └── temperature_variation/   # 温度変化実験
├── analysis/                    # 解析・可視化スクリプト
│   ├── plot_argon_density.py
│   ├── plot_vapor_pressure_curve.py
│   └── plot_production_average.py
├── MIGRATION_NOTES.md           # Python→Rust移植記録
├── .gitignore                   # Git除外リスト
└── README.md                    # このファイル
```

## 実行方法

### 複数温度VLE計算（推奨）

```bash
cargo run --bin argon_vle --release
```

84K～148Kの複数温度でVLE曲線を計算。各温度200,000サイクル。
結果ファイル：
- `results/argon_vle_multitemp_rs.csv` - 各温度の平衡密度
- `results/argon_vle_density_history_T*K.csv` - 温度別密度履歴

### 単一温度実行

```bash
cargo run --bin argon_compare --release
```

T=114K で実行。結果は `results/direct/` に出力。

### ベンチマーク

```bash
cargo run --bin argon_bench --release -- --n 50 --cycles 10000 --t-k 114
```

CLIオプション：`--n`, `--cycles`, `--t-k`

## 主な特徴

| 機能 | 説明 |
|------|------|
| **高速化** | Cell List + cutoff で計算効率向上 |
| **複数温度** | 自動VLE計算（84～148K） |
| **精度** | Python版とほぼ同じ結果 |
| **単位変換** | LJ単位→g/cm³自動変換 |

## Python→Rust移植

詳細は `MIGRATION_NOTES.md` を参照。

**修正済み項目**
- Cell List重複排除バグ（2026-03-07）

**未実装項目**
- 長距離補正（LRC）
- 受理率適応制御

## 関連資料

- `../lennard_jones_mc/` - Python版（教育用）
- `../lennard_jones_mc_benchmark/` - ベンチマーク比較
- `../COMPARISON_PYTHON_RUST.md` - 言語別比較分析
