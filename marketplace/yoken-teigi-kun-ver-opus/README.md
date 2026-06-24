# yoken-teigi-kun-ver-opus（要件定義君 Opus版）v0.9.2

ITシステムの **構成精査 → 要件定義 → 基本設計 → 詳細設計 → 画面モック → コスト概算 → 開発向け実装ガイド → 実装** までを、ユーザーと対話しながら一気通貫で完成させる Claude Code プラグイン（サブエージェント群 + hooks + skills）です。

## 何ができるか

### 設計フェーズ

- **Phase 0**: ノーコード / SaaS / AIエージェント / スクラッチの中から最適方式を比較提案 → ユーザー承認ゲート。git 初期化・コミット作者確定・GitHub リモート作成もここで行う
- ジュニアエンジニアでも答えられる選択肢式の質問で、機能要件と非機能要件を抜け漏れなくヒアリング（質問はチャットに番号付きで提示、AskUserQuestion ツールは使わない）
- 基本設計・詳細設計まで自動生成（人間の確認ポイントは明示）
- 画面モックは HTML + Tailwind で作成し、ブラウザですぐ確認可能
- **Phase 5**: コスト概算を md + PDF で出力（3カテゴリ：開発・インフラ・外部API/LLM）
- 設計成果物は `docs/` フォルダ1つに集約し、実装エージェントが読む `IMPLEMENTATION_GUIDE.md` まで自動生成
- **各フェーズ完了時に spec-critic がアンチ視点で検品**（チェックリスト未達・上流との矛盾・ID 参照切れ・設計レベルの脆弱性）し、PASS / 条件付き PASS / 差し戻し を判定
- **セッションを跨いでも途中から再開できる**: orchestrator は起動時に状態ファイル（phase_status / tickets）から現在地を判定し、再開宣言をしてから続行
- **設計確定後の仕様変更は spec-change-manager の変更管理フロー**で処理（@spec 逆引きの影響分析 → CR-XXX 記録 → 上流から更新 → 再レビュー）

### 実装フェーズ

- `docs/` を **唯一の真実(Single Source of Truth)** として `src/` 配下にコードを生成
- 仕様駆動: 全ての実装は仕様 ID(F-XXX/EP-XXX/SC-XXX 等)に紐づく(`@spec` タグ強制)
- チケット駆動: 仕様を `docs/_impl_state/tickets/T-XXX.md` に分解し、依存関係を整理
- **並列実行**: 独立したチケットを backend/frontend/db/batch/test の専門エージェントで同時に進める
- マイルストーン末に **security-reviewer / code-reviewer** が横断レビュー
- Claude Code hooks による **安全弁**: シークレット混入・docs/ への書き込み・PII 露出・トレーサビリティ違反をブロック（プラグインインストールだけで自動有効）

## 全体フロー

```
[Phase 0] 構成精査 + 承認ゲート     ← spec-orchestrator が solution-architect 定義をインライン実行
            ↓ ユーザー承認
[Phase 1] 要件定義                  ← requirements-analyst
            ↓
[Phase 2] 基本設計                  ← basic-designer
            ↓
[Phase 3] 画面モック                ← ui-mock-designer（Phase 2 と並走可）
            ↓
[Phase 4] 詳細設計                  ← detailed-designer
            ↓
[Phase 5] コスト概算 (md+PDF)       ← spec-orchestrator が cost-estimator 定義をインライン実行
            ↓
[Phase 6] 実装ガイド                ← spec-handoff-writer
            ↓
（実装フェーズ）                    ← impl-orchestrator 配下のエージェント群
```

> **各フェーズの完了時に `spec-critic` がアンチレビュー**（不足・不整合・設計脆弱性の検品）を行い、BLOCKER があればフェーズを差し戻す。PASS するまで次フェーズに進まない。

> 💡 **インライン実行の設計**
> ユーザーへの対話的な質問はメインセッションでのインライン実行時のみ成立するため、対話頻度が極めて高い Phase 0/5 は spec-orchestrator が **該当エージェント定義を Read してインライン実行** します（エージェント定義が唯一のソース）。
> `solution-architect` と `cost-estimator` は **単独起動** もできます（「solution-architect 起動して」と言えば普通に動きます）。

## 構成

### 設計エージェント（10体）

| エージェント | 役割 | 主な出力 |
|---|---|---|
| `spec-orchestrator` | 全体統括。フェーズ管理 | `docs/_state/phase_status.md` |
| `solution-architect` | Phase 0 構成精査 + 承認ゲート + git 初期化 | `docs/00_solution/proposal.md`, `approved_option.md` |
| `requirements-analyst` | Phase 1 要件定義(機能+非機能) | `docs/01_requirements/` |
| `basic-designer` | Phase 2 基本設計(構成・画面・データ) | `docs/02_basic_design/` |
| `ui-mock-designer` | Phase 3 画面モック (HTML+Tailwind) | `docs/04_ui_mocks/` |
| `detailed-designer` | Phase 4 詳細設計(API・DDL・処理) | `docs/03_detailed_design/` |
| `cost-estimator` | Phase 5 コスト概算 (md+PDF) | `docs/05_cost_estimate/` |
| `spec-handoff-writer` | Phase 6 開発向け実装ガイド | `docs/IMPLEMENTATION_GUIDE.md` |
| `spec-critic` (**opus**) | **各フェーズ完了時のアンチレビューゲート**（不足・不整合・設計脆弱性の検品と差し戻し判定） | `docs/_state/phase_reviews/phase<N>_review.md` |
| `spec-change-manager` | **仕様変更の変更管理フロー**（影響分析 → CR 記録 → 上流から更新 → critic 再レビュー） | `docs/_state/change_requests.md` |

> spec-critic 以外の設計エージェントは sonnet。spec-critic はゲート役のため impl 側 reviewer と同じく opus（コスト重視なら frontmatter で sonnet に下げられる）。

### 実装エージェント（9体）

| エージェント | モデル | 役割 | 主な出力 |
|---|---|---|---|
| `impl-orchestrator` | **opus** | 全体統括。チケット起票・並列起動・レビュー集約 | `docs/_impl_state/progress.md` |
| `impl-ticket-planner` | sonnet | 仕様 → チケット分解(依存グラフ込み) | `docs/_impl_state/tickets/T-XXX.md` |
| `impl-backend-engineer` | sonnet | API / サービス層 / リポジトリ層 | `src/api/`, `src/services/` |
| `impl-frontend-engineer` | sonnet | ページ / コンポーネント / API クライアント | `src/app/`, `src/components/` |
| `impl-db-engineer` | sonnet | DDL / マイグレーション / ORM モデル | `src/db/` |
| `impl-batch-engineer` | sonnet | 定期/常駐ジョブ・冪等性・観測 | `src/batch/` |
| `impl-test-engineer` | sonnet | 単体/結合/E2E/負荷/CI | `tests/`, `.github/workflows/` |
| `impl-security-reviewer` | **opus** | OWASP / PII / 認可 / 依存脆弱性 監査 | `docs/_impl_state/review_findings.md` |
| `impl-code-reviewer` | **opus** | 仕様準拠・トレーサビリティ・保守性 | 同上 |

> 💡 モデル配分の設計: ゲート役 3 体(orchestrator + 2 reviewer)を opus に集約、実装役 6 体は sonnet。高度な判断は常にエスカレーション経路で opus に流れる構造。詳細は `references/IMPL_RULES.md §6.5`。

### 共通基盤

- `references/SPEC_RULES.md` — 設計エージェント共通の対話規約（番号付き質問・最大4問 等）
- `references/IMPL_RULES.md` — 実装エージェント共通の不変ルール（仕様駆動・トレーサビリティ・セキュリティ 等）
- `hooks/` — Claude Code hooks。`hooks/hooks.json` によりプラグインインストールだけで自動有効（シークレット/PII/docs read-only/@spec/フォーマット）
- `skills/requirements-architect/` — 使い方案内スキル
- `skills/security-review/` — OWASP セキュリティレビューのチェックリスト + 検出コマンド集
- `skills/spec-traceability/` — 仕様 ↔ 実装 双方向トレース手順
- `templates/` — 各種テンプレ（構成提案、コスト概算、チケット、進捗、spec_gaps、incidents、review_findings、_state 各種）

### 外部スキル依存（任意）

- `tool-selection-advisor` スキル — `solution-architect` が参照（ない環境でも単独で動く）
- `anthropic-skills:pdf` スキル — `cost-estimator` が PDF 生成で使用（ない環境では pandoc 等にフォールバック）

## セットアップ

### プラグインとして使う（推奨）

プラグインをインストールするだけで、エージェント・スキル・hooks が自動で有効になります。プロジェクト側の状態ファイルは各エージェントが必要時にテンプレートからコピーします。

### 手動コピーで使う

[`install.md`](install.md) を参照（`.claude/agents/` `.claude/references/` `.claude/hooks/` への配置手順）。

## 使い方

### 設計フェーズから始める

プロジェクトのルートで:

```
spec-orchestrator を起動して、新しいシステムの設計を始めて。
```

→ spec-orchestrator が Phase 0（構成精査 + git 初期化 + 承認ゲート）をインライン実行します。
→ ユーザー承認が取れた後に Phase 1 以降に進みます。
→ Phase 4 完了後、Phase 5（コスト概算 md+PDF）をインライン実行します。

### 設計済み(docs/ がある)で実装フェーズに入る

```
impl-orchestrator を起動して、docs/ の仕様に従って実装を始めて。
```

エージェントはチャットに番号付きで質問を提示し、ユーザーの返信を待ちます（AskUserQuestion ツールは使いません）。番号で選んで答えてください。

### 途中から再開する

セッションが切れても、orchestrator をもう一度起動するだけで `docs/_state/` / `docs/_impl_state/` から現在地を判定し、再開宣言をしてから続きを進めます。

```
spec-orchestrator を起動して、設計の続きから再開して。
impl-orchestrator を起動して、実装の続きから再開して。
```

### 仕様を変更したくなったら

確定済みの仕様を直接書き換えず、変更管理フローを通します:

```
spec-change-manager で「注文キャンセル機能を追加したい」の変更要求を処理して。
```

→ 影響分析（docs 横断 grep + 実装中なら @spec 逆引き）→ `CR-XXX` として記録 → ユーザー承認 → 上流から下流の順に docs 更新 → spec-critic 再レビュー → 実装中なら差分チケットの案内、まで一貫して行います。

## 成果物フォルダ構成(最終形)

```
docs/
├─ 00_README.md
├─ 00_solution/             # 構成精査・承認
│  ├─ proposal.md
│  └─ approved_option.md
├─ 01_requirements/         # 要件定義
├─ 02_basic_design/         # 基本設計
├─ 03_detailed_design/      # 詳細設計
├─ 04_ui_mocks/             # 画面モック
├─ 05_cost_estimate/        # コスト概算
│  ├─ cost_estimate.md
│  ├─ cost_estimate.pdf
│  └─ assumptions.md
├─ IMPLEMENTATION_GUIDE.md  # 実装エージェント向け
├─ _state/                  # 設計フェーズの Q&A ログ・未解決事項・進捗
│  ├─ change_requests.md    # 仕様変更の台帳（CR-XXX）
│  └─ phase_reviews/        # spec-critic のフェーズ別アンチレビュー結果
└─ _impl_state/             # 実装フェーズのチケット・進捗・レビュー指摘
   ├─ tickets/              # T-XXX.md チケット群
   ├─ progress.md           # ダッシュボード
   ├─ spec_gaps.md          # 仕様の欠落・矛盾ログ
   ├─ incidents.md          # ルール違反・失敗ログ
   └─ review_findings.md    # セキュリティ/コードレビュー指摘集約

src/                        # 実装エージェントの出力
tests/                      # テスト
```

## ルール(共通)

### 設計エージェント（詳細: `references/SPEC_RULES.md`）
- 質問はチャットに番号付きで提示してユーザーの返信を待つ(AskUserQuestion ツールは使わない)
- 1回4問まで、ジュニアにも答えられる言葉で
- **Phase 0 のユーザー承認が取れるまで Phase 1 以降には進まない**
- 機能要件と非機能要件の両方を必ず確定
- **Phase 5 のコスト概算は md と PDF を両方出力**
- 回答ログは `docs/_state/answers.md` に追記、未解決は `docs/_state/open_questions.md` にチケット化
- 成果物は必ず `docs/` 配下に

### 実装エージェント（詳細: `references/IMPL_RULES.md`）
- `docs/` 配下が **唯一の仕様**。実装は必ず仕様 ID に紐づく
- `docs/` は **読み取り専用**(書けるのは `docs/_impl_state/` のみ)
- シークレット・PII はコード/ログ/プロンプトに書かない
- 並列実行時は **同じファイルを別エージェントに触らせない**
- 全ファイルに `@spec` トレーサビリティタグを付与
- マイルストーン末にセキュリティ + コードレビューを必ず走らせる

## カスタマイズ

- 設計エージェント共通の対話規約を変えたい → `references/SPEC_RULES.md` を編集
- 実装エージェント共通の不変ルールを変えたい → `references/IMPL_RULES.md` を編集
- 構成方式の選択肢を変えたい → `agents/solution-architect.md` の「構成方式カタログ」を編集
- コスト見積もりの計算式を更新したい → `agents/cost-estimator.md` の Step 3 を編集
- 採用技術を絞り込みたい → `agents/basic-designer.md` の質問例セクションを編集
- モックを React で出力したい → `agents/ui-mock-designer.md` の出力テンプレートを差し替え
- 実装の出力先を変えたい → `references/IMPL_RULES.md` R-7 と `agents/impl-ticket-planner.md` の `estimated_files` 既定値を編集
- hook の検出パターンを調整したい → `hooks/*.py` を編集
- セキュリティチェックリストを増減 → `skills/security-review/SKILL.md` を編集

## 変更履歴

### v0.9.2
- **hooks を prompt ベースへ移行（Cowork 互換性修正）**: 旧 `hooks/hooks.json` は `python "${CLAUDE_PLUGIN_ROOT}/hooks/*.py"` の command 型だったが、Cowork のフックランナーが `${CLAUDE_PLUGIN_ROOT}` を展開せず未展開リテラルが相対パス化して全 hook が失敗していた。`secret_guard`/`docs_readonly_guard`/`pii_check`/`spec_traceability` を **1本の PreToolUse prompt フック（LLM 判定型）に統合**し、パス参照依存を排除。`post_format` は prompt 化不可のため plugin-native hooks からは除外（CLI 手動配置用の .py は残置）

### v0.9.1
- **Fable 提供終了に伴うモデル構成の見直し**: 最上位ゲート役 5 体（`spec-orchestrator` / `spec-critic` / `impl-orchestrator` / `impl-code-reviewer` / `impl-security-reviewer`）の frontmatter を `fable` から **`opus`** に変更し、Opus を最上位とする構成に統一。README のモデル表（opus 表記）と frontmatter の不整合も解消。エスカレーション経路は「高度な判断 → opus、実装作業 → sonnet」の 2 段構成

### v0.9.0
- **再開（レジューム）プロトコルを追加**: spec-orchestrator / impl-orchestrator が起動時に状態ファイル（`docs/_state/phase_status.md` / `docs/_impl_state/tickets/`）から現在地を自動判定し、「再開宣言」をしてから続行。中断チケットの owner クリア・差分起票ルールも明文化（SPEC_RULES Q-6 新設）
- **spec-change-manager（変更管理フロー）を新設**: 設計確定後・実装中の仕様変更を「影響分析（@spec 逆引き）→ CR-XXX 起票 → ユーザー承認 → 上流から更新 → spec-critic 再レビュー → 差分チケット案内」の正式フローで処理。台帳テンプレ `templates/_change_request_template.md` を追加。実装中は `.impl_active` ガードを一時退避して安全に docs を更新

### v0.8.0
- **spec-critic（アンチレビューゲート）を新設**: 各設計フェーズ（Phase 0〜6）の完了時に成果物を敵対的視点で検品する品質ゲートを追加。不足（チェックリスト未達・placeholder 残り）、不整合（上流ドキュメントとの矛盾・画面⇔機能⇔API⇔DDL のトレース欠落を Bash で機械検証）、設計レベルの脆弱性（認可設計漏れ・PII・OWASP 設計観点）をチェックし、BLOCKER があればフェーズを差し戻す。結果は `docs/_state/phase_reviews/` に記録（テンプレ: `templates/_phase_review_template.md`）

### v0.7.0（リファクタリング）
- **重複排除**: spec-orchestrator に丸ごと埋め込まれていた Phase 0/5 の手順を削除し、`agents/solution-architect.md` / `agents/cost-estimator.md` を唯一のソースとして「Read してインライン実行」する方式に統一
- **共通ルール集約**: 設計エージェント共通の対話規約を `references/SPEC_RULES.md` に新設。`IMPL_RULES.md` を `agents/` から `references/` へ移動（偽エージェント登録を解消）
- **hooks のプラグインネイティブ化**: `hooks/hooks.json` を追加し、インストールだけで自動有効に。`docs_readonly_guard` は実装フェーズマーカー（`docs/_impl_state/.impl_active`）がある時だけブロックするよう変更（設計フェーズの docs/ 書き込みを妨げない）
- **model 不整合の解消**: `impl-ticket-planner` / `impl-db-engineer` を IMPL_RULES §6.5 通り sonnet に、`spec-handoff-writer` を sonnet に統一
- **パス解決の修正**: エージェントが参照する共通ファイル・テンプレートを `${CLAUDE_PLUGIN_ROOT}` 基準に統一（プラグインインストール時に正しく解決される）
- **その他**: 画面IDを SC-XXX に統一、`skills/requirements-architect/references/` の完全重複コピーを削除、plugin.json の description を簡潔化、LLM 単価の記載を「見積もり時点で公式料金を確認」方式に変更

### v0.6.0
- AskUserQuestion 全廃（チャット番号付き質問化）・git 管理（Phase 0 でアカウント確定 + リモート作成）・docs/ と src/ の分離徹底

### v0.5.x
- Phase 0「構成精査 + 承認ゲート」、Phase 5「コスト概算」を新設。Phase 0/5 のインライン実行化

## ライセンス / メンテ

このエージェント群はあなたのプロジェクト用のテンプレートです。自由に編集・運用してください。
