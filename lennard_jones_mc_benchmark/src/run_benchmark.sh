#!/bin/bash
# ベンチマーク実行スクリプト
# 使用: ./run_benchmark.sh または bash run_benchmark.sh

cd "$(dirname "$0")"
/Users/yamamoto/Desktop/CompPhysHack/.venv-base/bin/python benchmark_python_rust.py
