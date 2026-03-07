# 2D Lennard-Jones MC シミュレーション 変更ログ

このドキュメントは、`lennard_jones_mc.py` の初回実装から現在までに行った変更を時系列で記録したものです。数式は Notion 用に **$...$**（インライン）および **$$...$$**（ブロック）の LaTeX 形式で書いてあります。

---

## 1. 初回実装

### 概要
- `exercise/lennard_jones_mc/` ディレクトリを新規作成し、2次元 Lennard-Jones ポテンシャルを用いたメトロポリス・モンテカルロ法シミュレーションを1ファイルで実装した。

### 実装内容
- **物理モデル**
  - Lennard-Jones 12-6 ポテンシャル:
    $$
    V(r) = 4\epsilon \left[ \left(\frac{\sigma}{r}\right)^{12} - \left(\frac{\sigma}{r}\right)^6 \right]
    $$
  - $\epsilon = 1.0$, $\sigma = 1.0$（無次元単位系）
  - 2次元周期境界条件（Minimum Image Convention）

- **初期配置**
  - 粒子数 $N = 64$、8×8 の格子状に配置
  - `box_size`（例: 10.0）を定義し、格子間隔で重ならないように配置

- **エネルギー計算** (`calc_energy`)
  - 指定した1粒子と他全粒子との LJ 相互作用の和
  - 距離計算で周期境界を考慮: `dx = dx - box_size * round(dx / box_size)`

- **MC ステップ** (`mc_step`)
  - ランダムに1粒子を選択し、`delta_max` 以内でランダム変位
  - メトロポリス判定: $\Delta E \le 0$ なら採用、$\Delta E > 0$ なら確率 $\exp(-\Delta E / T)$ で採用

- **メインループ・可視化**
  - 指定ステップ数（例: 10,000）のループ
  - matplotlib で粒子配置の散布図とエネルギー履歴を表示
  - 一定ステップごとに `pos_history` に保存し、アニメーションまたは最終状態を表示

- **パラメータ**
  - スクリプト冒頭で $T$, ステップ数, `delta_max` 等を変更可能にした。

### 出力
- `README.md` を追加（実行方法・パラメータ・物理モデルの説明）

---

## 2. 日本語表示対応（グラフタイトル等）

### 問題
- グラフタイトル・軸ラベル等の日本語が正しく表示されなかった。

### 対応
- **パッケージ**: `japanize-matplotlib` を venv にインストール（`uv pip install japanize-matplotlib`）。
- **コード**: `matplotlib.pyplot` の直後に `import japanize_matplotlib` を追加。
- **依存関係**: `requirements.txt` に `japanize-matplotlib>=1.1` を追加。

---

## 3. 初期配置・パラメータ検証・出力先の改善（一括修正）

### 3.1 初期配置を格子からランダム配置へ変更
- **問題**: $N$ を平方数と暗黙に仮定した格子配置のため、$N$ が非平方数だと一部粒子が未初期化になる可能性があった。
- **対応**:
  - 粒子を箱内にランダムに配置。
  - 粒子間の最小距離（例: $0.9\sigma$）未満にならないようにし、周期境界を考慮した距離判定で近接を避けた。

### 3.2 高密度時の再試行処理
- **問題**: ランダム配置で高密度だと置けなくなり、その時点で `ValueError` で終了していた。
- **対応**: 局所的に詰まった場合は初期配置全体を最初からやり直すループ（`for-else` と `while True`）を導入し、配置可能な条件では自動で再試行するようにした。

### 3.3 パラメータ検証の追加
- **追加**: `validate_parameters()` を追加し、実行前に以下をチェック。
  - $T \le 0$, $N \le 0$, `N_STEPS <= 0`, `DELTA_MAX < 0`, `BOX_SIZE <= 0`, `EPSILON < 0`, `SIGMA <= 0`, `VISUALIZE_INTERVAL <= 0`

### 3.4 温度 \(T \le 0\) の不具合防止
- **問題**: $T = 0$ で `exp(-dE / T)` がゼロ除算、$T < 0$ では物理的に不正なメトロポリス判定になる。
- **対応**: `validate_parameters()` で $T > 0$ を要求するようにした。

### 3.5 出力ファイルの保存先を固定
- **問題**: `lennard_jones_animation.gif` や `lennard_jones_final.png` が実行時カレントディレクトリに保存されていた。
- **対応**: `OUTPUT_DIR = Path(__file__).resolve().parent` を定義し、アニメーション・最終画像を常にスクリプトと同じディレクトリに保存するようにした。

### 3.6 不要コードの整理
- 可視化まわりで未使用だった `viz_steps` を削除した。

---

## 4. 追加の不具合修正・仕様改善

### 4.1 最終状態の保存漏れ
- **問題**: `N_STEPS` が `VISUALIZE_INTERVAL` の倍数でない場合、ループ終了後の最終配置が `pos_history` に含まれず、最終配置画像が「最後の可視化間隔の状態」になっていた。
- **対応**: ループ終了後に `if N_STEPS % VISUALIZE_INTERVAL != 0:` のときだけ `pos_history.append(pos.copy())` で最終状態を追加した。

### 4.2 初期配置の無限ループ対策
- **問題**: 密度が高すぎる場合、`init_positions` の `while True` が終わらずプログラムがハングする可能性があった。
- **対応**:
  - `init_positions` に `max_global_retries`（デフォルト 1000）を導入し、`while True` を `for _ in range(max_global_retries)` に変更。
  - 上限超過時に「配置失敗」旨の `ValueError` を送出するようにした。

### 4.3 密度の妥当性チェック
- **問題**: 配置が物理的に不可能な高密度でも検証されず、初期化でハングまたは長時間ループする可能性があった。
- **対応**: `validate_parameters()` 内で、ランダム配置の目安として $N \cdot \pi (d/2)^2 > 0.8 \cdot \text{BOX\_SIZE}^2$（$d$ は最小初期距離）のとき `ValueError` を出すようにした。

### 4.4 DELTA_MAX = 0 の扱い
- **問題**: `DELTA_MAX = 0` だと粒子が動かず、意味のあるサンプリングにならない。
- **対応**: `validate_parameters()` で `DELTA_MAX > 0` を要求するように変更（従来の「非負」から「正」に変更）。

### 4.5 コメントの修正
- **問題**: 初期配置をランダムに変更した後も、$N$ のコメントが「8x8格子」のままだった。
- **対応**: `# 粒子数（8x8格子）` を `# 粒子数` に修正した。

### 4.6 mc_step の docstring 修正
- **問題**: 返り値の説明が「採用時は正、不採用時は0」となっていたが、$\Delta E \le 0$ で採用する場合は負やゼロも返る。
- **対応**: 「採用時はエネルギー差 ΔE、不採用時は 0」に修正した。

---

## 5. 受理率（Acceptance Ratio）の表示

### 概要
- メトロポリス法の受理率を記録し、シミュレーション終了後に表示する機能を追加した。

### 実装内容
- **`mc_step`**: 返り値を `(dE, accepted: bool)` のタプルに変更。
- **`run_simulation`**: 受理した回数 `n_accepted` をカウントし、返り値に `n_accepted` を追加。
- **`main`**: 実行後に「受理率 (Acceptance Ratio): XX.XX% (受理数/総ステップ数)」をプリントするようにした。

---

## 6. 3次元対応と 3D GEMC の追加

### 6.1 共通ロジックの切り出し
- **追加ファイル**: `lj_core.py`
- **内容**:
  - Minimum Image Convention
  - 周期境界での座標折り返し
  - ランダム初期配置
  - 1 粒子エネルギーと全エネルギー
  - 挿入エネルギー
  - 単箱 MC / GEMC 共通のパラメータ検証
- **目的**: 既存 2D 実装を残したまま、3D 単箱 MC と 3D GEMC で再利用できるようにするため。

### 6.2 既存 2D 実装の維持
- **対象**: `lennard_jones_mc.py`
- **対応**:
  - 既存の 2D 挙動は維持
  - 初期配置・エネルギー計算・基本検証だけを `lj_core.py` に委譲
- **目的**: 2D の参照実装を壊さず、共通部だけを整理するため。

### 6.3 3D 単箱 MC の追加
- **追加ファイル**: `lennard_jones_mc_3d.py`
- **内容**:
  - 3 次元座標 `shape = (N, 3)` を使った Metropolis MC
  - 1 粒子変位 move
  - 3D 最終配置とエネルギー履歴の可視化
- **出力**:
  - `lennard_jones_3d_final.png`

### 6.4 3D GEMC の追加
- **追加ファイル**: `lennard_jones_gemc_3d.py`
- **内容**:
  - 2 箱の状態を `BoxState` で管理
  - 粒子変位 move
  - 体積交換 move
  - 粒子交換 move
  - 各箱の粒子数・密度・体積・エネルギー履歴を記録
- **出力**:
  - `lennard_jones_gemc_3d_final.png`

### 6.5 ドキュメントと作業ログ
- **README**:
  - 2D / 3D / GEMC の 3 本立てに再構成
  - 実行コマンドを絶対パスで明記
- **作業ログ**:
  - `WORK_LOG_3D_MC_2026-03-07.md`
  - `WORK_LOG_GEMC_3D_2026-03-07.md`

### 6.6 cutoff / cell list の追加
- **対象**:
  - `lj_core.py`
  - `lennard_jones_mc.py`
  - `lennard_jones_mc_3d.py`
  - `lennard_jones_gemc_3d.py`
- **追加した切替パラメータ**:
  - `USE_CUTOFF`
  - `CUTOFF_RADIUS`
  - `USE_CELL_LIST`
  - `CELL_SIZE`
- **実装内容**:
  - cutoff なし総当たり
  - cutoff あり総当たり
  - cutoff + cell list
  の 3 モードを共通部で切替可能にした。
- **補足**:
  - `cell list` は cutoff を前提にするため、`USE_CELL_LIST=True` でも `USE_CUTOFF=False` の場合は有効化されない。
- **ログ追加**:
  - `WORK_LOG_ARGON_VLE_CHECK_2026-03-07.md`
  - `WORK_LOG_CUTOFF_CELLLIST_2026-03-07.md`

---

## 現在の主な仕様まとめ

| 項目 | 内容 |
|------|------|
| 初期配置 | ランダム配置（最小距離・周期境界を考慮）、失敗時は全体を再試行（回数上限あり） |
| パラメータ検証 | $T>0$, $N>0$, `N_STEPS>0`, `DELTA_MAX>0`, `BOX_SIZE>0`, `EPSILON≥0`, `SIGMA>0`, `VISUALIZE_INTERVAL>0`、および高密度チェック |
| 出力先 | スクリプトと同じディレクトリ（`Path(__file__).resolve().parent`） |
| 最終状態 | `N_STEPS` が `VISUALIZE_INTERVAL` の倍数でなくても、最終配置を `pos_history` に含めて可視化・保存 |
| 表示 | 日本語フォント（japanize-matplotlib）、受理率の表示 |
| 3D 単箱 MC | `lennard_jones_mc_3d.py` として追加 |
| 3D GEMC | `lennard_jones_gemc_3d.py` として追加 |

---

*最終更新: 変更ログ作成時点の `lennard_jones_mc.py` の状態に基づく。*
