# Lennard-Jones 流体のMonte Carloシミュレーション

Lennard-Jones系のMonte Carloシミュレーションの包括的なスイート。PythonとRustの両方の実装とベンチマーク機能を含んでいます。

## 概要

このリポジトリには、Lennard-Jones Monte Carloシミュレーションの3つの主要な実装が含まれています：

### 1. **lennard_jones_mc** - Python実装
純粋なPython実装で、以下の機能をサポート：
- 標準的なMCシミュレーション
- 3次元シミュレーション
- Grand Canonical Ensemble (GEMC)
- 柔軟なカットオフとセルリストの実装
- 相図とVLE計算の解析ツール

### 2. **lennard_jones_mc_rs** - Rust実装
高性能なRust実装で以下を提供：
- 高速で効率的なシミュレーション
- Python版と同じアルゴリズム
- Python版との比較ベンチマーク
- ネイティブなパフォーマンス最適化

### 3. **lennard_jones_mc_benchmark** - ベンチマークスイート
包括的なベンチマーキングツール：
- PythonとRustiの性能比較
- スケーリング解析
- メモリ使用量プロファイリング
- 結果の検証

## クイックスタート

### Python版
```bash
cd lennard_jones_mc
# lennard_jones_mc/README.mdの指示に従ってください
```

### Rust版
```bash
cd lennard_jones_mc_rs
# lennard_jones_mc_rs/README.mdの指示に従ってください
```

### ベンチマーク
```bash
cd lennard_jones_mc_benchmark
# lennard_jones_mc_benchmark/README.mdの指示に従ってください
```

## 主な機能

- **Monte Carloシミュレーション**: NVTおよびGrand Canonical Ensemble実装
- **3次元シミュレーション**: 現実的なシステム向けの完全な3D対応
- **高性能**: 最適化されたPython版と高速なRust版の両方
- **解析ツール**: 相図生成、VLE計算
- **ベンチマーキング**: 詳細な性能比較とプロファイリング
- **柔軟なパラメータ**: カットオフ、セルリスト、システムパラメータのカスタマイズ可能

## リポジトリ構成

```
.
├── lennard_jones_mc/              # Python実装
├── lennard_jones_mc_rs/           # Rust実装
└── lennard_jones_mc_benchmark/    # ベンチマーク用ツール
```

## ライセンス

このプロジェクトは研究および教育目的で提供されています。

## ドキュメント

詳細なドキュメントと使用方法については、各サブディレクトリのREADMEファイルを参照してください：
- [Python実装ガイド](lennard_jones_mc/README.md)
- [Rust実装ガイド](lennard_jones_mc_rs/README.md)
- [ベンチマーキングガイド](lennard_jones_mc_benchmark/README.md)
