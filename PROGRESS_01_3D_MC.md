# 進捗ログ 01: 3D Lennard-Jones MC 追加

- 日付: 2026-03-07
- 参照: `lennard_jones_mc/WORK_LOG_3D_MC_2026-03-07.md`

## 概要

既存の 2D 実装は残したまま、3 次元の単箱 Lennard-Jones MC を追加した。

## 実装方針

- 既存の `lennard_jones_mc.py` は 2D の参照実装として維持
- 2D と 3D で共通化できる最小限の処理だけを `lj_core.py` に切り出す
- 3D 単箱 MC は新規ファイル `lennard_jones_mc_3d.py` として追加

## 追加・変更したファイル

- `lj_core.py`（共通部）
- `lennard_jones_mc.py`（lj_core 呼び出しへ一部置換）
- `lennard_jones_mc_3d.py`（新規）

## 実装内容

### 共通部（lj_core.py）

- パラメータ検証
- 初期密度チェック
- Minimum Image Convention
- 周期境界での座標折り返し
- ランダム初期配置
- 1 粒子エネルギー
- 全エネルギー

### 3D 単箱 MC（lennard_jones_mc_3d.py）

- 3 次元ランダム初期配置
- 3 成分のランダム変位
- Metropolis 判定
- 3D 最終配置 + エネルギー履歴の可視化
- PNG 出力

## 主な判断

- 既存 2D 実装を大きく一般化すると差分が大きくなりやすいため、3D は別入口にした
- 計算量はまず O(N²) のままとし、教育用として読みやすい実装を優先
