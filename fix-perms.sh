#!/usr/bin/env bash
# node_modules 等のコンテナ専用volumeを node が書けるようにする。
# named volume は既定 root 所有で生成されるため、起動時に所有者を直す。
# root で実行（entrypoint が sudo 経由で呼ぶ）。
set -e
for d in /workspace/node_modules; do
  if [ -d "$d" ]; then
    chown node:node "$d" 2>/dev/null || true
  fi
done
