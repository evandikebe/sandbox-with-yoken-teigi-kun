# Phase <N> アンチレビュー結果

- レビュー実施: YYYY-MM-DD HH:MM
- レビュアー: spec-critic
- 対象フェーズ: Phase <N>（<フェーズ名>）
- 対象成果物:
  - docs/...
  - docs/...

## 判定

**FAIL（差し戻し） / PASS_WITH_CONDITIONS / PASS**

| 重大度 | 件数 |
|---|---|
| BLOCKER | n |
| MAJOR | n |
| MINOR | n |
| INFO | n |

> 判定ルール: BLOCKER ≥1 → FAIL / BLOCKER 0 & MAJOR ≥1 → PASS_WITH_CONDITIONS / それ以外 → PASS

## 機械検証の結果

| 検証 | 方法 | 結果 |
|---|---|---|
| placeholder 残り（TODO/TBD/…/YYYY-MM-DD） | grep | 検出 n 件 |
| ID 参照の双方向突き合わせ | grep + comm | 欠落 n 件 |
| ファイル存在 / リンク切れ | Glob / Bash | 切れ n 件 |

## 指摘一覧

### B-1 [BLOCKER] <一行サマリ>
- **ファイル**: docs/path/to/file.md（該当セクション）
- **問題**: <何が欠落 / 何と矛盾しているか。事実ベースで>
- **影響**: <このまま進むと後続フェーズで何が起きるか>
- **推奨修正**: <具体的に>
- **担当**: <該当フェーズの担当エージェント>

### M-1 [MAJOR] <一行サマリ>
- （同上の形式）

### N-1 [MINOR] <一行サマリ>
- （同上の形式）

### I-1 [INFO] <観察・提案>
- ...

## PASS_WITH_CONDITIONS の条件（該当時のみ）

- [ ] <次フェーズと並行で修正すべき項目>（期限: 次フェーズ完了まで）

## 未確認事項（ユーザー / orchestrator への持ち帰り）

- <レビュアーだけでは判断できなかった点>

## 再レビュー記録（差し戻し時のみ追記）

| 回 | 日時 | 判定 | メモ |
|---|---|---|---|
| 1 | YYYY-MM-DD HH:MM | FAIL | 初回 |
| 2 | | | |
