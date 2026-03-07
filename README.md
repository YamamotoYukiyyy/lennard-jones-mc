# Lennard-Jones Monte Carlo Examples

このディレクトリには、Lennard-Jones 流体に対する 3 種類の教育用サンプル実装が入っています。

- `lennard_jones_mc.py`: 既存の 2 次元・単箱 Metropolis MC
- `lennard_jones_mc_3d.py`: 新規追加した 3 次元・単箱 Metropolis MC
- `lennard_jones_gemc_3d.py`: 新規追加した 3 次元 Gibbs Ensemble Monte Carlo

共通処理は `lj_core.py` にまとめてあります。

## 実行方法

### 2D 単箱 MC

```bash
/Users/yamamoto/Desktop/CompPhysHack/.venv-base/bin/python /Users/yamamoto/Desktop/CompPhysHack/exercise/lennard_jones_mc/lennard_jones_mc.py
```

### 3D 単箱 MC

```bash
/Users/yamamoto/Desktop/CompPhysHack/.venv-base/bin/python /Users/yamamoto/Desktop/CompPhysHack/exercise/lennard_jones_mc/lennard_jones_mc_3d.py
```

### 3D GEMC

```bash
/Users/yamamoto/Desktop/CompPhysHack/.venv-base/bin/python /Users/yamamoto/Desktop/CompPhysHack/exercise/lennard_jones_mc/lennard_jones_gemc_3d.py
```

## ファイル構成

| ファイル | 内容 |
|---|---|
| `lennard_jones_mc.py` | 2D の既存単箱 MC |
| `lennard_jones_mc_3d.py` | 3D の単箱 MC |
| `lennard_jones_gemc_3d.py` | 3D の GEMC |
| `lj_core.py` | 最小鏡像、初期配置、エネルギー計算などの共通部 |
| `CHANGELOG.md` | 実装変更履歴 |
| `WORK_LOG_3D_MC_2026-03-07.md` | 3D 単箱 MC 追加の作業ログ |
| `WORK_LOG_GEMC_3D_2026-03-07.md` | 3D GEMC 追加の作業ログ |
| `WORK_LOG_ARGON_VLE_CHECK_2026-03-07.md` | アルゴン代表点の 1 点試算ログ |
| `WORK_LOG_CUTOFF_CELLLIST_2026-03-07.md` | cutoff / cell list 導入ログ |

## 物理モデル

- ポテンシャル: Lennard-Jones 12-6
  $$
  V(r) = 4\epsilon \left[ \left(\frac{\sigma}{r}\right)^{12} - \left(\frac{\sigma}{r}\right)^6 \right]
  $$
- 無次元単位系を使用し、既定値は `epsilon = 1.0`, `sigma = 1.0`
- 境界条件は周期境界条件で、距離計算には Minimum Image Convention を使います

## 2D 単箱 MC の概要

既存の `lennard_jones_mc.py` はそのまま残してあります。粒子を 1 つずつランダム変位し、Metropolis 判定で受理・棄却します。

主なパラメータ:

| パラメータ | 説明 |
|---|---|
| `T` | 温度 |
| `N_STEPS` | モンテカルロステップ数 |
| `DELTA_MAX` | 粒子の最大移動距離 |
| `BOX_SIZE` | 2D ボックスの一辺 |
| `N` | 粒子数 |
| `USE_CUTOFF` | cutoff を使うか |
| `CUTOFF_RADIUS` | cutoff 半径 |
| `USE_CELL_LIST` | cell list を使うか |
| `CELL_SIZE` | セルサイズ |

主な出力:

- `lennard_jones_animation.gif`
- `lennard_jones_final.png`

## 3D 単箱 MC の概要

`lennard_jones_mc_3d.py` は、既存 2D 実装の流れを保ったまま 3 次元に拡張した版です。

特徴:

- 座標は `shape = (N, 3)`
- 1 粒子変位の Metropolis MC
- 初期配置・エネルギー計算は `lj_core.py` を利用
- `cutoff` と `cell list` をフラグで切替可能
- 最終 3D 配置とエネルギー履歴を `lennard_jones_3d_final.png` に保存可能

## 3D GEMC の概要

`lennard_jones_gemc_3d.py` は 2 箱を用いた Gibbs Ensemble Monte Carlo の実装です。

1 サイクルで次の move を行います。

1. 粒子変位 move を複数回
2. 体積交換 move を 1 回
3. 粒子交換 move を複数回

記録する量:

- 各箱の粒子数 `N1`, `N2`
- 各箱の密度 `rho1`, `rho2`
- 各箱の体積 `V1`, `V2`
- 各箱のエネルギー `E1`, `E2`
- `cutoff` と `cell list` をフラグで切替可能

主な出力:

- `lennard_jones_gemc_3d_final.png`

## 高速化オプション

各スクリプトには、少なくとも次の高速化パラメータがあります。

| パラメータ | 説明 |
|---|---|
| `USE_CUTOFF` | `True` で cutoff を有効化 |
| `CUTOFF_RADIUS` | cutoff 半径 |
| `USE_CELL_LIST` | `True` で cell list を有効化 |
| `CELL_SIZE` | cell list のセルサイズ |

挙動:

- `USE_CUTOFF=False, USE_CELL_LIST=False`
  - 全粒子総当たり
- `USE_CUTOFF=True, USE_CELL_LIST=False`
  - cutoff 付き総当たり
- `USE_CUTOFF=True, USE_CELL_LIST=True`
  - cutoff + cell list

注意:

- `cell list` は実質的に cutoff 半径を前提にするため、`USE_CELL_LIST=True` でも `USE_CUTOFF=False` の場合は cell list は有効に使われません。
- `USE_CUTOFF=True` の場合、`CUTOFF_RADIUS < BOX_SIZE / 2` が必要です。GEMC では体積交換で箱が縮むため、設定によっては一部の体積交換 move が自動で棄却されます。

## 注意

- 実装は教育用・可読性重視のため、計算量は基本的に `O(N^2)` です
- GEMC は小規模系では有限サイズ効果が大きく、短い実行では平衡点がまだ十分安定しないことがあります
- 既定パラメータは「まず動くこと」を優先した値なので、蒸気圧曲線の本格計算には追加の平衡化・平均化が必要です
