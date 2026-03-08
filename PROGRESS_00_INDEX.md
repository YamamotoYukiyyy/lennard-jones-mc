# 進捗ログ インデックス

- 日付: 2026-03-07
- 対象: CompPhysHack exercise（Lennard-Jones MC / GEMC）

## 項目一覧

| No. | ファイル | 内容 |
|-----|----------|------|
| 01 | [PROGRESS_01_3D_MC.md](PROGRESS_01_3D_MC.md) | 3D Lennard-Jones MC 追加 |
| 02 | [PROGRESS_02_GEMC.md](PROGRESS_02_GEMC.md) | 3D GEMC 追加 |
| 03 | [PROGRESS_03_CUTOFF_CELLLIST.md](PROGRESS_03_CUTOFF_CELLLIST.md) | Cutoff + Cell List 導入 |
| 04 | [PROGRESS_04_ARGON_VLE.md](PROGRESS_04_ARGON_VLE.md) | アルゴン VLE 1 点試算 |
| 05 | [PROGRESS_05_N100_C5000.md](PROGRESS_05_N100_C5000.md) | N=100, cycles=5000 の実行 |
| 06 | [PROGRESS_06_RUST_MIGRATION.md](PROGRESS_06_RUST_MIGRATION.md) | Rust 移行 |
| 07 | [PROGRESS_07_ADDITIONAL_FEATURES.md](PROGRESS_07_ADDITIONAL_FEATURES.md) | 追加機能（進捗表示・単位変換・複数温度VLE） |

## 関連ディレクトリ

- `lennard_jones_mc/` — Python 版（2D MC, 3D MC, 3D GEMC）
- `lennard_jones_mc_rs/` — Rust 版（移植 + argon 専用バイナリ）
