#!/usr/bin/env python3
"""
post_format.py — Claude Code PostToolUse hook

Write/Edit の直後に対象ファイルへフォーマッタをベストエフォートで適用する。
フォーマッタが見つからなければ silent に exit 0。

対応:
- .py            → ruff format → なければ black
- .ts/.tsx/.js/.jsx → prettier → なければ biome
- .json/.md      → prettier (任意)
- .sql           → sqlfluff fix (任意)
"""
from __future__ import annotations
import json
import shutil
import subprocess
import sys
from pathlib import Path


def _which(*names: str) -> str | None:
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


def _run(cmd: list[str]) -> int:
    try:
        return subprocess.run(cmd, capture_output=True, timeout=20).returncode
    except Exception:
        return -1


def format_python(fp: str) -> None:
    ruff = _which("ruff")
    if ruff:
        _run([ruff, "format", fp])
        # ついでに lint --fix (安全な修正のみ)
        _run([ruff, "check", "--fix", "--select", "I,UP,F401", fp])
        return
    black = _which("black")
    if black:
        _run([black, "-q", fp])


def format_ts(fp: str) -> None:
    npx = _which("npx")
    # prettier
    if npx:
        rc = _run([npx, "--no-install", "prettier", "--write", fp])
        if rc == 0:
            return
    # biome
    biome = _which("biome")
    if biome:
        _run([biome, "format", "--write", fp])


def format_json_md(fp: str) -> None:
    npx = _which("npx")
    if npx:
        _run([npx, "--no-install", "prettier", "--write", fp])


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
    if not fp or not Path(fp).exists():
        return 0

    f = fp.replace("\\", "/")

    # docs/ や hooks/ は触らない
    if "/docs/" in f or "/hooks/" in f or "/.claude/" in f:
        return 0

    if f.endswith(".py"):
        format_python(fp)
    elif f.endswith((".ts", ".tsx", ".js", ".jsx")):
        format_ts(fp)
    elif f.endswith((".json", ".md")):
        format_json_md(fp)
    # 失敗しても黙って終了(format は best effort)
    return 0


if __name__ == "__main__":
    sys.exit(main())
