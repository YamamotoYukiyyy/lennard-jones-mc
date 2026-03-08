# 進捗ログ 03: Cutoff + Cell List 導入

- 日付: 2026-03-07
- 参照: `lennard_jones_mc/WORK_LOG_CUTOFF_CELLLIST_2026-03-07.md`

## 概要

2D/3D 単箱 MC および 3D GEMC に対して、cutoff と cell list を切り替え可能な形で導入した。

## 実装方針

- 全バージョンにパラメータ追加: `USE_CUTOFF`, `CUTOFF_RADIUS`, `USE_CELL_LIST`, `CELL_SIZE`
- モード: 総当たり / cutoff 付き総当たり / cutoff + cell list
- cell list は cutoff を前提とする

## 変更対象

- `lj_core.py`
- `lennard_jones_mc.py`
- `lennard_jones_mc_3d.py`
- `lennard_jones_gemc_3d.py`

## lj_core.py の追加内容

- `NeighborState`: cutoff / cell list 設定、セル情報
- `normalize_neighbor_options`, `build_neighbor_state`, `rebuild_neighbor_state`, `update_neighbor_state_after_move`
- `calc_energy`, `total_energy`, `insertion_energy` の拡張

## GEMC 側の変更

- 各箱に `neighbor_state` を保持
- 粒子変位: 差分更新
- 体積交換・粒子交換: 受理時に両箱の近傍状態を再構築
- `CUTOFF_RADIUS < BOX_SIZE / 2` を満たさない提案は棄却

## ベンチマーク結果（小規模）

| モード | 時間 |
|--------|------|
| plain | 1.769 s |
| cutoff | 1.370 s |
| cutoff_cell | 1.785 s |

- 小さい系では cutoff 単独が最も速い
- cutoff あり総当たりと cutoff + cell list で同じ結果（整合性確認済み）
