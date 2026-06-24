#!/usr/bin/env python3
"""
docs_readonly_guard.py — Claude Code PreToolUse hook

実装エージェントは docs/ 配下の仕様ドキュメントを編集してはいけない (IMPL_RULES R-3)。
唯一の例外は docs/_impl_state/ 配下(実装側の状態管理)。

このガードは **実装フェーズ中のみ** 有効。設計フェーズ(spec-orchestrator 等)は docs/ に
書き込む必要があるため、マーカーファイル `docs/_impl_state/.impl_active` が存在する場合のみ
ブロックする(マーカーは impl-orchestrator が Phase A で作成する)。

入力: stdin JSON
出力: exit 0 = OK, exit 2 = ブロック
"""
from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path

# 実装フェーズ中であることを示すマーカー(impl-orchestrator が作成)
IMPL_ACTIVE_MARKER = "docs/_impl_state/.impl_active"


def _impl_phase_active(cwd: str | None) -> bool:
    """マーカーファイルの有無で実装フェーズ中かを判定。環境変数でも強制可。"""
    if os.environ.get("IMPL_DOCS_GUARD", "") == "1":
        return True
    base = Path(cwd) if cwd else Path.cwd()
    try:
        return (base / IMPL_ACTIVE_MARKER).exists()
    except Exception:
        return False


def _normalize(p: str) -> str:
    """Windows / POSIX 両対応で / 区切りに正規化"""
    return p.replace("\\", "/")


def is_blocked(file_path: str, cwd: str | None) -> tuple[bool, str]:
    if not file_path:
        return False, ""

    fp = _normalize(file_path)
    # cwd 配下に揃える(絶対パスでも相対パスでも判定したい)
    if cwd:
        cwd_n = _normalize(cwd)
        if fp.startswith(cwd_n):
            rel = fp[len(cwd_n):].lstrip("/")
        else:
            rel = fp
    else:
        rel = fp

    # docs/ 配下か?
    parts = rel.split("/")
    # 絶対パスのケースもあるので、いずれかの位置に "docs" が現れるか見る
    # ただし誤検出を減らすために、"docs/" がパスのコンポーネント境界に来る場合のみ
    has_docs = "docs" in parts
    if not has_docs:
        return False, ""

    docs_idx = parts.index("docs")
    sub = parts[docs_idx + 1] if len(parts) > docs_idx + 1 else ""

    # 例外: docs/_impl_state/ は許可
    if sub == "_impl_state":
        return False, ""

    return True, f"docs/{sub}{'/...' if len(parts) > docs_idx + 2 else ''}"


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    tool = data.get("tool_name", "")
    if tool not in {"Write", "Edit", "MultiEdit"}:
        return 0

    ti = data.get("tool_input", {}) or {}
    fp = ti.get("file_path") or ti.get("path") or ""
    cwd = data.get("cwd")

    # 設計フェーズ中はガード無効(docs/ への書き込みは設計エージェントの正当な仕事)
    if not _impl_phase_active(cwd):
        return 0

    blocked, sample = is_blocked(fp, cwd)
    if blocked:
        print("[docs_readonly_guard] docs/ 配下への書き込みをブロックしました。", file=sys.stderr)
        print(f"  対象: {fp}", file=sys.stderr)
        print(f"  該当: {sample}", file=sys.stderr)
        print("  ルール: references/IMPL_RULES.md R-3 (docs/ は読み取り専用、書けるのは docs/_impl_state/ のみ)", file=sys.stderr)
        print("  対応: 仕様の更新は spec-orchestrator または人間に依頼。実装側の状態は docs/_impl_state/ に書く。", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
