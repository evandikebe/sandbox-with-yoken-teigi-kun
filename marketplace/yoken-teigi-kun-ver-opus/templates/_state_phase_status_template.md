# フェーズ進捗

最終更新: <YYYY-MM-DD HH:MM>

> 各フェーズの完了には spec-critic のアンチレビュー判定の記録が必要（例: `critic: PASS (YYYY-MM-DD)` / 詳細は docs/_state/phase_reviews/）。

## Phase 0: 構成精査 + 承認ゲート (solution-architect)  ← **最初に必ず実施**
- [ ] solution-architect 起動
- [ ] ヒアリング完了（A要望/B環境/C制約/D将来像）
- [ ] docs/00_solution/proposal.md 作成（最低2案の比較）
- [ ] ユーザーへの比較表提示
- [ ] **ユーザー承認取得（チャットでの番号付き質問に対し明示的に「進めてください」の返信を得る）**
- [ ] docs/00_solution/approved_option.md 作成
- 承認状態：⬜ 未承認 / ⬜ ✅ 承認済み（承認日: ____ / 採用方式: ____）
- ⚠️ **承認済みになるまで Phase 1 以降には進まない**

## Phase 1: 要件定義 (requirements-analyst)
- [ ] 背景・目的
- [ ] ステークホルダー・ユーザー像
- [ ] 機能要件（MoSCoW 分類済み）
- [ ] 非機能要件 (8カテゴリ全て)
- [ ] 用語集
- [ ] スコープ外
- [ ] Phase 0 採用方式と整合
- [ ] ユーザー承認

## Phase 2: 基本設計 (basic-designer)
- [ ] システム全体構成
- [ ] 技術スタック（採用理由つき / Phase 0 採用方式と整合）
- [ ] 画面一覧
- [ ] 画面遷移図
- [ ] データモデル（ER図）
- [ ] 外部IF
- [ ] 権限と認証

## Phase 3: 画面モック (ui-mock-designer)
- [ ] デザイントーン確定（ユーザー承認）
- [ ] デザイントークン (design_notes.md)
- [ ] tokens.html サンプル
- [ ] 主要画面モック
- [ ] サブ画面モック
- [ ] index.html
- [ ] 各画面に通常/空/エラー/ロード状態
- [ ] 最終ユーザー承認

## Phase 4: 詳細設計 (detailed-designer)
- [ ] API 仕様（全エンドポイント）
- [ ] DB スキーマ（全テーブルDDL）
- [ ] 処理フロー
- [ ] バリデーション規則
- [ ] エラー設計（コード一覧）
- [ ] バッチ・常駐処理
- [ ] セキュリティ実装方針

## Phase 5: コスト概算 (cost-estimator)
- [ ] 入力ドキュメントの読み込み（00_solution / 01_requirements / 02_basic_design / 03_detailed_design）
- [ ] 前提条件のユーザー確認（人月単価・運用期間・インフラ方針・LLMボリューム）
- [ ] docs/05_cost_estimate/assumptions.md 作成
- [ ] docs/05_cost_estimate/cost_estimate.md 作成（3カテゴリすべて埋まる）
- [ ] docs/05_cost_estimate/cost_estimate.pdf 生成（pdf スキル経由）
- [ ] 初期費用 / 月額ランニングがレンジで明記されている

## Phase 6: 開発向け実装ガイド (spec-handoff-writer)
- [ ] docs/IMPLEMENTATION_GUIDE.md 生成
- [ ] docs/00_README.md 生成
- [ ] open_questions.md に未解決ゼロ（または「実装中に決める」明示）
- [ ] Phase 5 コスト概算へのリンクを含む

## 全体完了
- [ ] ユーザー最終承認
