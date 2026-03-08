# 一次元イジング鎖 実装サマリー

> **Notion での数式**：ブロック数式は `$$...$$`、インラインは `$...$`。Notion の /math ブロックには LaTeX 部分のみ貼り付けてください。

## 1. 概要

一次元イジング鎖の基底状態エネルギーと波動関数を、**DMRG（密度行列繰り込み群）**と**厳密対角化（Exact Diagonalization）**の2つの手法で計算するプログラムを実装した。

---

## 2. モデル

### 2.1 ハミルトニアン

$$
\mathcal{H} = -J \sum_{i=1}^{N-1} S_i^z S_{i+1}^z
$$

- $N$：サイト数
- $J$：結合定数
- $S_i^z$：サイト $i$ のスピン z 成分（スピン1/2：$\pm 1/2$）

### 2.2 基底状態の性質

| $J$ | 基底状態 |
|---------|----------|
| $J > 0$（強磁性） | 全スピン同方向（$\lvert \uparrow \uparrow \cdots \rangle$ または $\lvert \downarrow \downarrow \cdots \rangle$） |
| $J < 0$（反強磁性） | Néel 状態（$\lvert \uparrow \downarrow \uparrow \downarrow \cdots \rangle$） |

### 2.3 理論値（強磁性、開端）

基底状態エネルギー：
$$
E_{\text{exact}} = -\frac{J(N-1)}{4}
$$

---

## 3. 実装内容

### 3.1 ファイル構成

| ファイル | 言語 | 説明 |
|----------|------|------|
| `ising_dmrg.cc` | C++ | DMRG による基底状態計算（ITensor 使用） |
| `exact_diagonalization.py` | Python | 厳密対角化による基底状態計算 |
| `visualize.py` | Python | 磁化プロファイル・相関関数の可視化 |
| `benchmark.py` | Python | DMRG と ED の実行時間比較 |
| `Makefile` | Make | DMRG のビルド |

### 3.2 DMRG 実装（ising_dmrg.cc）

1. **SiteSet**：スピン1/2鎖（`SpinHalf`）
2. **MPO 構築**：`AutoMPO` で $\mathcal{H} = -J \sum S_i^z S_{i+1}^z$ を MPO に変換
3. **初期状態**：ランダム MPS（`randomMPS`）
4. **DMRG パラメータ**：10 スイープ、maxdim = 10〜200、cutoff = $10^{-12}$
5. **出力**：基底状態エネルギー、各サイトの $\langle S^z \rangle$、相関行列、CSV データ

**コマンドライン引数**：`./ising_dmrg [N] [J]`（デフォルト：N=20, J=1.0）

### 3.3 厳密対角化実装（exact_diagonalization.py）

イジング模型は $S^z$ 基底で対角なため、全 $2^N$ 状態のエネルギーを計算し最小値を基底状態エネルギーとする。

- **計算量**：$O(2^N)$（状態の列挙）
- **メモリ**：$O(2^N)$（エネルギー配列）

### 3.4 可視化（visualize.py）

`ising_data.csv` を読み込み、以下をプロット：

1. **磁化プロファイル**：各サイトの $\langle S_i^z \rangle$
2. **中心サイトとの相関**：$\langle S_{\text{center}}^z S_j^z \rangle$
3. **相関行列**：$\langle S_i^z S_j^z \rangle$ のヒートマップ

---

## 4. 計算結果

### 4.1 基底状態エネルギー（N=20, J=1.0）

| 手法 | エネルギー | 理論値との誤差 |
|------|------------|----------------|
| DMRG | $-4.750000000000$ | $0$ |
| 厳密対角化 | $-4.750000000000$ | $0$ |
| 理論値 | $-J(N-1)/4 = -4.75$ | — |

両手法とも理論値と一致。

### 4.2 磁化プロファイル（強磁性、N=20）

全サイトで $\langle S_i^z \rangle = \pm 0.5$（全スピン同方向）を確認。強磁性基底状態と一致。

### 4.3 相関関数（強磁性）

全スピン同方向の基底状態では：
$$
\langle S_i^z S_j^z \rangle = \frac{1}{4} \quad (\forall i, j)
$$

計算結果も $0.25$ で一致。

---

## 5. ベンチマーク結果（ED vs DMRG）

### 5.1 実行時間比較（N=4〜20）

| N | ED (秒) | DMRG (秒) | 倍率（DMRG が速い） |
|---|---------|-----------|----------------------|
| 4 | 0.20 | 0.004 | 約 50 倍 |
| 8 | 0.15 | 0.010 | 約 15 倍 |
| 12 | 0.19 | 0.016 | 約 12 倍 |
| 16 | 0.45 | 0.022 | 約 20 倍 |
| 18 | 1.48 | 0.032 | 約 46 倍 |
| 20 | **5.90** | **0.027** | **約 220 倍** |

### 5.2 スケーリング

- **厳密対角化**：計算量 $O(2^N)$ のため、N の増加とともに指数関数的に遅くなる
- **DMRG**：計算量はほぼ多項式的で、N が増えても実行時間は緩やかに増加

N=20 では DMRG が ED より約 220 倍高速。

---

## 6. 使い方

```bash
# DMRG のビルド・実行
cd exercise/ising_chain
make
./ising_dmrg [N] [J]

# 厳密対角化
python exact_diagonalization.py [N]

# 可視化
python visualize.py

# ベンチマーク
python benchmark.py --max-n 20
```

---

## 7. 出力ファイル

| ファイル | 説明 |
|----------|------|
| `ising_data.csv` | 磁化・相関行列の数値データ |
| `ising_visualization.png` | 可視化図（3 パネル） |
| `benchmark_comparison.png` | ED と DMRG の実行時間比較プロット |

---

## 8. まとめ

- 一次元イジング鎖の基底状態を DMRG と厳密対角化の両方で計算
- 両手法とも理論値と一致する結果を得た
- DMRG は N が大きい系で圧倒的に高速（N=20 で約 220 倍）
- 磁化プロファイル・相関関数の可視化と、実行時間のベンチマークを実装
