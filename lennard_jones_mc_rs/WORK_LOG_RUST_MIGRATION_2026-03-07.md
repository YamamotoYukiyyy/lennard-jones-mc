# Rust 移行作業ログ

- 日付: 2026-03-07
- 対象ディレクトリ: `/Users/yamamoto/Desktop/CompPhysHack/exercise/lennard_jones_mc_rs`
- 目的: Python 版 `lennard_jones_mc` を Rust に移植し、計算速度の向上を図る

## 1. プロジェクト構成

```
lennard_jones_mc_rs/
├── Cargo.toml
├── src/
│   ├── lib.rs        # ライブラリエントリ
│   ├── main.rs       # 実行バイナリ
│   ├── lj_core.rs    # LJ コア（Python lj_core.py の移植）
│   ├── mc_3d.rs      # 3D 単箱 MC（Python lennard_jones_mc_3d.py の移植）
│   └── gemc_3d.rs    # 3D GEMC（Python lennard_jones_gemc_3d.py の移植）
└── WORK_LOG_RUST_MIGRATION_2026-03-07.md
```

## 2. 移植内容

### 2.1 lj_core.rs

Python `lj_core.py` の機能を移植:

| 機能 | 説明 |
|------|------|
| `minimum_image` | Minimum Image Convention |
| `wrap_positions` | 周期境界での座標折り返し |
| `lj_pair_energy` | Lennard-Jones 12-6 ペアエネルギー |
| `calc_energy` | 粒子 i の相互作用エネルギー |
| `total_energy` | 全系エネルギー |
| `insertion_energy` | 挿入エネルギー（GEMC 粒子交換用） |
| `init_positions` | ランダム初期配置 |
| `build_neighbor_state` | cutoff / cell list 構築 |
| `update_neighbor_state_after_move` | 変位後の cell list 差分更新 |
| `rebuild_neighbor_state` | 粒子追加・削除後の再構築 |

データ構造:

- `Vec3 = [f64; 3]` で 3 次元ベクトルを表現
- `NeighborState` で cutoff / cell list を管理
- `HashMap<(i32,i32,i32), Vec<usize>>` でセル→粒子インデックスを保持

### 2.2 mc_3d.rs

3D 単箱 NVT Monte Carlo:

- `McParams` でパラメータを保持
- `run_mc` でシミュレーション実行
- 1 ステップ = 1 粒子のランダム変位 + Metropolis 判定
- 計算時間を `Instant::elapsed()` で計測

### 2.3 gemc_3d.rs

3D Gibbs Ensemble Monte Carlo:

- `BoxState` で各箱の状態を管理
- 1 cycle の流れ:
  1. 粒子変位 move（各箱で複数回）
  2. 体積交換 move
  3. 粒子交換 move（双方向で複数回）
- `GemcResult` で密度・粒子数履歴を返却

## 3. 依存関係

- `rand = "0.8"`: 乱数生成（`StdRng`, `SeedableRng`, `Rng`）

## 4. 実行例

```bash
cd exercise/lennard_jones_mc_rs
cargo run --release
```

出力例（T=1.2, N=64, 10000 steps）:

```
単箱 MC: T=1.2, N=64, steps=10000
  最終エネルギー: -69.8708
  受理率: 76.88% (7688/10000)
  計算時間: 0.012 秒

GEMC: T=1.15, N_total=64, cycles=2000
  最終状態:
    Box 1: N=6, V=72.362, rho=0.0829, E=-1.5525
    Box 2: N=58, V=140.972, rho=0.4114, E=-147.2187
  ...
  計算時間: 0.129 秒
```

## 5. 今後の拡張候補

- [ ] cutoff + cell list の CLI オプション対応
- [ ] CSV 出力（密度履歴など）
- [ ] 可視化用データのエクスポート
- [ ] `rayon` による並列化
- [ ] アルゴン蒸気圧曲線用の温度掃引スクリプト

## 6. 不具合修正（2026-03-07）

### cell list の重複カウント

**現象**: GEMC の Volume 受理率が 1〜2% と極端に低い（Python 版は約 45%）。

**原因**: `n_cells=1` のとき、`neighbor_cells` が同じセル `(0,0,0)` を 27 回返し、候補粒子インデックスが重複。エネルギーが約 27 倍に計算され、体積交換がほぼ拒否されていた。

**修正**: `candidate_indices_for_particle` と `candidate_indices_for_point` で、候補インデックスを `HashSet` で重複排除。

**結果**: Volume 受理率が約 55% に改善。

## 7. 文献条件への準拠（2026-03-07）

Chialvo & Horita (2003) に合わせて `argon.rs` の計算条件を更新:

| 項目 | 旧（軽量設定） | 新（文献条件） |
|------|----------------|----------------|
| N_total | 100 | 500 |
| n_cycles | 20,000 | 30,000 |
| cutoff_radius | 1.5 | 3.0 (r_c ≈ 3.0 σ) |
| cell_size | 1.5 | 3.0 |
| displacement_tries_per_cycle | 100 | 500 |
| transfer_tries_per_cycle | 30 | 150 |

- epsilon/k = 114.5 K, sigma = 3.374 Å（無次元化で ε=1, σ=1）
- T* = 100/114.5 ≈ 0.87336
- cutoff_radius = 3.0 のため box_size > 6 が必要（total_density=0.30, N=500 で各箱 ≈ 9.4）

`plot_argon_density.py` のファイル名も N500_C30000 に更新済み。

## 8. Python 版との対応

| Python | Rust |
|--------|------|
| `lj_core.py` | `lj_core.rs` |
| `lennard_jones_mc_3d.py` | `mc_3d.rs` |
| `lennard_jones_gemc_3d.py` | `gemc_3d.rs` |
| NumPy `ndarray` | `Vec<Vec3>` |
| `np.random.Generator` | `rand::StdRng` |
