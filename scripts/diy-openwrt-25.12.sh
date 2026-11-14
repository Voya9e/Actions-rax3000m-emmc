#!/usr/bin/env bash
set -euo pipefail

# Match the RAX3000M 64 GB eMMC data area: a 57 GiB partition beginning at 553 MiB.
# This workflow only builds the CMCC RAX3000M eMMC profile.
GPT_IMAGE=target/linux/mediatek/image/filogic.mk
python3 - "$GPT_IMAGE" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
source = path.read_text()
marker = "-N data -p 58368M@553M"
if marker not in source:
    start_marker = "$(if $(findstring emmc,$1),"
    start = source.index(start_marker)
    block_end = re.search(r"\n[ \t]*\)", source[start:])
    if block_end is None:
        raise SystemExit(f"Could not find the eMMC GPT block in {path}")
    end = start + block_end.start()
    emmc_block = source[start:end]
    pattern = re.compile(r"(^[ \t]*-t 0x2e -N production[^\n]*\\$)", re.MULTILINE)
    partition = "\n\t\t\t-t 0x83 -N data -p 58368M@553M " + chr(92)
    emmc_block, replacements = pattern.subn(
        lambda match: match.group(1) + partition,
        emmc_block,
        count=1,
    )
    if replacements != 1:
        raise SystemExit(f"Could not add the VidBee eMMC partition to {path}")
    path.write_text(source[:start] + emmc_block + source[end:])
PY

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

# Set the router's default system time zone to Shanghai on first boot.
TIMEZONE_DEFAULTS=target/linux/mediatek/filogic/base-files/etc/uci-defaults/98-rax3000m-timezone
cat > "$TIMEZONE_DEFAULTS" <<'EOF'
#!/bin/sh

uci -q set 'system.@system[0].timezone=CST-8'
uci -q set 'system.@system[0].zonename=Asia/Shanghai'
uci commit system
exit 0
EOF
chmod 0755 "$TIMEZONE_DEFAULTS"

# Set LuCI's default interface language to Simplified Chinese on first boot.
LANGUAGE_DEFAULTS=target/linux/mediatek/filogic/base-files/etc/uci-defaults/97-rax3000m-luci-language
mkdir -p "$(dirname "$LANGUAGE_DEFAULTS")"
cat > "$LANGUAGE_DEFAULTS" <<'EOF'
#!/bin/sh

uci -q set 'luci.main.lang=zh_cn'
uci commit luci
exit 0
EOF
chmod 0755 "$LANGUAGE_DEFAULTS"

# Start VidBee automatically from official ARM64 container images on the eMMC data partition.
DATA_INIT=package/base-files/files/etc/init.d/rax3000m-data
mkdir -p "$(dirname "$DATA_INIT")"
cat > "$DATA_INIT" <<'EOF'
#!/bin/sh /etc/rc.common

START=10
STOP=90

STORAGE_DEVICE=/dev/mmcblk0p6
STORAGE_MOUNT=/data
SWAPFILE="$STORAGE_MOUNT/swapfile"
READY_FLAG=/var/run/rax3000m-data.ready

log() {
    logger -t rax3000m-data "$*"
}

is_mounted() {
    awk -v device="$STORAGE_DEVICE" -v mountpoint="$STORAGE_MOUNT" \
        '$1 == device && $2 == mountpoint { found = 1 } END { exit !found }' /proc/mounts
}

initialize_storage() {
    [ -b "$STORAGE_DEVICE" ] || return 1
    [ "$(blkid -s PARTLABEL -o value "$STORAGE_DEVICE" 2>/dev/null || true)" = data ] || return 1

    mkdir -p "$STORAGE_MOUNT"
    if ! is_mounted; then
        fs_type="$(blkid -s TYPE -o value "$STORAGE_DEVICE" 2>/dev/null || true)"
        if [ -z "$fs_type" ]; then
            mkfs.ext4 -F -L data "$STORAGE_DEVICE" || return 1
            fs_type=ext4
        fi
        [ "$fs_type" = ext4 ] || return 1
        mount -t ext4 -o noatime "$STORAGE_DEVICE" "$STORAGE_MOUNT" || return 1
    fi

    mkdir -p "$STORAGE_MOUNT/docker" "$STORAGE_MOUNT/vidbee/downloads" "$STORAGE_MOUNT/vidbee/data"
    chown 1000:1000 "$STORAGE_MOUNT/vidbee/downloads" "$STORAGE_MOUNT/vidbee/data"
    uci -q show dockerd.globals >/dev/null 2>&1 || uci -q set dockerd.globals=globals
    uci -q set 'dockerd.globals.data_root=/data/docker'
    uci -q commit dockerd

    if [ ! -f "$SWAPFILE" ] || [ "$(stat -c '%s' "$SWAPFILE" 2>/dev/null || echo 0)" -ne 1073741824 ]; then
        swap_tmp="$SWAPFILE.tmp"
        rm -f "$swap_tmp"
        dd if=/dev/zero of="$swap_tmp" bs=1M count=1024 || return 1
        chmod 0600 "$swap_tmp"
        mkswap "$swap_tmp" || return 1
        mv "$swap_tmp" "$SWAPFILE" || return 1
    fi
    chmod 0600 "$SWAPFILE"
    if ! grep -q "^$SWAPFILE " /proc/swaps; then
        swapon "$SWAPFILE" 2>/dev/null || { mkswap "$SWAPFILE" && swapon "$SWAPFILE"; } || return 1
    fi

    touch "$READY_FLAG"
    log "Data partition mounted and 1 GiB swap enabled"
}

start() {
    rm -f "$READY_FLAG"
    attempt=0
    while ! initialize_storage; do
        attempt=$((attempt + 1))
        [ "$attempt" -lt 30 ] || {
            log "Unable to initialize the data partition or swap"
            return 1
        }
        sleep 2
    done
}
EOF
chmod 0755 "$DATA_INIT"

VIDBEE_SUPERVISOR=package/base-files/files/usr/sbin/vidbee-supervisor
mkdir -p "$(dirname "$VIDBEE_SUPERVISOR")"
cat > "$VIDBEE_SUPERVISOR" <<'EOF'
#!/bin/sh

DATA_READY_FLAG=/var/run/rax3000m-data.ready
VIDBEE_ROOT=/data/vidbee
API_IMAGE=ghcr.io/nexmoe/vidbee-api:latest
WEB_IMAGE=ghcr.io/nexmoe/vidbee-web:latest

log() {
    logger -t vidbee "$*"
}

data_is_ready() {
    [ -f "$DATA_READY_FLAG" ] \
        && awk '$1 == "/dev/mmcblk0p6" && $2 == "/data" { found = 1 } END { exit !found }' /proc/mounts \
        && grep -q '^/data/swapfile ' /proc/swaps
}

ensure_container() {
    name="$1"
    image="$2"
    shift 2

    if docker container inspect "$name" >/dev/null 2>&1; then
        running="$(docker container inspect --format '{{.State.Running}}' "$name" 2>/dev/null || true)"
        [ "$running" = true ] || docker start "$name" >/dev/null
        return
    fi

    docker run -d --name "$name" --restart unless-stopped "$@" "$image" >/dev/null
}

while :; do
    if ! data_is_ready; then
        log "Waiting for the data service to mount /data and enable swap"
        sleep 60
        continue
    fi

    /etc/init.d/dockerd start >/dev/null 2>&1 || true
    if ! docker info >/dev/null 2>&1; then
        sleep 20
        continue
    fi

    if ! docker image inspect "$API_IMAGE" >/dev/null 2>&1; then
        log "Pulling official VidBee API image"
        docker pull "$API_IMAGE" || { sleep 60; continue; }
    fi
    if ! docker image inspect "$WEB_IMAGE" >/dev/null 2>&1; then
        log "Pulling official VidBee Web image"
        docker pull "$WEB_IMAGE" || { sleep 60; continue; }
    fi

    if ! docker network inspect vidbee >/dev/null 2>&1; then
        docker network create vidbee >/dev/null || { sleep 20; continue; }
    fi

    LAN_IP="$(uci -q get network.lan.ipaddr || true)"
    if [ -z "$LAN_IP" ] || ! ip -4 address show | grep -q " $LAN_IP/"; then
        sleep 20
        continue
    fi

    if ! ensure_container vidbee-api "$API_IMAGE" \
        --network vidbee --network-alias api \
        --publish "$LAN_IP:3100:3100" \
        --env VIDBEE_API_HOST=0.0.0.0 \
        --env VIDBEE_API_PORT=3100 \
        --env VIDBEE_DOWNLOAD_DIR=/data/downloads \
        --env VIDBEE_DATA_DIR=/data/vidbee \
        --env VIDBEE_HISTORY_STORE_PATH=/data/vidbee/vidbee.db \
        --volume "$VIDBEE_ROOT/downloads:/data/downloads" \
        --volume "$VIDBEE_ROOT/data:/data/vidbee"; then
        log "Unable to start VidBee API container"
        sleep 60
        continue
    fi

    if ! ensure_container vidbee-web "$WEB_IMAGE" \
        --network vidbee \
        --publish "$LAN_IP:3000:3000" \
        --env VIDBEE_API_URL_INTERNAL=http://api:3100 \
        --env VIDBEE_WEB_HOST=0.0.0.0 \
        --env VIDBEE_WEB_PORT=3000; then
        log "Unable to start VidBee Web container"
        sleep 60
        continue
    fi

    log "VidBee is available at http://$LAN_IP:3000"
    while :; do
        if ! docker info >/dev/null 2>&1; then
            /etc/init.d/dockerd start >/dev/null 2>&1 || true
            sleep 60
            continue
        fi
        for name in vidbee-api vidbee-web; do
            running="$(docker container inspect --format '{{.State.Running}}' "$name" 2>/dev/null || true)"
            if [ "$running" != true ]; then
                docker start "$name" >/dev/null 2>&1 || break
            fi
        done
        sleep 60
    done
done
EOF
chmod 0755 "$VIDBEE_SUPERVISOR"

VIDBEE_INIT=package/base-files/files/etc/init.d/vidbee
mkdir -p "$(dirname "$VIDBEE_INIT")"
cat > "$VIDBEE_INIT" <<'EOF'
#!/bin/sh /etc/rc.common

USE_PROCD=1
START=99

start_service() {
    procd_open_instance
    procd_set_param command /usr/sbin/vidbee-supervisor
    procd_set_param respawn 3600 5 5
    procd_close_instance
}
EOF
chmod 0755 "$VIDBEE_INIT"

VIDBEE_DEFAULTS=target/linux/mediatek/filogic/base-files/etc/uci-defaults/96-rax3000m-vidbee
mkdir -p "$(dirname "$VIDBEE_DEFAULTS")"
cat > "$VIDBEE_DEFAULTS" <<'EOF'
#!/bin/sh

uci -q show dockerd.globals >/dev/null 2>&1 || uci -q set dockerd.globals=globals
uci -q set 'dockerd.globals.data_root=/data/docker'
uci -q commit dockerd
/etc/init.d/dockerd disable >/dev/null 2>&1 || true
/etc/init.d/rax3000m-data enable
/etc/init.d/vidbee enable
# UCI defaults run inside S10boot, after rcS has expanded its startup list.
# Start both services now so the first boot follows the same storage-first order.
/etc/init.d/rax3000m-data start >/dev/null 2>&1 || true
/etc/init.d/vidbee start >/dev/null 2>&1 || true
exit 0
EOF
chmod 0755 "$VIDBEE_DEFAULTS"

# Add packages that are not shipped in the official OpenWrt feeds.
cat >> feeds.conf.default <<'EOF'
src-git openclash https://github.com/vernesong/OpenClash.git;dev
src-git small https://github.com/kenzok8/small-package.git
src-git diskman https://github.com/sbwml/luci-app-diskman.git
src-git footstrap https://github.com/VizzleTF/luci-theme-footstrap.git
src-git kiddin9 https://github.com/kiddin9/op-packages.git
EOF
