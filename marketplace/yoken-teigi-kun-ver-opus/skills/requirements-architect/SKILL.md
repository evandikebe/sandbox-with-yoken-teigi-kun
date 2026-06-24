---
name: requirements-architect
description: |
  ITシステムの構成精査・要件定義・基本設計・詳細設計・画面モック・コスト概算・実装までを一気通貫で行うエージェント群の使い方を案内するスキル。
  ユーザーが「要件定義したい」「システムを設計したい」「spec-orchestrator を使いたい」「impl-orchestrator を起動したい」
  「設計エージェントを使いたい」「実装エージェントを使いたい」「要件定義君の使い方を教えて」「solution-architect を使いたい」
  「コスト概算を出したい」「仕様を変更したい」「要件が変わった」「設計の続きから再開したい」「実装の続きから再開したい」と発話したときに起動する。
  設計フェーズと実装フェーズのどちらから始めるか・再開か・仕様変更かを案内し、対応するエージェントを呼び出す手順を示す。
metadata:
  version: "0.9.0"
---

# yoken-teigi-kun（要件定義君）使い方ガイド

このプラグインは ITシステムの **構成精査 → 要件定義 → 基本設計 → 詳細設計 → 画面モック → コスト概算 → 実装** までを、ユーザーと対話しながら一気通貫で完成させるエージェント群です。

エージェント一覧・モデル配分・フォルダ構成などの詳細はプラグインの `README.md` を参照（このスキルは「どう始めるか」の案内に特化）。

## 全体フロー

```
[Phase 0] 構成精査 + 承認ゲート     ← spec-orchestrator がインライン実行（git 初期化もここ）
            ↓ ユーザー承認
[Phase 1] 要件定義                  ← requirements-analyst
[Phase 2] 基本設計                  ← basic-designer
[Phase 3] 画面モック                ← ui-mock-designer
[Phase 4] 詳細設計                  ← detailed-designer
[Phase 5] コスト概算 (md+PDF)       ← spec-orchestrator がインライン実行
[Phase 6] 実装ガイド                ← spec-handoff-writer
            ↓
[実装]                              ← impl-orchestrator 配下のエージェント群（並列実装 + レビュー）
```

> 各フェーズの完了時に **spec-critic** がアンチレビュー（不足・不整合・設計脆弱性の検品）を行い、BLOCKER があれば差し戻す。

## 使い方の判断

ユーザーの状況に応じて案内する:

| 状況 | 案内 |
|---|---|
| これからシステムを作りたい / 要件が固まっていない | **パターン1**（spec-orchestrator） |
| `docs/` 一式（IMPLEMENTATION_GUIDE.md 含む）が揃っている | **パターン2**（impl-orchestrator） |
| 特定の成果物だけ欲しい（モックだけ・コスト概算だけ 等） | **パターン3**（個別エージェント） |
| セッションが切れた / 途中から再開したい | **パターン4**（orchestrator を再起動 → 自動で再開判定） |
| 確定済みの仕様を変更したい / 要件が変わった | **パターン5**（spec-change-manager） |

### パターン1: 設計フェーズから始める（推奨）

プロジェクトのルートで:

```
spec-orchestrator を起動して、新しいシステムの設計を始めて。
```

spec-orchestrator は Phase 0（構成精査）をインライン実行する。最初にプロジェクトの git 初期化とコミット作者確定を行い、ノーコード/SaaS/AIエージェント/スクラッチの中から **2〜3案の比較表** を `docs/00_solution/proposal.md` に出力し、チャットに番号付きで質問して明示承認を取得する（AskUserQuestion ツールは使わない）。

承認後に Phase 1（要件定義）→ Phase 4（詳細設計）まで進み、Phase 5 でコスト概算（`docs/05_cost_estimate/cost_estimate.md` + `cost_estimate.pdf`）をインライン実行。最後に Phase 6 で `spec-handoff-writer` が `docs/IMPLEMENTATION_GUIDE.md` を仕上げる。

### パターン2: docs/ が揃っていて実装フェーズに入る

```
impl-orchestrator を起動して、docs/ の仕様に従って実装を始めて。
```

最初に並列度・マイルストーン・git方針を番号付き質問で確認後、チケット分解 → 並列実装 → セキュリティ/コードレビューが自動で走る。

### パターン3: 個別エージェントを直接呼ぶ

```
solution-architect で構成方式の比較だけしてほしい。
requirements-analyst で機能要件と非機能要件だけ詰めて。
ui-mock-designer でログイン画面とダッシュボードのモックだけ作って。
cost-estimator で現状の docs/ からコスト概算 PDF を作って。
impl-security-reviewer で src/ の現状をレビューして。
impl-code-reviewer で M1 の仕様準拠チェックだけして。
spec-critic で Phase 2 の成果物をアンチレビューして。
```

### パターン4: 途中から再開する

```
spec-orchestrator を起動して、設計の続きから再開して。
impl-orchestrator を起動して、実装の続きから再開して。
```

orchestrator が状態ファイル（`docs/_state/phase_status.md` / `docs/_impl_state/tickets/`）から現在地を判定し、「どこまで完了・次に何をするか」の再開宣言をしてから続行する。

### パターン5: 仕様を変更する

```
spec-change-manager で「<変更内容>」の変更要求を処理して。
```

影響分析（@spec 逆引き含む）→ CR-XXX 記録 → ユーザー承認 → 上流から docs 更新 → spec-critic 再レビュー → 実装中なら差分チケット案内、の正式フローで処理する。確定済み docs の直接書き換えはしない。

## 不変ルール（要点）

### 設計フェーズ（詳細: `${CLAUDE_PLUGIN_ROOT}/references/SPEC_RULES.md`）

1. **Phase 0 のユーザー承認が取れるまで Phase 1 以降に進まない**（`docs/_state/phase_status.md` の Phase 0 が「✅ 承認済み」になるまでゲートで止まる）
2. **Phase 5 でコスト概算 md と PDF を必ず両方出す**
3. **ドキュメントは全部 `docs/` 配下に集約**（コードは `src/`、厳密分離）
4. **質問はチャットに番号付きで提示してユーザーの返信を待つ（AskUserQuestion ツールは使わない）**
5. **1回最大4問・ジュニアエンジニアにも答えられる言葉で**

### 実装フェーズ（詳細: `${CLAUDE_PLUGIN_ROOT}/references/IMPL_RULES.md`）

- `docs/` 配下が **唯一の仕様**。実装は必ず仕様 ID（F-XXX/EP-XXX/SC-XXX 等）に紐づく
- 全実装ファイルに `@spec` トレーサビリティタグを付与
- 並列実行時は同じファイルを別エージェントに触らせない
- マイルストーン末にセキュリティ + コードレビューを必ず走らせる

## セットアップ補足

プラグインとしてインストール済みなら追加作業は不要（hooks も自動有効）。プロジェクト側の状態ファイル（`docs/_state/` 等）は各エージェントが必要時に `${CLAUDE_PLUGIN_ROOT}/templates/` からコピーして作成する。手動配置の手順はプラグインの `install.md` を参照。
