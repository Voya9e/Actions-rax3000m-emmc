#!/bin/bash

# Set the router hostname and LuCI system description on first boot.
SYSTEM_DEFAULTS=package/base-files/files/etc/uci-defaults/99-rax3000m-system
mkdir -p "$(dirname "$SYSTEM_DEFAULTS")"
cat > "$SYSTEM_DEFAULTS" <<'EOF'
#!/bin/sh

uci -q set 'system.@system[0].hostname=bAIR'
uci -q set 'system.@system[0].description=A bair ef socks.'
uci commit system
exit 0
EOF
chmod 0755 "$SYSTEM_DEFAULTS"

# 设置ttyd免密登录(1为启用命令,填0为不作修改)
export Ttyd_account_free_login="0"

#更改默认地址为192.168.6.1
sed -i 's/192.168.1.1/192.168.6.1/g' package/base-files/files/bin/config_generate

# 添加软件源
# sed -i '$a src-git lienol https://github.com/Lienol/openwrt-package' feeds.conf.default
# sed -i '$a src-git kiddin9 https://github.com/kiddin9/openwrt-packages' feeds.conf.default
# sed -i '$a src-git smpackage https://github.com/kenzok8/small-package' feeds.conf.default
# sed -i '$a src-git mihomo https://github.com/morytyann/OpenWrt-mihomo.git;main' feeds.conf.default

# 添加luci-app-adguardhome
git clone https://github.com/chenmozhijin/luci-app-adguardhome.git package/luci-app-adguardhome
# 添加迅雷下载


# 增加AdGuardHome插件和核心
export AdGuardHome_Core="1"


