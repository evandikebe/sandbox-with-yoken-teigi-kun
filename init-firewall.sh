#!/usr/bin/env bash
# =============================================================================
# 許可リスト型(allowlist)ファイアウォール
#   既定は「全 OUTBOUND 遮断」。下の ALLOWED_DOMAINS と GitHub の IP のみ許可。
#   --dangerously-skip-permissions で動くエージェントが、想定外の宛先へ
#   通信・データ送信するのを OS レイヤで封じ込めるのが目的。
#
#   root 権限が必要(entrypoint が sudo で呼ぶ)。CAP_NET_ADMIN/NET_RAW が
#   付与されていない環境では何もせず正常終了する(隔離は弱まる旨を警告)。
# =============================================================================
set -euo pipefail

# 権限・ケーパビリティが無ければスキップ（compose で cap_add を付け忘れた場合など）
if ! iptables -L >/dev/null 2>&1; then
  echo "[firewall] iptables を操作できないためスキップします（cap_add: NET_ADMIN を確認してください）。" >&2
  echo "[firewall] ※ この状態ではネットワーク隔離が効いていません。" >&2
  exit 0
fi

# 許可ドメイン（スペース区切り・環境変数で上書き可）
ALLOWED_DOMAINS="${ALLOWED_DOMAINS:-\
api.anthropic.com \
console.anthropic.com \
statsig.anthropic.com \
sentry.io \
o227196.ingest.sentry.io \
registry.npmjs.org \
pypi.org \
files.pythonhosted.org \
binaries.prisma.sh \
checkpoint.prisma.io \
objects.githubusercontent.com \
raw.githubusercontent.com \
github.com \
api.github.com \
codeload.github.com}"

echo "[firewall] ルール初期化..."
iptables -F
iptables -X 2>/dev/null || true
ipset destroy allowed-domains 2>/dev/null || true

# ループバックは常に許可
iptables -A INPUT  -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# DNS（名前解決）と確立済みコネクションは許可
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT
iptables -A INPUT  -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# 開発サーバ等の受信を許可（ホストのブラウザから localhost:PORT で覗く用）
# DEV_PORTS は .env で上書き可（スペース/カンマ区切り）。既定 3000。
for _p in $(printf '%s' "${DEV_PORTS:-3000}" | tr ',' ' '); do
  iptables -A INPUT -p tcp --dport "$_p" -j ACCEPT
done

# 許可IPの ipset を作成
ipset create allowed-domains hash:net

# GitHub の公開 API/Web レンジを meta API から取得して登録
echo "[firewall] GitHub IP レンジ取得..."
if gh_ranges="$(curl -fsSL --max-time 15 https://api.github.com/meta 2>/dev/null)"; then
  echo "$gh_ranges" \
    | jq -r '(.web + .api + .git)[]?' 2>/dev/null \
    | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/[0-9]+$' \
    | while read -r cidr; do ipset add allowed-domains "$cidr" 2>/dev/null || true; done
else
  echo "[firewall] GitHub meta 取得失敗（github.com への git は効かない場合あり）。" >&2
fi

# 許可ドメインを名前解決して登録
for domain in $ALLOWED_DOMAINS; do
  ips="$(dig +short A "$domain" 2>/dev/null | grep -E '^[0-9.]+$' || true)"
  for ip in $ips; do
    ipset add allowed-domains "$ip" 2>/dev/null || true
  done
done
echo "[firewall] 許可エントリ数: $(ipset list allowed-domains | grep -c '^[0-9]' || echo 0)"

# ホスト（Docker DNS/ゲートウェイ）への通信は許可（DNS解決のため）
host_net="$(ip route | awk '/default/ {print $3}' | head -1)"
if [ -n "${host_net:-}" ]; then
  iptables -A OUTPUT -d "$host_net" -j ACCEPT
fi

# 許可IPセット宛のみ OUTBOUND を許可
iptables -A OUTPUT -m set --match-set allowed-domains dst -j ACCEPT

# それ以外の OUTBOUND/INBOUND は破棄（デフォルト deny）
iptables -P INPUT   DROP
iptables -P FORWARD DROP
iptables -P OUTPUT  DROP

echo "[firewall] 完了。許可: Anthropic / npm / PyPI / GitHub / DNS のみ。"
