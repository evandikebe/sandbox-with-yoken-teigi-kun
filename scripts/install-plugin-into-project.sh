#!/usr/bin/env bash
# =============================================================================
# 方式B フォールバック:
#   settings.json のプラグイン自動有効化が効かない場合に、対象プロジェクトの
#   .claude/ へ agents・references・hooks・skills を直接配置する。
#   （install.md の「方法B」をコンテナ用に自動化したもの）
#
# 使い方:  install-plugin-into-project.sh [対象プロジェクトのパス(既定:カレント)]
# =============================================================================
set -euo pipefail

SRC="/opt/yoken-marketplace/yoken-teigi-kun-ver-opus"
DST="${1:-$PWD}"

echo "[install] src=$SRC"
echo "[install] dst=$DST"

mkdir -p "$DST/.claude/agents" "$DST/.claude/references" "$DST/.claude/hooks"
cp "$SRC"/agents/*.md       "$DST/.claude/agents/"
cp "$SRC"/references/*.md    "$DST/.claude/references/"
cp "$SRC"/hooks/*.py         "$DST/.claude/hooks/"
cp "$SRC"/hooks/settings.example.json "$DST/.claude/settings.json"

# hooks は python を呼ぶ。本イメージは python(=python3) を用意済みなので置換不要だが、
# 念のため python3 明示に寄せておく
sed -i 's|"command": "python |"command": "python3 |g' "$DST/.claude/settings.json" || true

# skills（実装エージェントが参照）
mkdir -p "$DST/skills"
cp -r "$SRC"/skills/security-review   "$DST/skills/" 2>/dev/null || true
cp -r "$SRC"/skills/spec-traceability "$DST/skills/" 2>/dev/null || true

# 設計フェーズの状態テンプレート
mkdir -p "$DST/docs/_state"
cp "$SRC"/templates/_state_phase_status_template.md   "$DST/docs/_state/phase_status.md"   2>/dev/null || true
cp "$SRC"/templates/_state_open_questions_template.md "$DST/docs/_state/open_questions.md" 2>/dev/null || true
cp "$SRC"/templates/_state_answers_template.md        "$DST/docs/_state/answers.md"        2>/dev/null || true

echo "[install] 完了。$DST で 'claude --dangerously-skip-permissions' を起動してください。"
