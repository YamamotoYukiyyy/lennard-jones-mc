# Lennard-Jones Monte Carlo - ベンチマーク比較

Python版と Rust版の計算性能・精度を比較するベンチマーク。

## ディレクトリ構成

```
lennard_jones_mc_benchmark/
├── src/
│   ├── benchmark_python_rust.py    # ベンチマークスクリプト
│   └── run_benchmark.sh            # 実行シェル
├── results/                        # 比較結果（Git除外）
│   ├── benchmark_results.csv       # 計測データ
│   └── benchmark_python_rust_T114K.png  # グラフ
├── .gitignore                      # Git除外リスト
└── README.md                       # このファイル
```

## 実行方法

### Python スクリプト（推奨）

```bash
cd src
python benchmark_python_rust.py
```

実行結果：
- `../results/benchmark_results.csv` - N別の計算時間・密度データ
- `../results/benchmark_python_rust_T114K.png` - 比較グラフ

### シェルスクリプト

```bash
bash src/run_benchmark.sh
```

## ベンチマーク条件

**温度**: T=114 K（液相安定域）
**パーティクル数**: N=20～100（可変）
**サイクル数**: cycles=40,000
**実装**: 
- Python: `../lennard_jones_mc/src/argon_gemc_run.py`
- Rust: `cargo run --bin argon_bench`

## 計測項目

- 実行時間（秒）
- 液相平均密度（g/cm³）
- 気相平均密度（g/cm³）
- 受理率（粒子移動）

## 期待される結果

| 項目 | Python | Rust | 備考 |
|------|--------|------|------|
| **実行時間** | 10-50秒 | 0.1-0.5秒 | 約50-100倍高速化 |
| **液相密度** | 0.70～0.75 g/cm³ | 0.70～0.75 g/cm³ | ほぼ同一 |
| **気相密度** | 0.001～0.003 g/cm³ | 0.001～0.003 g/cm³ | ほぼ同一 |

## 関連資料

- `../lennard_jones_mc/` - Python版実装
- `../lennard_jones_mc_rs/` - Rust版実装
- `../COMPARISON_PYTHON_RUST.md` - 詳細比較分析
