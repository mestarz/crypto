#!/bin/bash
conda env list

# 获取当前文件的目录
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
export PYTHONPATH=$SCRIPT_DIR:$PYTHONPATH

conda activate okx && python main.py
