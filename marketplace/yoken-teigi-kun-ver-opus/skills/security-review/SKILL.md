---
name: security-review
description: 実装済みコードに対する OWASP Top 10 + PII + 認可 + シークレット + 依存脆弱性の体系的レビュー手順とチェックリスト。impl-security-reviewer エージェントが起動時に読む想定。grep ベースの簡易検出と仕様準拠チェックの両輪で動く。
---

# security-review skill

`impl-security-reviewer` エージェントが実装コードをレビューする際の **チェックリスト** と **検出スクリプト集** です。
他プロジェクトでも流用可能。

---

## 1. レビューフレーム

```
[A] 認証・認可     [B] 入力検証   [C] インジェクション
[D] シークレット   [E] PII         [F] ロギング・監査
[G] 通信・暗号化   [H] レート制限  [I] 依存ライブラリ
[J] プロジェクト固有 (docs/03_detailed_design/07_セキュリティ実装方針.md)
```

各カテゴリで **BLOCKER / MAJOR / MINOR / INFO** の重大度を判定。

---

## 2. カテゴリ別チェックリスト

### A. 認証・認可

```yaml
- check: 認証ミドルウェアが全保護エンドポイントで動作
  how:   "ルート定義一覧と認証 decorator/middleware の対応を grep で確認"
  block: 漏れがある

- check: 認可判定が API/サービス層に存在
  how:   "フロントの非表示制御だけで終わってないか"
  block: あり

- check: 組織ツリー・親子関係を含む認可
  how:   "再帰CTE or 関係テーブル経由で都度計算しているか(静的キャッシュ禁止)"
  block: 静的キャッシュしている

- check: セッション固定攻撃対策
  how:   "ログイン成功時にセッションID再発行 (session_regenerate / new_session)"
  block: 無い

- check: パスワード保存
  how:   "bcrypt / argon2 を使用、salt はライブラリ任せ"
  block: MD5/SHA1/平文/独自ハッシュ
```

### B. 入力検証

```yaml
- check: 全 HTTP 入力がスキーマ検証
  how:   "Pydantic / Zod の使用率"
  block: 検証なしで body を直接使う箇所がある

- check: ファイルアップロード
  how:   "MIME + 拡張子 + サイズ + パスサニタイズ"
  block: パストラバーサル可能 / サイズ無制限

- check: リダイレクト先 URL
  how:   "allowlist の有無"
  block: 任意 URL に遷移可能(オープンリダイレクト)

- check: CSV/Excel エクスポートの数式インジェクション
  how:   "= + - @ で始まるセル値のエスケープ(' プレフィックス)"
  major: 対策なし
```

### C. インジェクション

```yaml
- check: SQL パラメータ化
  how:   "grep で 'execute' + f-string / 'execute' + + 連結 を探す"
  block: 文字列連結 SQL の存在

- check: HTML 出力
  how:   "dangerouslySetInnerHTML / v-html / |raw / Markup() の使用箇所"
  block: 検証なしで使っている

- check: LLM プロンプトインジェクション対策
  how:   "外部入力をテンプレ変数に渡しているか、role 明示しているか"
  major: 対策なし
```

### D. シークレット

```yaml
- check: ハードコードされたシークレット
  how:   |
    grep -rEn "(API_KEY|SECRET|TOKEN|PASSWORD)\s*=\s*['\"][^'\"]{8,}" src/ tests/
    また secret_guard.py の検出パターンを参考に
  block: 検出あり

- check: .env / .env.local が .gitignore
  how:   "cat .gitignore | grep -E '^\\.env$'"
  block: 含まれていない

- check: コミット履歴にシークレット残存
  how:   "git log -p | grep -E '(API_KEY|SECRET).*=.*[A-Za-z0-9]{20,}'  (重い場合は scan tool)"
  block: あり(履歴削除と鍵ローテーション必要)
```

### E. PII

```yaml
- check: ログに PII を出さない
  how:   "logger.info / log のフォーマット文字列に氏名/メール/電話 が入ってないか"
  block: 検出あり

- check: LLM 送信前マスキング
  how:   "LLM クライアント呼び出し直前で mask_pii() などのフックを通す"
  block: 通していない or テストでマスキング検証なし

- check: マスキング・マッピング表が永続化されていない
  how:   "DB テーブル / ファイル / Redis に保存していないか"
  block: 永続化している

- check: 例外メッセージ・スタックトレースが本番でクライアントに返らない
  how:   "エラーハンドラの本番設定"
  major: 露出している
```

### F. ロギング・監査

```yaml
- check: 認証イベント(ログイン/失敗/ログアウト)を監査ログに記録
  major: 記録なし

- check: 認可拒否(403)を監査ログに記録
  major: 記録なし

- check: 管理操作(ユーザー/権限/設定変更)を監査ログに記録
  block: 記録なし

- check: 監査ログ自体が改ざんされにくい
  how:   "append-only / 別 DB / 暗号化バックアップ"
  major: 同一 DB + 編集可能
```

### G. 通信・暗号化

```yaml
- check: HSTS / Secure / HttpOnly / SameSite Cookie
  block: クッキー設定に不足

- check: CORS が allowlist
  how:   "Access-Control-Allow-Origin が * になってないか(認証付き API では特に)"
  block: * 設定

- check: TLS 必須
  how:   "プロキシ/ELB 設定確認"
  major: HTTP 受け付け
```

### H. レート制限

```yaml
- check: ログイン試行レート制限
  major: なし

- check: パスワードリセット濫用対策
  major: なし

- check: 高コスト処理(LLM/エクスポート)の制限
  minor: なし
```

### I. 依存ライブラリ

```yaml
- check: pip-audit / npm audit 通過
  how: |
    pip install pip-audit && pip-audit --strict
    npm audit --audit-level=high
  block: HIGH 以上の脆弱性検出

- check: ライセンス
  how:   "GPL/AGPL の混入なし"
  major: あり(法務確認必要)

- check: lockfile コミット
  block: package-lock.json / poetry.lock / uv.lock がない
```

### J. プロジェクト固有

`docs/03_detailed_design/07_セキュリティ実装方針.md` を読み、書かれている対策が全て実装されているかチェック。`docs/IMPLEMENTATION_GUIDE.md` §5(既知の落とし穴)も確認。

---

## 3. 検出スクリプト集

### 3.1 シークレット静的検出

```bash
# 単純パターン
grep -rEn "(API_KEY|SECRET|TOKEN|PASSWORD|PASSWD)\s*[:=]\s*['\"][^'\"]{8,}" src/ tests/ \
  --include='*.py' --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' \
  --include='*.json' --include='*.yaml' --include='*.yml'

# 高エントロピー文字列(40文字以上の連続英数)
grep -rEn "[A-Za-z0-9+/]{40,}" src/ tests/ \
  --include='*.py' --include='*.ts' --include='*.tsx' | head -50

# AWS Access Key
grep -rEn "AKIA[0-9A-Z]{16}" src/ tests/

# PEM 秘密鍵
grep -rEn "BEGIN (RSA|EC|OPENSSH|DSA|) ?PRIVATE KEY" .
```

### 3.2 SQL インジェクション疑い

```bash
# Python: f-string / format で execute
grep -rEn "execute\s*\(\s*f['\"]" src/
grep -rEn "execute\s*\(\s*['\"].*\{" src/
grep -rEn "execute\s*\(\s*['\"][^'\"]*['\"]\s*\+\s*" src/

# TypeScript: raw query 連結
grep -rEn "query\s*\(\s*`[^`]*\$\{" src/
```

### 3.3 PII ログ出力疑い

```bash
# Python
grep -rEn "(logger|log)\.(info|debug|warning|error|exception)\s*\(.*name|email|phone|address" src/
# TypeScript
grep -rEn "console\.(log|info|warn|error)\s*\(.*name|email|phone" src/
```

### 3.4 認可漏れ(デコレータ未使用)疑い

```bash
# FastAPI ルート定義の認可デコレータ確認
grep -rB2 -E "@(app|router)\.(get|post|put|delete|patch)" src/api/ \
  | grep -E "@(require_role|require_auth|Depends.*current_user)" -B5 | head -30
```

### 3.5 依存スキャン

```bash
# Python
pip install pip-audit && pip-audit -r requirements.txt --strict
# or
poetry export -f requirements.txt | pip-audit -r /dev/stdin

# Node
npm audit --audit-level=high
# or
npx better-npm-audit audit --level high
```

### 3.6 dangerous HTML / eval

```bash
grep -rEn "dangerouslySetInnerHTML|v-html|\|\s*safe|\beval\s*\(|new Function\s*\(" src/
```

---

## 4. 重大度判定の指針

- **BLOCKER**: 既知の脆弱性 / 認可漏れ / シークレット混入 / PII 漏洩 / 管理操作の監査ログ未記録
- **MAJOR**: OWASP 対策の欠落 / 一般的監査ログ未記録 / 入力検証欠落 / CORS *
- **MINOR**: 設定の改善余地 / 軽微 CVE / ロギング改善
- **INFO**: 観察事項 / 提案

判断に迷ったら **「実害シナリオを書けるか」** をチェック:
- 書ける → MAJOR 以上
- 書きにくい → MINOR or INFO

---

## 5. 報告フォーマット

`docs/_impl_state/review_findings.md` への追記形式:

```markdown
## Security Review: YYYY-MM-DD (スコープ: M1)

### Findings サマリ
- BLOCKER: 1
- MAJOR: 3
- MINOR: 5
- INFO: 8

---

### F-YYYY-MM-DD-001 [BLOCKER] <一行サマリ>
- ファイル: src/path/to/file.py:NN
- 問題: <事実ベースで何が問題か>
- リスク: <実害シナリオ>
- 仕様: <該当する仕様 ID or 設計書のセクション>
- 推奨修正: <具体的に>
- 担当チケット: T-XXX → 修正チケット T-XXX-fix-001 を起票

### F-YYYY-MM-DD-002 [MAJOR] ...
```

---

## 6. レビューを終えるための条件

- [ ] チェックリスト 10 カテゴリすべてに目を通した
- [ ] 検出スクリプトを最低限実行した(3.1〜3.6)
- [ ] プロジェクト固有(`07_セキュリティ実装方針.md`)を逐一突き合わせた
- [ ] BLOCKER 全てに修正チケットを起票した
- [ ] `review_findings.md` に記録した
