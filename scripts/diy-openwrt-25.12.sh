#!/usr/bin/env bash
set -euo pipefail

# Keep the LAN address used by the existing RAX3000M firmware.
sed -i 's/192[.]168[.]1[.]1/192.168.6.1/g' package/base-files/files/bin/config_generate

# Enable both RAX3000M radios with the requested open-network SSIDs on first boot.
WIFI_DEFAULTS=target/linux/mediatek/filogic/base-files/etc/uci-defaults/99-rax3000m-wifi
mkdir -p "$(dirname "$WIFI_DEFAULTS")"
cat > "$WIFI_DEFAULTS" <<'EOF'
#!/bin/sh

for radio in $(uci show wireless | grep '=wifi-device$' | cut -d. -f2 | cut -d= -f1); do
    band="$(uci -q get "wireless.$radio.band")"
    case "$band" in
        2g) ssid='蓝袜子' ;;
        5g) ssid='BlueSock' ;;
        *) continue ;;
    esac

    uci -q set "wireless.$radio.disabled=0"

    for iface in $(uci show wireless | grep '=wifi-iface$' | cut -d. -f2 | cut -d= -f1); do
        [ "$(uci -q get "wireless.$iface.device")" = "$radio" ] || continue
        uci -q set "wireless.$iface.ssid=$ssid"
        uci -q set "wireless.$iface.encryption=none"
        uci -q delete "wireless.$iface.key" || true
        uci -q set "wireless.$iface.disabled=0"
    done
done

uci commit wireless
exit 0
EOF
chmod 0755 "$WIFI_DEFAULTS"

# Set the router's default system time zone to Hong Kong on first boot.
TIMEZONE_DEFAULTS=target/linux/mediatek/filogic/base-files/etc/uci-defaults/98-rax3000m-timezone
cat > "$TIMEZONE_DEFAULTS" <<'EOF'
#!/bin/sh

uci -q set 'system.@system[0].timezone=HKT-8'
uci -q set 'system.@system[0].zonename=Asia/Hong_Kong'
uci commit system
exit 0
EOF
chmod 0755 "$TIMEZONE_DEFAULTS"

# Add packages that are not shipped in the official OpenWrt feeds.
cat >> feeds.conf.default <<'EOF'
src-git openclash https://github.com/vernesong/OpenClash.git;dev
src-git argon https://github.com/jerrykuku/luci-theme-argon.git;master
src-git small https://github.com/kenzok8/small-package.git
src-git diskman https://github.com/sbwml/luci-app-diskman.git
src-git footstrap https://github.com/VizzleTF/luci-theme-footstrap.git
EOF
