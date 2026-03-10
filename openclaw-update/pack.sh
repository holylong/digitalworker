#!/usr/bin/env bash
# OpenClaw 一键打包脚本
# 使用方式: ./pack.sh [输出目录]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${1:-$SCRIPT_DIR}"
PACKAGE_NAME="openclaw"

# 获取版本号
VERSION=$(node -p "require('$SCRIPT_DIR/package.json').version")
TGZ_FILE="$OUTPUT_DIR/${PACKAGE_NAME}-${VERSION}.tgz"

echo "========================================"
echo "OpenClaw 打包脚本"
echo "========================================"
echo "版本: $VERSION"
echo "输出: $TGZ_FILE"
echo "========================================"

# 检查 dist 目录是否存在
if [ ! -d "$SCRIPT_DIR/dist" ]; then
    echo "[1/3] 构建 dist 目录..."
    cd "$SCRIPT_DIR"
    node scripts/tsdown-build.mjs
    node scripts/copy-plugin-sdk-root-alias.mjs
    pnpm build:plugin-sdk:dts
else
    echo "[1/3] dist 目录已存在，跳过构建"
fi

# 打包
echo "[2/3] 打包中..."
cd "$SCRIPT_DIR"
npm pack --ignore-scripts

# 移动到输出目录
if [ "$OUTPUT_DIR" != "$SCRIPT_DIR" ]; then
    mv "$SCRIPT_DIR/${PACKAGE_NAME}-${VERSION}.tgz" "$TGZ_FILE"
fi

echo "[3/3] 打包完成!"
echo ""
echo "安装方式:"
echo "  pnpm add ./${PACKAGE_NAME}-${VERSION}.tgz"
echo ""
echo "或全局安装:"
echo "  pnpm add -g ./${PACKAGE_NAME}-${VERSION}.tgz"
echo ""
echo "文件大小: $(ls -lh "$TGZ_FILE" | awk '{print $5}')"