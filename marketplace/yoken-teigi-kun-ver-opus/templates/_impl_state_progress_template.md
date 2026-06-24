# 実装進捗ダッシュボード

> 自動 + 手動更新。impl-orchestrator が各エージェントの完了報告を受けるたびに最新化する。

最終更新: <YYYY-MM-DD HH:MM>
レビュー実施日: <YYYY-MM-DD>

---

## マイルストーン進捗

| Milestone | スコープ | 完了 / 全体 | 状態 |
|---|---|---|---|
| M1 基盤構築 | infra / shared / 認証 / 監査ログ基盤 | 0 / N | 進行中 |
| M2 コア機能 | F-002〜F-021 を中心とした主要ユースケース | 0 / N | 待機 |
| M3 上司・管理機能 | F-016〜F-031 | 0 / N | 待機 |
| M4 ハーディング | 負荷試験 / セキュリティ / 監視 / 運用 | 0 / N | 待機 |

---

## チケット一覧

### M1: 基盤構築

| Ticket | Type | 仕様 | 状態 | 担当 | 依存 |
|---|---|---|---|---|---|
| T-001 | infra | — | open | — | — |
| T-002 | shared | NF-009 (構造化ログ) | open | — | T-001 |
| T-003 | db | NF-004 (認証) | open | — | T-001 |
| ... | | | | | |

### M2: コア機能

| Ticket | Type | 仕様 | 状態 | 担当 | 依存 |
|---|---|---|---|---|---|
| T-010 | backend | F-009, EP-020 | open | — | T-005 |
| ... | | | | | |

---

## 依存グラフ(初期実行可能セット)

`depends_on` が空のチケット = **今すぐ並列起動できる**:

- T-001 (infra: リポジトリ初期化)
- T-002 (shared: ロガー)

---

## 並列実行履歴

| 日時 | 起動エージェント | チケット | 結果 |
|---|---|---|---|
| YYYY-MM-DD HH:MM | impl-backend-engineer | T-010 | completed |
| YYYY-MM-DD HH:MM | impl-frontend-engineer | T-011 | completed (並走) |

---

## ブロッカー

(blocked 状態のチケットと理由)

- なし

---

## レビュー結果サマリ

- 最新セキュリティレビュー: <YYYY-MM-DD>(BLOCKER: 0 / MAJOR: 0 / MINOR: 0)
- 最新コードレビュー: <YYYY-MM-DD>(MAJOR: 0 / MINOR: 0)
- 仕様欠落発見: <数件> → `docs/_impl_state/spec_gaps.md`
- インシデント: <数件> → `docs/_impl_state/incidents.md`

---

## 次のアクション

(orchestrator が「次に何を並列で走らせるか」を書く)

1. T-XXX, T-YYY を並列起動 (impl-backend-engineer × 2)
2. T-ZZZ は touches_shared = true なので単独実行
3. M1 完了見込み: <日付>
