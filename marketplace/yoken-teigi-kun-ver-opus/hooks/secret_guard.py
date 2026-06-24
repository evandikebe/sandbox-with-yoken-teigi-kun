#!/usr/bin/env python3
"""
secret_guard.py — Claude Code PreToolUse hook

Write/Edit/MultiEdit が呼ばれる直前に、書き込まれる内容と対象ファイル名から
シークレットらしき値(API キー・トークン・パスワード等)を検出してブロックする。

入力: stdin に JSON ({tool_name, tool_input: {file_path, content/new_string, ...}})
出力: exit 0 = OK, exit 2 = ブロック (stderr に理由)
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

# ---- 検出パターン --------------------------------------------------------
# 1. 明らかに「キーの値らしい」高エントロピー文字列を含む代入
SECRET_VALUE_PATTERNS: list[tuple[re.Pattern, str]] = [
    # AWS
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID らしき値"),
    (re.compile(r"aws_secret_access_key\s*=\s*['\"][A-Za-z0-9/+=]{40}['\"]", re.I), "AWS Secret Access Key"),
    # Google / GCP
    (re.compile(r"AIza[0-9A-Za-z\-_]{35}"), "Google API Key"),
    (re.compile(r"ya29\.[0-9A-Za-z\-_]+"), "Google OAuth Token"),
    # GitHub
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"), "GitHub Token"),
    # Slack
    (re.compile(r"xox[abpr]-[A-Za-z0-9-]{10,}"), "Slack Token"),
    # Stripe
    (re.compile(r"sk_live_[A-Za-z0-9]{20,}"), "Stripe Live Secret Key"),
    (re.compile(r"rk_live_[A-Za-z0-9]{20,}"), "Stripe Restricted Key"),
    # OpenAI / Anthropic
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "OpenAI/Anthropic-like Secret Key"),
    (re.compile(r"sk-ant-[A-Za-z0-9\-_]{20,}"), "Anthropic API Key"),
    # JWT (本物っぽいもの。署名部が30文字以上のもの)
    (re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{30,}"), "JWT (本物の可能性)"),
    # Private key PEM
    (re.compile(r"-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----"), "PEM 形式の秘密鍵"),
]

# 2. キー名 + 直書き値 の代入文 (例: PASSWORD = "abcd1234..." )
ASSIGN_PATTERN = re.compile(
    r"""(?xi)
    (?:^|[^A-Za-z0-9_])
    (api[_-]?key|secret(?:[_-]?key)?|access[_-]?token|auth[_-]?token|password|passwd|pwd|client[_-]?secret|private[_-]?key)
    \s*[:=]\s*
    (?:r?b?["'])
    ([A-Za-z0-9+/=_\-\.]{12,})
    (?:["'])
    """
)

# 3. 一般的なダミー値はホワイトリスト(誤検出を減らす)
DUMMY_VALUES = {
    "password", "your-password", "changeme", "secret", "your-secret", "example",
    "xxxxxxxx", "abcdef0123456789", "your-api-key-here", "<your-key>", "REPLACE_ME",
    "test", "dummy", "placeholder", "todo", "tbd",
}

# ファイル名で許可されるもの (シークレットを書く前提がないファイル以外)
# .env.example などはコミット対象として正しい(値はダミー想定)
ALLOWLIST_PATH_PARTS = {
    ".env.example", "secrets.example", "credentials.example",
}

# 完全に除外するファイル(documentation, テスト等で意図的に書く)
SKIP_PATH_PATTERNS = [
    re.compile(r"hooks/secret_guard\.py$"),  # 自分自身は当然ヒットするので除外
    re.compile(r"\.md$"),                    # README 内のサンプルは許容(別の手段でレビュー)
    re.compile(r"agents/.*\.md$"),
]


def _extract_payload(data: dict) -> tuple[str, str]:
    """tool_input から file_path と書き込み内容を抽出"""
    ti = data.get("tool_input", {}) or {}
    fp = ti.get("file_path") or ti.get("path") or ""
    content = (
        ti.get("content")
        or ti.get("new_string")
        or ti.get("text")
        or ""
    )
    # MultiEdit
    if "edits" in ti and isinstance(ti["edits"], list):
        content = "\n".join(
            (e.get("new_string") or "") for e in ti["edits"]
        )
    return fp, content


def _looks_like_dummy(value: str) -> bool:
    v = value.lower()
    if v in DUMMY_VALUES:
        return True
    # 連続する同じ文字 / 'x' だらけ
    if len(set(v)) <= 3:
        return True
    return False


def scan(file_path: str, content: str) -> list[str]:
    findings: list[str] = []
    # スキップファイル
    for pat in SKIP_PATH_PATTERNS:
        if pat.search(file_path):
            return findings
    # ALLOWLIST: .env.example 等は内容のチェック緩める(本物のキーがハードコードされていないか軽くだけ見る)
    in_allowlist = any(part in file_path for part in ALLOWLIST_PATH_PARTS)

    # 1. 明示パターン
    for pat, name in SECRET_VALUE_PATTERNS:
        m = pat.search(content)
        if m:
            findings.append(f"[BLOCK] {name} を検出: 抜粋='{m.group(0)[:30]}...'")

    # 2. KEY = "VALUE" 形式
    if not in_allowlist:
        for m in ASSIGN_PATTERN.finditer(content):
            key, value = m.group(1), m.group(2)
            if _looks_like_dummy(value):
                continue
            # 環境変数読み出し風(os.environ, process.env)は OK
            line_start = content.rfind("\n", 0, m.start()) + 1
            line = content[line_start:content.find("\n", m.end()) if content.find("\n", m.end()) >= 0 else None]
            if "os.environ" in line or "process.env" in line or "getenv" in line:
                continue
            findings.append(
                f"[BLOCK] '{key}' に値が直書きされています: '{value[:6]}...{value[-3:] if len(value) > 9 else ''}'。環境変数や Secret Manager 経由にしてください。"
            )

    return findings


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        # 入力が読めなければ通す(hook 障害でブロックすると開発が止まる)
        print(f"[secret_guard] stdin parse error: {e}", file=sys.stderr)
        return 0

    tool = data.get("tool_name", "")
    if tool not in {"Write", "Edit", "MultiEdit"}:
        return 0

    fp, content = _extract_payload(data)
    if not content:
        return 0

    findings = scan(fp, content)
    if findings:
        print("[secret_guard] シークレットらしき値の書き込みをブロックしました:", file=sys.stderr)
        for f in findings:
            print(f"  - {f}", file=sys.stderr)
        print(f"  対象ファイル: {fp}", file=sys.stderr)
        print("  対応: 環境変数 (os.environ / process.env) や Secret Manager 経由に変更してください。", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
