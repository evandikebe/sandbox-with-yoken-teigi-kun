#!/usr/bin/env python3
"""
pii_check.py — Claude Code PreToolUse hook

src/ や tests/ に書き込む内容に「明らかに本物の個人情報パターン」が含まれていないか軽くチェック。
誤検出が出やすい領域なので、デフォルトは exit 1 (警告) のみ。環境変数 IMPL_PII_STRICT=1 でブロック化。

検出対象:
- 日本の電話番号らしき値 (090/080/070-XXXX-XXXX, +81-XX-XXXX-XXXX)
- メールアドレス + 日本人氏名 が近接して登場
- マイナンバーらしき12桁
- クレジットカードらしき値 (Luhn チェック)
"""
from __future__ import annotations
import json
import os
import re
import sys

# 日本の電話 (簡易)
JP_PHONE = re.compile(r"\b(0[7-9]0)[-\s]?(\d{4})[-\s]?(\d{4})\b")
# 国際表記
INTL_PHONE = re.compile(r"\+81[-\s]?\d{1,4}[-\s]?\d{1,4}[-\s]?\d{4}")
# マイナンバーらしき12桁(連続数字)
MY_NUMBER = re.compile(r"\b\d{12}\b")
# クレジットカード (空白/ハイフン除去後 13-19 桁)
CC = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")
# 日本人氏名 (簡易: 漢字2-4文字 + スペース + 漢字2-4文字、または カタカナ4-8文字)
JP_NAME = re.compile(r"[一-龥]{2,4}[ 　][一-龥]{2,4}|[ァ-ヺー]{4,8}")
# メアド
EMAIL = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")

# テスト用ダミーと思われるドメインは除外
DUMMY_EMAIL_DOMAINS = ("example.com", "example.org", "example.net", "test.com", "localhost")
DUMMY_NAMES = {"山田太郎", "山田 太郎", "テストユーザー", "テスト ユーザー", "田中 太郎", "田中太郎"}


def _is_dummy_email(addr: str) -> bool:
    return any(addr.endswith("@" + d) for d in DUMMY_EMAIL_DOMAINS)


def _luhn_ok(digits: str) -> bool:
    """クレカらしき数字列の Luhn チェック"""
    s = 0
    for i, c in enumerate(reversed(digits)):
        n = int(c)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        s += n
    return s % 10 == 0


def _extract_payload(data: dict) -> tuple[str, str]:
    ti = data.get("tool_input", {}) or {}
    fp = ti.get("file_path") or ti.get("path") or ""
    content = ti.get("content") or ti.get("new_string") or ti.get("text") or ""
    if "edits" in ti and isinstance(ti["edits"], list):
        content = "\n".join((e.get("new_string") or "") for e in ti["edits"])
    return fp, content


def scan(content: str) -> list[str]:
    findings: list[str] = []
    # 電話
    for m in JP_PHONE.finditer(content):
        v = m.group(0)
        # ダミー (000-0000-0000) は除外
        digits = re.sub(r"\D", "", v)
        if len(set(digits)) <= 2:
            continue
        findings.append(f"日本国内電話番号らしき値: {v}")

    for m in INTL_PHONE.finditer(content):
        findings.append(f"国際表記電話番号らしき値: {m.group(0)}")

    # マイナンバー
    for m in MY_NUMBER.finditer(content):
        digits = m.group(0)
        if len(set(digits)) <= 2:
            continue
        # 連番(000000000000 / 123456789012) も除外
        if digits in {"123456789012", "012345678901"}:
            continue
        findings.append(f"12桁数字 (マイナンバーの可能性): {digits[:4]}...{digits[-4:]}")

    # クレカ
    for m in CC.finditer(content):
        digits = re.sub(r"[ -]", "", m.group(0))
        if not (13 <= len(digits) <= 19):
            continue
        if len(set(digits)) <= 2:
            continue
        if _luhn_ok(digits):
            findings.append(f"クレカ番号らしき値 (Luhn OK): {digits[:4]}...{digits[-4:]}")

    # メアド (ダミー除外)
    real_emails = [e for e in EMAIL.findall(content) if not _is_dummy_email(e)]
    real_names = [n for n in JP_NAME.findall(content) if n not in DUMMY_NAMES]
    if real_emails and real_names:
        findings.append(
            f"実在しそうなメールアドレス + 氏名の近接: 例 '{real_names[0]}' / '{real_emails[0]}'"
        )
    elif len(real_emails) >= 3:
        findings.append(f"実在しそうなメールアドレス複数: {real_emails[:3]}")

    return findings


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    tool = data.get("tool_name", "")
    if tool not in {"Write", "Edit", "MultiEdit"}:
        return 0

    fp, content = _extract_payload(data)
    if not content:
        return 0

    # docs/ や hooks/ 自身は対象外
    if "/docs/" in fp.replace("\\", "/") or fp.endswith("pii_check.py"):
        return 0

    findings = scan(content)
    if not findings:
        return 0

    print("[pii_check] 個人情報らしきパターンを検出しました:", file=sys.stderr)
    for f in findings:
        print(f"  - {f}", file=sys.stderr)
    print(f"  対象ファイル: {fp}", file=sys.stderr)
    print("  対応: テストデータならダミー(example.com / 090-0000-0000)に置換してください。", file=sys.stderr)

    strict = os.environ.get("IMPL_PII_STRICT", "0") == "1"
    return 2 if strict else 1


if __name__ == "__main__":
    sys.exit(main())
