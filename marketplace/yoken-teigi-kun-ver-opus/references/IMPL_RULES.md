# 実装エージェント 共通ルール (IMPL_RULES)

> このファイルは **実装エージェントチーム全員が起動時に最初に読む** 不変ルール集です。
> 個別エージェントの `.md` から参照されます。仕様駆動開発・並列実行・セキュリティ・保守性の土台。

## 参照方法

- プラグインとして導入している場合: `${CLAUDE_PLUGIN_ROOT}/references/IMPL_RULES.md`
- 手動コピーで導入している場合: `.claude/references/IMPL_RULES.md`（install.md の手順で配置）

---

## 0. 「実装エージェントチーム」とは

`docs/` 配下の設計ドキュメントを **唯一の真実(Single Source of Truth)** として、`src/` 配下にコードを生成・編集する Claude Code サブエージェント群です。

```
[docs/]  ←  唯一の仕様
   │
   ▼
[impl-orchestrator] が読み込み、チケットに分解
   │
   ├─ [impl-ticket-planner]  仕様 → チケット化
   │
   ├─ [impl-backend-engineer]   ┐
   ├─ [impl-frontend-engineer]  │ 並列実行
   ├─ [impl-db-engineer]        │ (依存解決後)
   ├─ [impl-batch-engineer]     │
   ├─ [impl-test-engineer]      ┘
   │
   ├─ [impl-security-reviewer]  最後 or マイルストーン末で集約レビュー
   └─ [impl-code-reviewer]      最後 or マイルストーン末で集約レビュー
   │
   ▼
[src/]    ←  生成されたコード
```

---

## 1. 不変ルール (Immutable Rules)

実装エージェントは以下を **絶対に破ってはいけません**。違反は即停止 + `docs/_impl_state/incidents.md` への記録対象。

### R-1: 仕様駆動 (Spec-Driven)

- **`docs/` 配下が唯一の仕様**。実装は必ずいずれかの仕様 ID(`F-XXX`, `SC-XXX`, `EP-XXX`, `NF-XXX` 等)に紐づく。
- 仕様にない機能を実装しない。「ついで実装」「気を利かせた追加」は禁止。
- 仕様が曖昧/欠落していたら **実装に進まず** `docs/_impl_state/spec_gaps.md` に追記し、orchestrator にエスカレーション。
- 仕様とコードが矛盾したら **仕様が勝つ**。コードを直す or 仕様変更チケットを起票。

### R-2: トレーサビリティ (Traceability)

- 生成する **すべてのコード成果物** は、ファイル冒頭または該当関数の docstring に対応する仕様 ID を必ず書く。
  - 例(TypeScript): `/** @spec F-009, SC-010 — 要注意スタッフリスト */`
  - 例(Python): `"""@spec F-014 — フォローコメント記録 (詳細設計 §4.3)"""`
- コミットメッセージにも仕様 ID を含める。例: `feat(F-009): implement attention-staff list endpoint`
- これによりレビュー時に **仕様 → 実装 → テストの追跡が機械的に可能** になる。

### R-3: docs/ は読み取り専用

- 実装エージェントは **`docs/` 配下に書き込み禁止**。仕様の更新は人間または設計エージェント（正式な変更は `spec-change-manager` の変更管理フロー = CR-XXX 起票 → 影響分析 → 更新 → spec-critic 再レビュー）の責務。
- 例外: `docs/_impl_state/` 配下のみ書き込み可(実装側の状態管理に限る)。
- 仕様の不備を発見しても直接編集しない。`docs/_impl_state/spec_gaps.md` に起票して orchestrator 経由で人間にレビュー依頼。

### R-4: シークレットを書かない

- API キー・トークン・パスワード・接続文字列を **コードにハードコードしない**。
- `.env.example` のみコミット、実値は環境変数 or シークレットマネージャ経由。
- もしユーザーが対話の中で実シークレットを提示しても、ファイルには書かない。Claude Code hook (`secret_guard.py`) がブロックする想定だが、エージェント側でも自己防衛する。

### R-5: 個人情報・PII 最小化

- ログ・エラーメッセージ・LLM プロンプトに PII (氏名・住所・電話番号・メール本文等)を載せない。
- 識別子は ID (UUID / 内部 ID)までに留める。
- 仕様に「マスキング」「匿名化」が定義されている処理は **必ず通す**。テストでマスキングが効いているか検証する。

### R-6: 並列実行の規律

- 各エージェントは自分の **担当チケットのファイル群以外を変更しない**。
- 共通ファイル(`pyproject.toml`, `package.json`, `tsconfig.json`, 共有ユーティリティ等)を編集する場合は **必ず該当チケットの `touches_shared: true` フラグを立てて** orchestrator が直列化する。
- 同じファイルへの並列書き込みは禁止。チケット間で共有が必要なコードは事前にインターフェースを切る。

### R-7: 出力先は `src/` 配下のみ（コードとドキュメントの厳密分離）

- 実装コードは **`src/` 配下に限定**。プロジェクト直下に新規ファイルを作らない。
- **`docs/` 配下にコード（`.ts/.tsx/.js/.py/.go` 等の実装ファイル）を絶対に置かない**。`docs/` は設計ドキュメント（.md / モック .html / 図）専用。設計ドキュメント内でコードを示す場合は Markdown のコードブロックとして書く（実体ファイルにしない）。
- リポジトリは「`docs/` = ドキュメント、`src/` = コード」に分離されている前提。既存プロジェクトでコードが `docs/` や直下に混在していたら、orchestrator が実装着手前に `src/` へ正規化する。
- ただし以下は例外として `src/` 外でも作成可:
  - `src/` 直下相当の設定ファイル: `package.json`, `pyproject.toml`, `tsconfig.json`, `.eslintrc`, `.ruff.toml`, `alembic.ini`, `docker-compose.yml`, `Dockerfile`, `.env.example`
  - CI 設定: `.github/workflows/`
  - 実装状態: `docs/_impl_state/`
  - テスト用フィクスチャ: `tests/` (`src/tests/` でも可、プロジェクト判断)

### R-8: 完了の定義 (Definition of Done)

チケットを「完了」とする条件:

- [ ] 仕様(該当 `F-XXX` / `SC-XXX`)の **成功パス + 失敗パス** を実装
- [ ] 該当箇所のユニットテスト/結合テスト/E2E のうち、`docs/IMPLEMENTATION_GUIDE.md` §4 で `Must` 指定のものをカバー
- [ ] バリデーション規則(`docs/03_detailed_design/04_バリデーション規則.md`)に準拠
- [ ] エラー設計(`docs/03_detailed_design/05_エラー設計.md`)のエラーコードを返す
- [ ] 認可ロジックがロール × リソース × 関係(組織ツリー等)で検証されている
- [ ] 監査ログ対象操作(`docs/03_detailed_design/07_セキュリティ実装方針.md`)で記録される
- [ ] `lint` / `type-check` / 該当テスト全て green
- [ ] 仕様 ID コメントが入っている (R-2)
- [ ] `docs/_impl_state/tickets/T-XXX.md` の `status: done` + `evidence` セクションが埋まっている

---

## 2. セキュリティ・脆弱性の最低ライン (Security Baseline)

すべての実装エージェントが **コードを書くたびに自己チェック** すべき項目。詳細は `skills/security-review/SKILL.md` 参照。

### S-1: OWASP Top 10 一次防御

| カテゴリ | 必須対策 |
|---|---|
| A01 アクセス制御不備 | 認可は **API 層で** チェック。フロント側の UI 非表示だけに頼らない |
| A02 暗号化の不備 | パスワードは bcrypt/argon2、通信は TLS、Cookie は `HttpOnly` + `Secure` + `SameSite` |
| A03 インジェクション | SQL: パラメータ化必須、ORM 使用。LLM プロンプト: テンプレート + プレースホルダ、外部入力は escape |
| A04 安全でない設計 | 認証・認可・レート制限はミドルウェア集約。各エンドポイントの個別実装に依存しない |
| A05 セキュリティ設定ミス | デフォルト deny。CORS は明示許可のみ。エラーレスポンスでスタックトレースを露出しない |
| A06 脆弱な依存関係 | 新規依存追加時は `npm audit` / `pip-audit` 相当を回す。CVE 既知の脆弱性があるバージョンは使わない |
| A07 認証の不備 | セッション固定攻撃対策(ログイン後にセッションID再発行)、ブルートフォース対策(レート制限) |
| A08 ソフトウェア・データ整合性の不備 | 依存は lockfile で固定、CI で `--frozen-lockfile` |
| A09 ロギング・監視の不足 | 認証イベント・認可拒否・管理操作は監査ログ必須 |
| A10 SSRF | 外部 URL を叩く場合はホスト allowlist、内部 IP/メタデータエンドポイントへの接続を拒否 |

### S-2: 入力境界の防衛

- すべての HTTP 入力は **型 + 値域 + 形式** をスキーマで検証(Pydantic / Zod 等)
- ファイルアップロード: MIME 検証 + 拡張子検証 + サイズ上限 + 保存パスのサニタイズ
- リダイレクト先 URL: allowlist でホスト検証

### S-3: シークレット・PII 取扱い

- 環境変数経由で読み込み、コードに書かない (R-4)
- ログには PII 出力しない (R-5)
- LLM 送信前に PII マスキング、マッピング表は永続化しない(`docs/IMPLEMENTATION_GUIDE.md` §5.3)

### S-4: 依存・サプライチェーン

- 新規ライブラリ採用前に: メンテ状況 (最終リリース日) / GitHub stars / ライセンスを確認
- ライセンス: GPL / AGPL は事前確認、許可ない場合は採用しない
- `package-lock.json` / `poetry.lock` / `uv.lock` を必ずコミット

---

## 3. 保守性の最低ライン (Maintainability Baseline)

### M-1: 命名と構造

- ファイル名・関数名・変数名は **仕様に出てくる用語と一致** させる(`docs/01_requirements/05_用語集.md`)
- 1 ファイル 1 責務。500 行を超えたら分割を検討
- ディレクトリ構造は技術スタックの慣習に従う:
  - Next.js: `src/app/`, `src/components/`, `src/lib/`, `src/types/`
  - FastAPI: `src/api/`, `src/services/`, `src/models/`, `src/schemas/`, `src/db/`, `src/core/`

### M-2: テスト容易性

- 純粋関数を優先。副作用(DB/HTTP/時刻/乱数)は注入する
- 認可ロジック・バリデーション・ビジネスルールは関数として分離
- テストファイル名は `<対象ファイル名>.test.ts` / `test_<対象ファイル名>.py`

### M-3: ドキュメンテーション

- public API (公開関数・公開クラス) には docstring 必須
- 「なぜこうしたか」コメントを書く(`what` ではなく `why`)
- 直感に反する実装には `docs/IMPLEMENTATION_GUIDE.md` §5(既知の落とし穴)へのリンクを残す

### M-4: 型・lint

- TypeScript: `strict: true`, `noUncheckedIndexedAccess: true`
- Python: `mypy --strict` または `pyright`、`ruff` で lint
- CI で型・lint・テストが green でなければマージ不可

### M-5: 依存方向

- レイヤード(`api → services → models`)、外側から内側への単方向依存のみ
- 横断的関心事(ログ・認可・トランザクション)はデコレータ/ミドルウェアで集約

---

## 4. ハーネス: チケットと状態管理

### 4.1 チケットの実体

すべての実装は **チケット(T-XXX)** に紐づく。チケットは:

- `docs/_impl_state/tickets/T-XXX.md` ファイル
- TaskList 上の Task (TaskCreate で作成、blockedBy で依存表現)

両方を **対で** 持つ(ファイルで永続化、Task で進行管理)。

チケットのテンプレートは `${CLAUDE_PLUGIN_ROOT}/templates/_impl_ticket_template.md` 参照。最低限のフィールド:

```yaml
---
ticket_id: T-001
spec_refs: [F-009, SC-010]
type: backend | frontend | db | batch | test | infra | shared
title: <端的に何を作るか>
depends_on: [T-000]
touches_shared: false  # 共有設定ファイルを編集するか
estimated_files:
  - src/api/staffs.py
  - src/services/staff_query.py
owner: <agent名> | null
status: open | in_progress | review | done | blocked
---

## 仕様
仕様の該当箇所を引用 or 要約。リンクを必ず張る

## 完了条件
- [ ] ...
- [ ] テストが通る
- [ ] 監査ログ対象なら記録される

## 実装メモ
(エージェントが書き残す)

## 証拠 (Evidence)
完了時に書く。テスト結果・コマンド出力・該当コミットなど
```

### 4.2 状態ディレクトリ

```
docs/_impl_state/
├─ README.md                   # この階層の使い方
├─ tickets/                    # 個別チケット (T-XXX.md)
├─ progress.md                 # ダッシュボード(マイルストーン進捗)
├─ spec_gaps.md                # 仕様の欠落・矛盾の発見ログ
├─ incidents.md                # ルール違反・失敗・回復ログ
└─ review_findings.md          # security-reviewer / code-reviewer の指摘集約
```

### 4.3 並列実行プロトコル

1. **orchestrator** が `TaskList` を確認 → 自分が割当てる前に新規チケットを `TaskCreate` で起票
2. 依存関係は `addBlockedBy` で表現
3. 同時に走らせる実装エージェントを **1メッセージ内で複数 Agent ツール呼び出し** して並列起動
4. 各エージェントは:
   - 起動時に `TaskList` で自分の owner なし & blocked なしのチケットから先頭を `TaskUpdate` で `owner = self`, `status = in_progress` に claim
   - 作業中は他チケットを触らない
   - 完了時に `status = completed` + チケット MD の `status: done` を更新
5. shared ファイルを触るチケット(`touches_shared: true`)は orchestrator が **直列実行** する(他の並列タスクが完了してから)

---

## 5. フック (Claude Code hooks) との連携

hooks は2通りの方法で有効になります:

1. **プラグイン利用時（推奨）**: プラグインの `hooks/hooks.json` が自動で読み込まれ、インストールするだけで有効。
2. **手動配置時**: `.claude/hooks/` 配下にスクリプトをコピーし、`.claude/settings.json` で発火条件を設定（`hooks/settings.example.json` 参照）。

実装エージェントは **hooks が無くても自衛できる** ことを前提に動きますが、hooks があると違反が即時ブロックされて安心です。

設定済みフック(詳細は `hooks/README.md`):

| Hook | 発火タイミング | 役割 |
|---|---|---|
| `secret_guard.py` | PreToolUse(Write/Edit) | API キー等のハードコードをブロック |
| `docs_readonly_guard.py` | PreToolUse(Write/Edit) | `docs/` 配下への書き込みをブロック(`docs/_impl_state/` 除く) |
| `pii_check.py` | PreToolUse(Write/Edit) | 明らかな個人情報パターン(氏名フルネーム+電話番号など)を検出 |
| `spec_traceability_check.py` | PostToolUse(Write/Edit) | `src/` 配下の新規/変更ファイルに `@spec` タグが含まれているかチェック |
| `post_format.py` | PostToolUse(Write/Edit) | `*.ts`/`*.tsx`/`*.py` を保存後にフォーマッタにかける(ベストエフォート) |

---

## 6. 失敗パターン(やってはいけないこと)

- ❌ 「仕様にないが普通こうあるべきだから」と勝手に機能追加
- ❌ レビュー前にメインブランチへ push (実装エージェントは PR/コミットを切るが、マージ判断は人間)
- ❌ docs/ を直接編集して仕様を変える
- ❌ 同じファイルを別エージェントと並行編集してマージ衝突を起こす
- ❌ シークレットをファイルに書く / コメントに書く / コミットメッセージに書く
- ❌ ログに PII を出す / 例外メッセージにスタックトレースを露出させる
- ❌ テストを「後で書く」と言ってチケットを done にする
- ❌ `@spec` タグを付けずに新規ファイルを作る

---

## 6.5 モデル選定ガイド(エージェント frontmatter `model:` 値)

各エージェントの `.md` 冒頭フロントマターで指定する Claude モデルの **推奨値とその理由** は以下:

| エージェント | 推奨モデル | 理由 |
|---|---|---|
| `impl-orchestrator` | **opus** | 全体統括。仕様の解釈、チケット計画レビュー、各専門エージェントの完了報告評価、レビュー指摘の重大度判定と進行判断。誤判定の影響範囲が広いため最高 reasoning が必要 |
| `impl-security-reviewer` | **opus** | セキュリティの最終ゲート。OWASP/PII/認可/依存 CVE の脅威モデリングと重大度判定。BLOCKER 取り違えコストが極めて高い |
| `impl-code-reviewer` | **opus** | 仕様準拠の最終ゲート。API仕様/DDL/処理フロー × 実装の横断突き合わせと保守性判定 |
| `impl-ticket-planner` | sonnet | 仕様 → チケット分解の構造的・反復的作業。複雑判断は orchestrator にエスカレーション可能 |
| `impl-backend-engineer` | sonnet | コーディング作業。security/code reviewer が後段で品質保証 |
| `impl-frontend-engineer` | sonnet | UI 実装。信頼境界はサーバー側 |
| `impl-db-engineer` | sonnet | DDL は仕様の写経色強。後方互換パターンは skill 化済 |
| `impl-batch-engineer` | sonnet | 冪等性・部分失敗パターンは skill 化済 |
| `impl-test-engineer` | sonnet | テスト派生作業 |

**設計思想**:

- **ゲート役(orchestrator + 2 reviewer)を opus** に集約し、品質判断の解像度を最大化
- **実装役 6 体を sonnet** に固定し、並列実行時のコスト効率を確保
- 高度な判断は **常にエスカレーション経路**(engineer → orchestrator → reviewer)で opus に流れる構造
- LLM コスト試算の例: 1 マイルストーン約 30 チケットを並列実装する場合、engineer 群を sonnet にすることで opus 比 **約 60〜70% のトークンコスト削減**(目安)

**変更したい場合**:

- 高速・低コスト優先 → reviewer を sonnet に下げる(品質ゲートが弱まる、自己責任)
- 最高品質優先 → 全エージェントを opus に上げる(コストが 3〜4 倍に)
- 個別エージェントは `.md` のフロントマター `model:` を直接編集

## 7. このルールの更新

このファイル `references/IMPL_RULES.md` は **実装エージェント側の不変ルール** であり、頻繁に変えるものではない。
更新が必要な場合は:

1. `docs/_impl_state/incidents.md` に「なぜ変えたいか」を記録
2. PR でこのファイルを修正
3. 全実装エージェントの `.md` から参照しているため、変更は全員に波及することを意識する
