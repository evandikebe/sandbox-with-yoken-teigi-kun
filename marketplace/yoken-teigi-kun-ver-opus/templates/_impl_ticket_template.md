---
ticket_id: T-XXX
spec_refs: []                # [F-014, EP-042, SC-032] のように関連仕様 ID を列挙
type: backend                # backend | frontend | db | batch | test | infra | shared
title: <端的に何を作るか — 50字以内>
milestone: M1                # M1 / M2 / M3 / M4
priority: must               # must | should | could
depends_on: []               # [T-001, T-005] 先に完了する必要があるチケット
addBlocks: []                # このチケットが完了するまで開始できないチケット
touches_shared: false        # true なら orchestrator が単独実行する
estimated_files:
  - src/path/to/file.py
estimated_effort: 1d         # 0.5d / 1d / 2d など
owner: null                  # 担当中のエージェント名 (impl-orchestrator が記入)
status: open                 # open | in_progress | review | done | blocked
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
---

# T-XXX <title>

## 仕様

該当する仕様の引用 or 要約をここに。`spec_refs` の各 ID について、

- 仕様ファイルへのリンク: `[F-014](docs/01_requirements/03_機能要件.md#F-014)`
- 関係する API 仕様: `[EP-042](docs/03_detailed_design/01_API仕様.md#EP-042)`
- 関係する画面: `[SC-032](docs/04_ui_mocks/screens/SC-032_スタッフ詳細_フォロー.html)`

の形で必ず参照を張ること。

## 完了条件 (Definition of Done)

最低限以下にチェックを入れて完了とする。チケットの性質によって項目を増減してよい。

- [ ] 仕様の成功パス + 失敗パスを実装
- [ ] バリデーション規則 (`docs/03_detailed_design/04_バリデーション規則.md`) 準拠
- [ ] エラーコード (`docs/03_detailed_design/05_エラー設計.md`) 準拠
- [ ] 認可ロジックがロール × リソース × 関係で検証されている
- [ ] 監査ログ対象なら記録されている (`docs/03_detailed_design/07_セキュリティ実装方針.md`)
- [ ] 単体テスト pass
- [ ] 結合テスト pass(該当する場合)
- [ ] lint clean / type-check clean
- [ ] `@spec` タグ が新規/変更ファイルに記載されている
- [ ] PII を扱う処理ならマスキング検証テストがある
- [ ] 直感に反する判断は `IMPLEMENTATION_GUIDE.md` §5 を参照、関連がある場合はコード内コメントで明示

## 実装メモ

(担当エージェントが書き残す。設計判断、トレードオフ、後続チケットへの申し送り事項など)

## 並走中に触ってはいけないファイル

(orchestrator が並列実行時に書き込む。他チケットの `estimated_files` を列挙)

## 証拠 (Evidence)

完了時に **担当エージェントが必ず埋める**:

- 実装ファイル:
  - (列挙)
- テスト結果:
  - <コマンド> → N passed, M failed (時刻)
- lint:
  - <コマンド> → clean
- type-check:
  - <コマンド> → clean
- セキュリティ自己チェック:
  - 認可: ✅ <どこで判定しているか>
  - 入力検証: ✅ <スキーマファイル>
  - 監査ログ: ✅ or 該当なし
  - PII: ✅ <マスキング箇所> or 該当なし
- 関連 commit / PR: (あれば)
