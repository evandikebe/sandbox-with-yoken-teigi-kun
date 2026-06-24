#!/usr/bin/env bash
# =============================================================================
# コンテナ起動時の処理:
#   1) ~/.claude を初回シード（プラグイン有効化設定）
#   2) 許可リスト型ファイアウォールを適用（best-effort）
#   3) プラグインを git から取得/更新（PLUGIN_REPO_URL 指定時）or 同梱版をseed
#   4) git 設定（進捗管理用: 所有者許可 + GitHub 認証）
#   5) 認証状態を確認（サブスクログイン or OAuthトークン）
#   6) claude --dangerously-skip-permissions を起動（cwd = マウント先 /workspace）
# =============================================================================
set -euo pipefail

CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
MP="/home/node/.yoken-marketplace"          # ローカルマーケットプレイス
PLUGIN_DIR="$MP/yoken-teigi-kun-ver-opus"   # プラグイン本体の置き場
BAKED="/opt/yoken-marketplace"              # イメージ同梱版（フォールバック元）

# --- 1) 設定のシード（マウント永続ボリュームを壊さないよう、無い時だけ） -------
mkdir -p "$CLAUDE_DIR"
if [ ! -f "$CLAUDE_DIR/settings.json" ]; then
  cp /opt/claude-defaults/settings.json "$CLAUDE_DIR/settings.json"
  echo "[entrypoint] 既定 settings.json をシードしました（プラグイン有効化）。"
fi

# --- 2) ファイアウォール（root 権限が要るので sudo 経由） ---------------------
if [ "${YOKEN_FIREWALL:-on}" = "on" ]; then
  sudo /usr/local/bin/init-firewall.sh || \
    echo "[entrypoint] firewall 適用に失敗（隔離が弱い状態で続行）。" >&2
else
  echo "[entrypoint] YOKEN_FIREWALL=off のため firewall をスキップ。" >&2
fi

# --- 2.5) コンテナ専用volume(node_modules等)を node 所有に直す -----------------
sudo /usr/local/bin/fix-perms.sh || true

# --- 3) プラグインの取得/更新 -------------------------------------------------
mkdir -p "$MP/.claude-plugin"
if [ ! -f "$MP/.claude-plugin/marketplace.json" ]; then
  cp "$BAKED/.claude-plugin/marketplace.json" "$MP/.claude-plugin/marketplace.json"
fi

if [ -n "${PLUGIN_REPO_URL:-}" ]; then
  CLONE_URL="$PLUGIN_REPO_URL"
  if [ -n "${GITHUB_TOKEN:-}" ]; then
    CLONE_URL="$(printf '%s' "$PLUGIN_REPO_URL" | sed -E 's#^https://#https://x-access-token:'"$GITHUB_TOKEN"'@#')"
  fi
  REF="${PLUGIN_REPO_REF:-}"

  if [ -d "$PLUGIN_DIR/.git" ]; then
    echo "[entrypoint] プラグインを git pull で更新..."
    git -C "$PLUGIN_DIR" remote set-url origin "$CLONE_URL" >/dev/null 2>&1 || true
    if git -C "$PLUGIN_DIR" fetch --depth 1 origin >/dev/null 2>&1; then
      git -C "$PLUGIN_DIR" reset --hard "origin/${REF:-HEAD}" >/dev/null 2>&1 \
        || git -C "$PLUGIN_DIR" reset --hard FETCH_HEAD >/dev/null 2>&1 || true
      echo "[entrypoint] プラグイン更新 完了。"
    else
      echo "[entrypoint] pull 失敗。前回取得分で続行します。" >&2
    fi
  else
    echo "[entrypoint] プラグインを git clone で取得..."
    rm -rf "$PLUGIN_DIR"
    if git clone --depth 1 ${REF:+--branch "$REF"} "$CLONE_URL" "$PLUGIN_DIR" >/dev/null 2>&1; then
      echo "[entrypoint] clone 完了: $PLUGIN_REPO_URL ${REF:+($REF)}"
    else
      echo "[entrypoint] clone 失敗（URL/トークン/ネットワークを確認）。同梱版で続行します。" >&2
      rm -rf "$PLUGIN_DIR"; cp -r "$BAKED/yoken-teigi-kun-ver-opus" "$PLUGIN_DIR"
    fi
  fi
else
  if [ ! -d "$PLUGIN_DIR" ]; then
    cp -r "$BAKED/yoken-teigi-kun-ver-opus" "$PLUGIN_DIR"
    echo "[entrypoint] 同梱プラグインを配置しました（PLUGIN_REPO_URL 未指定）。"
  fi
fi

# --- 4) git 設定（プロジェクトの進捗管理用） ---------------------------------
# bind mount は所有者がホスト側のため、safe.directory を許可しないと
# git が "dubious ownership" で停止する。
git config --global --add safe.directory '*' 2>/dev/null || true
git config --global init.defaultBranch main 2>/dev/null || true
git config --global user.name  "${GIT_USER_NAME:-yoken-sandbox}"        2>/dev/null || true
git config --global user.email "${GIT_USER_EMAIL:-yoken-sandbox@local}" 2>/dev/null || true
if [ -n "${GITHUB_TOKEN:-}" ]; then
  # GitHub/HTTPS の push/pull をトークンで認証（credential helper）
  git config --global credential.helper store
  printf 'https://x-access-token:%s@github.com\n' "$GITHUB_TOKEN" > "$HOME/.git-credentials"
  chmod 600 "$HOME/.git-credentials"
  echo "[entrypoint] git 認証(GitHub/HTTPS)を設定。commit/push 可（トークンの権限に依存）。"
else
  echo "[entrypoint] GITHUB_TOKEN 未設定 → ローカル commit は可、push は不可。" >&2
fi

# --- 5) 認証状態の確認 -------------------------------------------------------
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  echo "[entrypoint] ANTHROPIC_API_KEY 検出 → API課金で動作します。"
elif [ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
  echo "[entrypoint] CLAUDE_CODE_OAUTH_TOKEN 検出 → サブスク(トークン)で動作します。"
elif [ -f "$CLAUDE_DIR/.credentials.json" ]; then
  echo "[entrypoint] 保存済みログイン情報を検出 → サブスクで動作します。"
else
  cat >&2 <<'MSG'
------------------------------------------------------------------
[entrypoint] まだログインしていません。次のいずれかでログインしてください:
  方法1（推奨）: ホストで `claude setup-token` → .env の
                  CLAUDE_CODE_OAUTH_TOKEN に設定。
  方法2: このコンテナ内で `claude /login` を実行し、URL をブラウザで認証。
------------------------------------------------------------------
MSG
fi

# --- 6) Claude 起動（cwd = /workspace = マウントしたプロジェクト） ------------
echo "[entrypoint] cwd=$(pwd) で claude --dangerously-skip-permissions 起動..."
exec claude --dangerously-skip-permissions "$@"
