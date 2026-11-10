#!/usr/bin/env bash
set -euo pipefail

CORE_DIR="files/etc/openclash/core"
DATA_DIR="files/etc/openclash"
DEFAULTS_DIR="files/etc/uci-defaults"
mkdir -p "$CORE_DIR" "$DATA_DIR" "$DEFAULTS_DIR"

# OpenClash Smart core for the RAX3000M's ARM64 (aarch64) target.
# OpenClash stores both Smart and Meta cores at clash_meta.
SMART_URL="https://raw.githubusercontent.com/vernesong/OpenClash/core/dev/smart/clash-linux-arm64.tar.gz"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

curl -fL --retry 3 --retry-delay 2 "$SMART_URL" -o "$TMP_DIR/clash-smart.tar.gz"
tar -xzf "$TMP_DIR/clash-smart.tar.gz" -C "$TMP_DIR" clash
test -s "$TMP_DIR/clash"
install -m 0755 "$TMP_DIR/clash" "$CORE_DIR/clash_meta"
"$CORE_DIR/clash_meta" -v

# Geo databases used by OpenClash.
GEOIP_URL="https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geoip.dat"
GEOSITE_URL="https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat"
COUNTRY_URL="https://raw.githubusercontent.com/alecthw/mmdb_china_ip_list/release/lite/Country.mmdb"

curl -fL --retry 3 --retry-delay 2 "$GEOIP_URL" -o "$DATA_DIR/GeoIP.dat"
curl -fL --retry 3 --retry-delay 2 "$GEOSITE_URL" -o "$DATA_DIR/GeoSite.dat"
curl -fL --retry 3 --retry-delay 2 "$COUNTRY_URL" -o "$DATA_DIR/Country.mmdb"
test -s "$DATA_DIR/GeoIP.dat"
test -s "$DATA_DIR/GeoSite.dat"
test -s "$DATA_DIR/Country.mmdb"

# Run after OpenClash's own first-boot defaults so Smart is selected by default.
cat > "$DEFAULTS_DIR/zz-openclash-smart" <<'EOF'
#!/bin/sh

uci -q set openclash.config.smart_enable='1'
uci -q commit openclash
exit 0
EOF
chmod 0755 "$DEFAULTS_DIR/zz-openclash-smart"
