# レビュー指摘集約 (review_findings.md)

> impl-security-reviewer と impl-code-reviewer の指摘を集約するファイル。

最終更新: <YYYY-MM-DD>

---

## 重大度

| Lv | 定義 | 対応期限 |
|---|---|---|
| BLOCKER | 既知の脆弱性 / 認可漏れ / シークレット混入 / PII 漏洩 | 即時 |
| MAJOR | OWASP 対策欠落 / 仕様乖離 / 監査ログ未記録 | マイルストーン内 |
| MINOR | 設定改善 / 軽微 CVE / 命名統一 / テスト命名 | バックログ |
| INFO | 観察・提案 | 任意 |

---

# Security Review

## YYYY-MM-DD (スコープ: M<N>)

### F-YYYY-MM-DD-001 [BLOCKER] <一行サマリ>
- **ファイル**: src/path/to/file.py:NN
- **問題**: ...
- **リスク**: <実害シナリオ>
- **仕様**: docs/03_detailed_design/07_セキュリティ実装方針.md §X.Y
- **推奨修正**: ...
- **担当チケット**: T-XXX → 修正チケット T-XXX-fix-001 を起票

---

# Code Review

## YYYY-MM-DD (スコープ: M<N>)

### CR-YYYY-MM-DD-001 [MAJOR] <一行サマリ>
- **ファイル**: src/path/to/file.ts:NN
- **問題**: ...
- **仕様**: docs/03_detailed_design/01_API仕様.md / EP-042
- **推奨修正**: ...
- **担当チケット**: T-XXX → 修正チケット T-XXX-fix-002 を起票
