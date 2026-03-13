#!/usr/bin/env bash

set -euo pipefail

REPO="xiaodonghsu/WindowsScreenDeviceAgent"
BASE_DIR="/home/jh/site-content/download/agent"
API_URL="https://api.github.com/repos/${REPO}/releases/latest"

echo "查询最新 Release..."

# 获取 release json
release_json=$(curl -fsSL "$API_URL")

# GitHub tag，例如 v1.0.0.6
tag_name=$(printf '%s' "$release_json" | jq -r '.tag_name')

if [[ -z "$tag_name" || "$tag_name" == "null" ]]; then
  echo "未获取到版本号"
  exit 1
fi

# 去掉前面的 v
version="${tag_name#v}"

target_dir="${BASE_DIR}/${version}"
target_file="${target_dir}/ExpoAgent.exe"

echo "GitHub tag: ${tag_name}"
echo "目录版本: ${version}"
echo "目标目录: ${target_dir}"

# 如果目录存在则不下载
if [[ -d "$target_dir" ]]; then
  echo "版本已存在，无需下载"
  exit 0
fi

mkdir -p "$target_dir"

# 查找 ExpoAgent.exe 下载地址
download_url=$(printf '%s' "$release_json" | jq -r '
  .assets[]
  | select(.name == "ExpoAgent.exe")
  | .browser_download_url
' | head -n 1)

if [[ -z "$download_url" || "$download_url" == "null" ]]; then
  echo "未找到 ExpoAgent.exe"
  rmdir "$target_dir" 2>/dev/null || true
  exit 1
fi

echo "开始下载: $download_url"
curl -fL "$download_url" -o "$target_file"

echo "下载完成: $target_file"