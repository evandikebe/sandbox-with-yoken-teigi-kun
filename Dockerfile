# =============================================================================
# yoken-teigi-kun-ver-opus 実行用サンドボックス
# - Claude Code を --dangerously-skip-permissions で安全に隔離実行するためのイメージ
# - 非rootユーザー(node)で起動（skip-permissions は root を拒否するため必須）
# - 実装エージェント向けに Node/TS + Python3.11 + DBクライアントを同梱
# =============================================================================
FROM node:22-bookworm

# --- OSパッケージ --------------------------------------------------------------
# python3(=3.11 on bookworm) : hooks(.py) と Pythonバックエンド/バッチ実装用
# postgresql-client/sqlite3   : DB実装エージェントの動作確認用
# iptables/ipset/dnsutils     : 許可リスト型ファイアウォール用
# sudo                        : node が firewall スクリプトのみ root 実行するため
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-pip python3-venv \
      postgresql-client sqlite3 \
      git curl jq ripgrep less procps \
      ca-certificates iptables ipset dnsutils iproute2 \
      sudo \
    && ln -sf /usr/bin/python3 /usr/local/bin/python \
    && rm -rf /var/lib/apt/lists/*

# --- Claude Code CLI -----------------------------------------------------------
RUN npm install -g @anthropic-ai/claude-code @anthropic-ai/sdk pnpm typescript \
    && npm cache clean --force

# --- node ユーザーに firewall スクリプトだけ sudo 許可 -------------------------
# （これ以外は sudo 不可。skip-permissions の暴走を OS 側で封じ込める）
RUN printf '%s\n' \
      'node ALL=(root) NOPASSWD: /usr/local/bin/init-firewall.sh' \
      'node ALL=(root) NOPASSWD: /usr/local/bin/fix-perms.sh' \
      > /etc/sudoers.d/yoken \
    && chmod 0440 /etc/sudoers.d/yoken

# --- スクリプト類 --------------------------------------------------------------
COPY init-firewall.sh /usr/local/bin/init-firewall.sh
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY scripts/install-plugin-into-project.sh /usr/local/bin/install-plugin-into-project.sh
COPY fix-perms.sh /usr/local/bin/fix-perms.sh
RUN chmod +x /usr/local/bin/init-firewall.sh \
             /usr/local/bin/entrypoint.sh \
             /usr/local/bin/install-plugin-into-project.sh \
             /usr/local/bin/fix-perms.sh

# --- プラグイン(ローカルマーケットプレイス) を焼き込み -------------------------
# /opt 配下に置き、settings.json から参照する。イメージに同梱するので
# 外部パスのバインドマウントに依存せず再現性が高い。
COPY marketplace/ /opt/yoken-marketplace/

# --- Claude のデフォルト設定(プラグイン有効化 + hooks用python) -----------------
# 初回起動時に entrypoint が ~/.claude へコピーする（ボリュームを汚さない設計）
COPY claude-defaults/ /opt/claude-defaults/

# 作業ディレクトリ / Claude設定 / プラグイン取得先 を node 所有で先に作る
# （named volume は初回マウント時にこのディレクトリの所有者を引き継ぐため、
#   ここで node:node にしておかないと volume が root 所有になり書き込めない）
RUN mkdir -p /workspace /workspace/node_modules /home/node/.claude /home/node/.yoken-marketplace \
    && chown -R node:node /workspace /workspace/node_modules /home/node/.claude \
                         /home/node/.yoken-marketplace /opt/claude-defaults
WORKDIR /workspace

# 非rootで実行（skip-permissions の必須要件）
USER node
ENV HOME=/home/node \
    CLAUDE_CONFIG_DIR=/home/node/.claude \
    NPM_CONFIG_PREFIX=/home/node/.npm-global \
    PATH=/home/node/.npm-global/bin:$PATH

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
# 引数なしなら対話モードで Claude を起動
CMD []
