# Claude Code Hooks — 実装エージェント用安全弁

このディレクトリは `agents/impl-*.md` の実装エージェント群が動作する際の **強制レイヤー** です。Claude Code が `Write` / `Edit` などのツールを使う直前/直後にスクリプトを実行して、ルール違反をブロックしたり後処理したりします。

## ファイル一覧

| ファイル | 役割 |
|---|---|
| `hooks.json` | **プラグイン用の hook 設定（prompt ベース）**。インストールするだけで自動有効。LLM 判定型なので `${CLAUDE_PLUGIN_ROOT}` 等のパス参照に依存せず、Cowork でもそのまま動く |
| `settings.example.json` | 手動配置用。`.claude/settings.json` の雛形 |
| `secret_guard.py` | PreToolUse(Write/Edit): API キー・トークンらしい値のコミットをブロック |
| `docs_readonly_guard.py` | PreToolUse(Write/Edit): `docs/` 配下への書き込みをブロック(`docs/_impl_state/` は許可)。**`docs/_impl_state/.impl_active` マーカーがある時=実装フェーズ中のみ有効**（設計フェーズの docs/ 書き込みは妨げない） |
| `pii_check.py` | PreToolUse(Write/Edit): 明らかな個人情報パターンを検出して警告 |
| `spec_traceability_check.py` | PostToolUse(Write/Edit): `src/` 配下の新規/変更ファイルに `@spec` タグが入っているか検証 |
| `post_format.py` | PostToolUse(Write/Edit): `*.ts/*.tsx/*.py` を保存後にフォーマッタにかける(ベストエフォート) |

## 導入手順

### プラグイン利用時（推奨）

何もしなくてよい。`hooks/hooks.json` が自動で読み込まれる。

### 手動配置時

```bash
# プロジェクトルートで(Linux/Mac)
mkdir -p .claude/hooks
cp hooks/*.py .claude/hooks/
cp hooks/settings.example.json .claude/settings.json

# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path .claude/hooks | Out-Null
Copy-Item hooks/*.py .claude/hooks/
Copy-Item hooks/settings.example.json .claude/settings.json
```

> ℹ️ Python 3.10+ が必要。hooks は `python` コマンドを呼びます。Windows は通常 `python`、Linux/Mac で `python` が無い場合は `python3` に置換してください（手動配置時は `settings.json` を編集）。

Claude Code を再起動すると hooks が有効になります。


## prompt ベース hook について（v0.9.2〜）

`hooks/hooks.json` は **prompt ベース（LLM 判定型）の PreToolUse フック1本** に統合した。`secret_guard` / `docs_readonly_guard` / `pii_check` / `spec_traceability_check` の4つの判定を1つのプロンプトにまとめ、`Write`/`Edit`/`MultiEdit` の直前に LLM が内容を検査してブロック(シークレット混入・docs/ 直接編集)または警告(PII・@spec 欠落)する。

**なぜ command 型をやめたか**: 旧版は `python "${CLAUDE_PLUGIN_ROOT}/hooks/xxx.py"` 形式だったが、Cowork のフックランナーは `${CLAUDE_PLUGIN_ROOT}` を展開しないため、未展開リテラルが相対パス扱いになり全 hook が失敗していた。prompt ベースはスクリプトのパス参照が不要なのでこの問題が原理的に発生しない。

**トレードオフ**: prompt フックは `Write`/`Edit` のたびに LLM 評価が1回走るため、command 型より僅かに遅くコストがかかる。また prompt フックは `PreToolUse` のみ対応のため、`post_format`(保存後フォーマット)は hooks.json から外した。

**.py スクリプトと settings.example.json は残置**: Claude Code(CLI) で手動配置する場合は従来どおり command 型(.py)が使える。その場合は下記『手動配置時』の手順を使う（CLI では `${CLAUDE_PLUGIN_ROOT}` も正しく展開される）。

## 動作の調整

- **docs/ ガードの有効/無効**: `docs/_impl_state/.impl_active` マーカーで切替（impl-orchestrator が Phase A で作成。設計フェーズに戻るなら削除）。環境変数 `IMPL_DOCS_GUARD=1` で強制有効化も可
- **PII 警告の誤検出が多い場合**: `pii_check.py` の検出パターン（`JP_PHONE` / `JP_NAME` 等）を編集
- **PII 検出をブロックに強める**: 環境変数 `IMPL_PII_STRICT=1`
- **`@spec` タグ警告をブロックに強める**: 環境変数 `IMPL_STRICT_TRACEABILITY=1`（デフォルトは警告のみ）
- **フォーマッタ未導入で `post_format.py` が失敗する場合**: そのまま放置でよい（フォーマッタが見つからなければ何もせず終了する）

## ブロック vs 警告

各 hook は終了コードで挙動を切り替えます:

| 終了コード | 意味 |
|---|---|
| `0` | OK(処理続行) |
| `1` | 警告のみ(stderr に表示、処理続行) |
| `2` | **ブロック**(Claude にエラー伝達、ツール呼び出し中止) |

## hook 入力形式 (参考)

Claude Code は hook プロセスに JSON を stdin で渡します。例(PreToolUse):

```json
{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/abs/path/to/file.py",
    "content": "..."
  },
  "session_id": "...",
  "cwd": "/path/to/project"
}
```

各 hook はこの JSON を読んで判断します。

## トラブルシュート

- **`python3` が見つからない (Windows)**:
  - `settings.json` のコマンドを `python` に変更
  - または `py -3` を使う
- **hook が動かない**:
  - `.claude/settings.json` の場所がプロジェクトルート直下になっているか確認
  - Claude Code を `--debug` 付きで起動し、hook 実行ログを確認
- **PowerShell 実行ポリシー**:
  - スクリプト実行が拒否される場合: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## 安全弁としての位置づけ

- hooks があれば事故率は下がるが、**エージェント側の規律が一次防壁**
- hooks を切られても問題が起きないように、エージェントの `.md` で同じルール(`agents/IMPL_RULES.md`)を全員に読ませている
- hooks は **二次防壁**。両方を維持することで多層防御
