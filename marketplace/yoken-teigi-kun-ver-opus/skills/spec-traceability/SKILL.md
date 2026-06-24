---
name: spec-traceability
description: 仕様 ID (F-XXX/EP-XXX/SC-XXX/BT-XXX/NF-XXX/IF-XXX) と実装コードを双方向に追跡する手順とコマンド集。@spec タグ規約・抽出方法・突き合わせ・ギャップ検出を含む。impl-code-reviewer エージェントが起動時に読む想定。
---

# spec-traceability skill

仕様と実装の **双方向トレーサビリティ** を確保するための手順とツール集。

---

## 1. なぜトレーサビリティか

- レビュー時に「この実装、どの仕様に対応?」を即答できる
- 仕様変更時に「影響を受ける実装ファイル一覧」を機械的に出せる
- 仕様にあるのに実装されていない / 実装にあるが仕様にない、を検出できる
- セキュリティ・コンプライアンス監査で必須

---

## 2. `@spec` タグ規約

### 2.1 形式

```
@spec <ID>[, <ID>...] — <短い説明>
```

- ID 形式: 大文字英字 1〜3 文字 + ハイフン + 数字 (例: `F-014`, `EP-042`, `SC-110`, `BT-001`, `NF-016`, `IF-003`)
- 複数 ID はカンマ区切り
- 説明は任意(あったほうがレビューしやすい)

### 2.2 配置場所

| 言語 | 配置 | 例 |
|---|---|---|
| Python | モジュール docstring または関数 docstring | `"""@spec F-014 — フォローコメント記録"""` |
| TypeScript / JavaScript | ファイル先頭の JSDoc または関数の JSDoc | `/** @spec EP-042 */` |
| Vue / Svelte | `<script>` ブロック内の先頭コメント | `// @spec SC-032` |
| SQL (migration) | ファイル先頭のコメント | `-- @spec DB:comment テーブル` |

### 2.3 粒度

- **ファイル単位** が基本(モジュールの目的に対応する仕様 ID)
- **関数単位** でも書ける(API ルートやサービス関数など、エンドポイントと 1:1 対応するもの)
- 同じ仕様 ID を複数箇所に書いて構わない(縦串で検索できる)

---

## 3. 抽出コマンド集

### 3.1 仕様 ID の全集合(docs/ から)

```bash
# 全仕様 ID を集める
grep -rEoh "\b[A-Z]{1,3}-[0-9]{2,4}\b" docs/ \
  | sort -u > /tmp/spec_ids.txt

# 種別ごとに分割
grep -E "^F-"   /tmp/spec_ids.txt > /tmp/spec_F.txt
grep -E "^EP-"  /tmp/spec_ids.txt > /tmp/spec_EP.txt
grep -E "^SC-"  /tmp/spec_ids.txt > /tmp/spec_SC.txt
grep -E "^BT-"  /tmp/spec_ids.txt > /tmp/spec_BT.txt
grep -E "^NF-"  /tmp/spec_ids.txt > /tmp/spec_NF.txt
grep -E "^IF-"  /tmp/spec_ids.txt > /tmp/spec_IF.txt
```

### 3.2 実装 ID の全集合(src/ tests/ から)

```bash
# @spec タグ近傍の ID を取る
grep -rEoh "@spec[^\n]{0,200}" src/ tests/ \
  | grep -oE "\b[A-Z]{1,3}-[0-9]{2,4}\b" \
  | sort -u > /tmp/impl_ids.txt
```

### 3.3 ギャップ検出

```bash
# 仕様にあるが実装にない (= 未実装 or タグ漏れ)
comm -23 /tmp/spec_ids.txt /tmp/impl_ids.txt > /tmp/missing_impl.txt
echo "未実装/タグ漏れ:"; cat /tmp/missing_impl.txt

# 実装にあるが仕様にない (= 仕様外実装 or タイポ ID)
comm -13 /tmp/spec_ids.txt /tmp/impl_ids.txt > /tmp/unknown_in_impl.txt
echo "仕様外実装/タイポ:"; cat /tmp/unknown_in_impl.txt
```

### 3.4 特定 ID から実装ファイルを引く

```bash
# F-014 を実装しているファイル
grep -rln "F-014" src/ tests/

# 仕様の該当箇所を引く
grep -rln "F-014" docs/
```

### 3.5 トレース表生成 (Markdown)

```bash
python - <<'PY'
import re, glob
from collections import defaultdict

spec = defaultdict(list)  # id -> [(file, line)]
impl = defaultdict(list)

# docs/ の仕様 ID
for f in glob.glob("docs/**/*.md", recursive=True):
    for i, line in enumerate(open(f, encoding="utf-8"), 1):
        for m in re.finditer(r"\b[A-Z]{1,3}-\d{2,4}\b", line):
            spec[m.group(0)].append((f, i))

# src/ + tests/ の @spec
for pat in ("src/**/*", "tests/**/*"):
    for f in glob.glob(pat, recursive=True):
        if not f.endswith((".py", ".ts", ".tsx", ".js", ".jsx")): continue
        try:
            text = open(f, encoding="utf-8").read()
        except Exception: continue
        for m in re.finditer(r"@spec[^\n]{0,200}", text):
            for sm in re.finditer(r"\b[A-Z]{1,3}-\d{2,4}\b", m.group(0)):
                impl[sm.group(0)].append(f)

ids = sorted(set(spec) | set(impl))
print("| 仕様 ID | 仕様 (代表) | 実装ファイル | 状態 |")
print("|---|---|---|---|")
for i in ids:
    src = spec[i][0] if spec[i] else "—"
    imp = ", ".join(sorted(set(impl[i]))) or "—"
    st = "OK" if spec[i] and impl[i] else ("仕様のみ" if spec[i] else "実装のみ")
    print(f"| {i} | {src} | {imp} | {st} |")
PY > docs/_impl_state/traceability_matrix.md
```

---

## 4. レビュー時の使い方

### 4.1 PR レビュー or マイルストーン末

1. 上記 3.1〜3.3 を実行
2. `missing_impl.txt` (仕様あり実装なし) の各 ID について:
   - その仕様が「未実装(チケット未消化)」なのか「タグ漏れ」なのかを判断
   - 未実装なら orchestrator に進捗確認
   - タグ漏れなら code-reviewer が修正チケット起票
3. `unknown_in_impl.txt` (実装あり仕様なし) の各 ID について:
   - タイポなら修正
   - 古い ID なら更新
   - 仕様外実装なら `spec_gaps.md` に追記

### 4.2 仕様変更時

1. 変更された仕様 ID をリストアップ
2. 各 ID で `grep -rln "<ID>" src/ tests/` を実行
3. 影響ファイル一覧を変更チケットに添付

---

## 5. CI への組み込み(推奨)

`.github/workflows/ci.yml` に以下のジョブを追加すると、PR 時にトレーサビリティ違反を自動検出できる:

```yaml
  traceability:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check spec traceability
        run: |
          # 全 @spec タグの ID を抽出
          grep -rEoh "@spec[^\\n]{0,200}" src/ tests/ \
            | grep -oE "\\b[A-Z]{1,3}-[0-9]{2,4}\\b" \
            | sort -u > /tmp/impl_ids.txt
          # 仕様 ID を抽出
          grep -rEoh "\\b[A-Z]{1,3}-[0-9]{2,4}\\b" docs/ \
            | sort -u > /tmp/spec_ids.txt
          # 実装にあって仕様にない ID を検出
          unknown=$(comm -13 /tmp/spec_ids.txt /tmp/impl_ids.txt)
          if [ -n "$unknown" ]; then
            echo "::error::仕様にない @spec ID が実装に含まれています:"
            echo "$unknown"
            exit 1
          fi
```

---

## 6. 失敗例(よくあるアンチパターン)

- ❌ コミット直前にまとめて `@spec` を貼る → 抽象的になりがち、レビュー価値低
- ❌ 「@spec F-014」を全ファイルにとりあえず貼る → 意味のないトレース
- ❌ ID を勝手に作る(例: `XYZ-001`) → 仕様にない ID が増殖
- ❌ ファイルごとに 10 個も ID を並べる → ファイル分割を検討すべきサイン
