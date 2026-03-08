# 開発プロンプトのまとめ

今回の Lennard-Jones モンテカルロシミュレーション開発において、実装の段階ごとに想定されるプロンプトの例をまとめました。  
（WORK_LOG、PROGRESS シリーズ、および本セッションのやり取りから再構成）

---

## 1. 2D → 3D MC の拡張

**段階**: 既存の 2D 実装を 3 次元に拡張

**想定プロンプト例**:
- 「既存の 2D 実装は残したまま、3 次元の単箱 Lennard-Jones MC を追加してほしい」
- 「2D と 3D で共通化できる部分は `lj_core.py` に切り出し、3D は `lennard_jones_mc_3d.py` として新規追加して」
- 「3 次元ランダム初期配置、3 成分のランダム変位、Metropolis 判定、最終配置とエネルギー履歴の可視化を実装して」

**参照**: `PROGRESS_01_3D_MC.md`, `WORK_LOG_3D_MC_2026-03-07.md`

---

## 2. 3D GEMC の追加

**段階**: Gibbs Ensemble MC（気液共存）の実装

**想定プロンプト例**:
- 「3 次元 Lennard-Jones 流体に対する Gibbs Ensemble Monte Carlo を追加してほしい」
- 「2 箱を独立した BoxState として管理し、1 サイクルは 粒子変位 → 体積交換 → 粒子交換 の順で実装して」
- 「粒子変位、体積交換、粒子交換の各 move を実装し、N1, N2, rho1, rho2, V1, V2, E1, E2 の履歴を記録して」
- 「まずは可読性重視で O(N²) 実装で。近接リストやカットオフは今回は入れないで」

**参照**: `PROGRESS_02_GEMC.md`, `WORK_LOG_GEMC_3D_2026-03-07.md`

---

## 3. Cutoff + Cell List の導入

**段階**: 計算の高速化のための cutoff と cell list

**想定プロンプト例**:
- 「2D/3D 単箱 MC と 3D GEMC に、cutoff と cell list を切り替え可能な形で導入してほしい」
- 「USE_CUTOFF, CUTOFF_RADIUS, USE_CELL_LIST, CELL_SIZE をパラメータとして追加して」
- 「総当たり / cutoff 付き総当たり / cutoff + cell list の 3 モードをサポートして」
- 「cell list は cutoff を前提にする。GEMC では体積交換で箱が縮むので、CUTOFF_RADIUS < BOX_SIZE/2 を満たさない提案は棄却して」

**参照**: `PROGRESS_03_CUTOFF_CELLLIST.md`, `WORK_LOG_CUTOFF_CELLLIST_2026-03-07.md`

---

## 4. アルゴン VLE 1 点試算

**段階**: 文献条件に合わせた検証

**想定プロンプト例**:
- 「文献 Chialvo & Horita (2003) を意識して、アルゴンの気液共存域に相当する 1 点を試算してほしい」
- 「epsilon/k = 114.5 K, sigma = 3.374 Å, T = 100 K で、N_total = 64, N_cycles = 2000, cutoff なしで実行して」
- 「計算時間と収束の度合いを確認したい」

**参照**: `PROGRESS_04_ARGON_VLE.md`, `WORK_LOG_ARGON_VLE_CHECK_2026-03-07.md`

---

## 5. Rust への移植

**段階**: Python 版の Rust 移植による高速化

**想定プロンプト例**:
- 「Python 版 lennard_jones_mc を Rust に移植して、計算速度を上げてほしい」
- 「lj_core.py → lj_core.rs, lennard_jones_mc_3d.py → mc_3d.rs, lennard_jones_gemc_3d.py → gemc_3d.rs の対応で移植して」
- 「cutoff と cell list も移植して。計算時間は Instant::elapsed() で計測して」
- 「Volume 受理率が Python と比べて極端に低い。cell list の重複カウントを修正して」（バグ修正）

**参照**: `PROGRESS_06_RUST_MIGRATION.md`, `WORK_LOG_RUST_MIGRATION_2026-03-07.md`

---

## 6. 追加機能（進捗表示・単位変換・複数温度 VLE）

**段階**: 運用性と検証のための拡張

**想定プロンプト例**:
- 「1000 サイクルごとに進捗を表示してほしい」
- 「密度を rho* (LJ) と g/cm³ (SI) の両方で表示して。アルゴンの単位変換を入れて」
- 「複数温度で気液共存を計算するスクリプト（argon_vle）を作って。84 K〜148 K の温度点で」
- 「文献条件 N=500, cycles=10000, r_c=3σ で実行し、argon_vle_multitemp_rs.csv に出力して」

**参照**: `PROGRESS_07_ADDITIONAL_FEATURES.md`

---

## 7. スライド作成（本セッション）

**段階**: ハッカソンまとめスライドの作成

**実際のプロンプト例**:
- 「/slide 今回実装してもらった Lennard-Jones モンテカルロシミュレーションについて、live coding のハッカソンのまとめとしてスライド 2 枚程度でまとめてください。あとで蒸気圧曲線を貼り付けたいです。スライド構成を一緒に考えてください」
- 「モンテカルロシミュレーションを行った。まず、二次元でレナードジョーンズポテンシャルの下でシミュレーションを行った。分子の動きはそれらしいものだったが、実装の正しさを確認したかったのでアルゴンの蒸気圧曲線を計算することにした。まず python で 3 次元の GEMC を実装してもらったが、計算が遅かったので rust に移植した。その結果、計算が早くなった。その後、先行研究の計算条件と合わせて蒸気圧曲線を書いたところ、近い結果が得られた」
- 「表は N=20 のベンチマーク結果（Python 273.26 s, Rust 0.30 s）から作成してください」
- 「図はこちらを貼り付けてください」（蒸気圧曲線の画像を指定）
- 「英語版を作成してください」

**参照**: 本チャット履歴

---

## プロンプトの傾向

| 傾向 | 例 |
|------|-----|
| **目的を明確に** | 「〜を追加してほしい」「〜を移植して」 |
| **制約を明示** | 「既存 2D は残す」「まず O(N²) で」「cutoff なしで」 |
| **出力形式を指定** | 「CSV に出力して」「履歴を記録して」 |
| **文献・条件を参照** | 「Chialvo & Horita (2003) を意識して」「N=500, r_c=3σ」 |
| **段階的に依頼** | 3D MC → GEMC → cutoff → アルゴン → Rust の順 |
| **問題があれば修正依頼** | 「Volume 受理率が低い。cell list の重複を修正して」 |
