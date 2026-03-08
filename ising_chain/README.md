# 一次元イジング鎖 DMRG

ITensor を用いて一次元イジング鎖の基底状態エネルギーと波動関数を DMRG で計算するプログラムです。

## ハミルトニアン

$$
\mathcal{H} = -J \sum_{i=1}^{N-1} S^z_i S^z_{i+1}
$$

- **J > 0 (強磁性)**: 基底状態は全スピン同方向（|↑↑↑...⟩ または |↓↓↓...⟩）
- **J < 0 (反強磁性)**: 基底状態は Néel 状態（|↑↓↑↓...⟩）

## ビルド方法

1. ITensor をビルド（初回のみ）:
   ```bash
   cd ../ITensor
   cp options.mk.sample options.mk   # 未作成の場合
   make
   ```

2. イジング鎖プログラムをビルド:
   ```bash
   cd ../ising_chain
   make
   ```

## 実行

```bash
./ising_dmrg
```

## 出力

- 基底状態エネルギー
- 各サイトの ⟨S^z⟩（磁化プロファイル）
- 理論値との比較（強磁性の場合）
- `ising_data.csv`（可視化用データ）

## 厳密対角化（Exact Diagonalization）

```bash
python exact_diagonalization.py [N]
```

例: `python exact_diagonalization.py 12` で N=12 の基底状態を計算

## ベンチマーク（ED vs DMRG）

```bash
python benchmark.py [--max-n 20] [--python python]
```

実行時間の比較プロットを `benchmark_comparison.png` に保存します。

## 可視化

```bash
python visualize.py
```

`ising_visualization.png` に以下が保存されます：

1. **磁化プロファイル** - 各サイトの ⟨S^z⟩（棒グラフ）
2. **中心サイトとの相関** - ⟨S^z_center S^z_j⟩
3. **相関行列** - ⟨S^z_i S^z_j⟩ のヒートマップ

## パラメータの変更

コマンドライン引数で指定：`./ising_dmrg [N] [J]`

- `N`: サイト数（デフォルト: 20）
- `J`: 結合定数（デフォルト: 1.0、負の値で反強磁性）

## 詳細なサマリー

実装内容と結果の詳細は `SUMMARY.md` を参照してください。
