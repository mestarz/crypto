#!/bin/bash

# 获取当前文件的目录
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
export PYTHONPATH=$SCRIPT_DIR:$PYTHONPATH

python main.py
