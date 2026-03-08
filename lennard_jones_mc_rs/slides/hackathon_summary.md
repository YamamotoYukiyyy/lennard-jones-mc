---
marp: true
theme: uncover
size: 16:9
paginate: true
header: 'モンテカルロシミュレーション Hackathon まとめ'
footer: 'CompPhysHack'
title: モンテカルロシミュレーション
style: |
  section { padding: 48px 64px; text-align: left; }
  h1 { font-size: 1.6em; margin-bottom: 0.3em; text-align: left; border-left: 6px solid #0066cc; padding-left: 16px; }
  h1 .sub { font-size: 0.6em; color: #666; font-weight: normal; margin-left: 0.5em; }
  h2 { font-size: 1.2em; color: #333; margin-bottom: 0.4em; text-align: left; }
  ul, table { text-align: left; }
  table { white-space: nowrap; }
  table td, table th { white-space: nowrap; }
  ul { line-height: 1.8; }
  strong { color: #0066cc; }
  .slide1 li:nth-child(3) { white-space: nowrap; }
---

<!-- _class: slide1 -->

# モンテカルロシミュレーション

- **モデル**: 2次元・レナードジョーンズポテンシャル
- **結果**: 分子の動きは妥当そう
- **次の目標**: 実装の正しさを検証<br> 　　　　→ アルゴン蒸気圧曲線を計算

---

# アルゴンの蒸気圧曲線の計算

- **GEMC** = Gibbs Ensemble MC（気液共存）
- Python で実装 → 計算が遅い → Rust に移植 → 高速化

**計算時間の比較（cutoff・cell list なし）**

| 条件 | Python (秒) | Rust (秒) | 速度比 |
|:-----|------------:|----------:|-------:|
| N=20,  T=114K <br> 40000 steps | 273.3 | 0.30 | 約 910× |

---

# アルゴンの蒸気圧曲線の計算

- 先行研究と近い値が得られた

![vapor_pressure_curve.png](vapor_pressure_curve.png)

---

# アルゴンの蒸気圧曲線の計算

![vapor_pressure_comparison.png](vapor_pressure_comparison.png)
