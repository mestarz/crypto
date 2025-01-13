#!/bin/bash

# 创建临时文件列表
FILE_LIST=$(mktemp)

# 查找所有文件，排除.git目录、.gitignore中的内容和output目录
find . -type f | grep -v '/\.git/' | grep -v '/__pycache__/' | grep -v '\.log$' | \
grep -v '/\.vscode/' | grep -v '/\.idea/' | grep -v '\.so$' | grep -v '/tools/.*\.ini$' | \
grep -v '/output/' > $FILE_LIST

# 添加config目录中的.so文件
find config -type f -name '*.so' >> $FILE_LIST

# 创建输出目录
mkdir -p ./output

# 创建打包文件
OUTPUT_FILE="./output/crypto_package_$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf $OUTPUT_FILE --transform 's,^,crypto/,' --files-from $FILE_LIST

# 清理临时文件
rm $FILE_LIST

echo "Package created: $OUTPUT_FILE"

if [ -z "$1" ]; then
  echo "Usage: $0 <target_ip>"
  exit 1
fi

scp $OUTPUT_FILE root@$1:/root/workspace
