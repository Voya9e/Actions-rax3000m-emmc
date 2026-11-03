#!/usr/bin/env bash
set -euo pipefail

# Keep the LAN address used by the existing RAX3000M firmware.
sed -i 's/192\.168\.1\.1/192.168.6.1/g' package/base-files/files/bin/config_generate

# Add packages that are not shipped in the official OpenWrt feeds.
cat >> feeds.conf.default <<'EOF'
src-git openclash https://github.com/vernesong/OpenClash.git;master
src-git argon https://github.com/jerrykuku/luci-theme-argon.git;master
src-git small https://github.com/kenzok8/small-package.git
EOF
