# 2D Lennard-Jones Molecular Monte Carlo Simulation

2次元空間におけるレナード・ジョーンズ（LJ）ポテンシャルを用いたメトロポリス・モンテカルロ法シミュレーション。

## 実行方法

```bash
/Users/yamamoto/Desktop/CompPhysHack/.venv-base/bin/python lennard_jones_mc.py
```

## パラメータ（スクリプト冒頭で変更可能）

| パラメータ | デフォルト | 説明 |
|-----------|------------|------|
| `T` | 0.5 | 温度（無次元） |
| `N_STEPS` | 10,000 | モンテカルロステップ数 |
| `DELTA_MAX` | 0.1 | 粒子の最大移動距離 |
| `BOX_SIZE` | 10.0 | シミュレーション箱のサイズ |
| `N` | 64 | 粒子数（8×8格子） |
| `SAVE_ANIMATION` | False | TrueでGIFアニメーションを保存 |
| `SAVE_FINAL_IMAGE` | True | 最終配置をPNGに保存 |
| `INTERACTIVE` | True | FalseでGUI表示をスキップ |

## 物理モデル

- **ポテンシャル**: Lennard-Jones 12-6
  $$V(r) = 4\epsilon \left[ \left(\frac{\sigma}{r}\right)^{12} - \left(\frac{\sigma}{r}\right)^6 \right]$$
  $\epsilon = 1.0$, $\sigma = 1.0$（無次元化単位系）

- **境界条件**: 2次元周期境界条件（Minimum Image Convention）

- **初期配置**: 8×8の格子状（重ならない配置）
