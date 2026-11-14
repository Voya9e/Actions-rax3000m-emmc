
# OpenWrt 25.12 for CMCC RAX3000M eMMC

The `Build OpenWrt 25.12` workflow compiles the official OpenWrt `openwrt-25.12` stable branch for the `mediatek/filogic` CMCC RAX3000M target.

## Included customizations

- LAN address: `192.168.6.1`
- Default router time zone: Shanghai (`Asia/Shanghai`, `CST-8`, UTC+8).
- On first boot, both Wi-Fi radios are enabled: 2.4 GHz SSID `蓝袜子` and 5 GHz SSID `BlueSock`. Both are open networks without a password.
- LuCI, Simplified Chinese language packs for the base interface, package manager, firewall, Disk Manager, Samba, and ttyd, plus the native package manager interface for OpenWrt 25.12 (APK). Select Simplified Chinese under **System → System → Language and Style**.
- Existing common utilities and selected LuCI apps, including OpenClash, Argon and Footstrap themes, disk management, FileBrowser Quantum LuCI from [kiddin9/op-packages](https://github.com/kiddin9/op-packages/tree/main/luci-app-filebrowser-q), Samba, and ttyd. OpenClash tracks its upstream `dev` feed; its Simplified Chinese translation is bundled in the app. The build presets the ARM64 Smart core as `/etc/openclash/core/clash_meta`, plus GeoIP, GeoSite, and Country.mmdb data, and enables Smart mode on first boot.
- Disk Manager uses [sbwml's ucode-based port](https://github.com/sbwml/luci-app-diskman), which declares support for OpenWrt 24.10 and newer.
- Docker support includes the OpenWrt 25.12 feed's Docker Engine, CLI, Compose, and Chinese-translated LuCI Dockerman. The firmware does not add first-boot auto-start for the daemon. Before enabling it, configure `/etc/config/dockerd` so `data_root` points to a mounted ext4 or Btrfs data disk; the default `/opt/docker/` can consume system storage. Then run `/etc/init.d/dockerd enable` and `/etc/init.d/dockerd start`. Docker-published ports may need firewall adjustments on OpenWrt's firewall4/nftables setup.
- Footstrap is included as an additional LuCI theme. The **Footstrap** and **Argon Config** settings submenus follow the active theme: switching to Footstrap shows **Footstrap**, and switching to Argon shows **Argon Config**. LuCI refreshes the menu cache for the selected theme. Choose a theme under **System → System → Language and Style → Design**. Footstrap's current translations cover Russian and Spanish, so its untranslated text falls back to English.
- USB drive support: USB mass storage and UAS drivers, block device mounting tools, and filesystem support for ext4, FAT32/VFAT, exFAT, NTFS3, Btrfs, XFS, and the already included F2FS. USB drive partitions can be mounted/configured through the system tools; automatic mounting can be configured with fstab. FileBrowser Quantum and its LuCI app are included; the backend uses the upstream ARM64 prebuilt binary, and its service is disabled by default. Configure `/etc/config/filebrowser-q` to enable the service and set its listen port and root path. A fresh installation initializes the account as `admin` / `admin`; change that password and restrict the root path before exposing the service beyond your trusted LAN. Existing installations keep their current account database. Samba remains available for SMB/network-share clients.
- The default eMMC frequency is 26 MHz. The workflow can optionally build at 52 MHz; some devices may not be stable at the higher frequency.
- The workflow defaults to the repository's NX30 Pro EEPROM. It embeds the first 4096 bytes into the RAX3000M eMMC device-tree overlay using mt76's `mediatek,eeprom-data` property. Untick “Use NX30 Pro EEPROM” to keep the factory-partition EEPROM. MAC addresses continue to come from the original factory NVMEM cells.
- The MTK SDK-only hardware QoS app is omitted from this official mt76-driver line.

The release contains eMMC-specific firmware and boot artifacts only, with a generated SHA-256 list. After each successful OpenWrt 25.12 build, the workflow retains the latest seven matching releases and deletes older releases together with their tags. Other release lines are unaffected.

To build, open **Actions**, select **Build OpenWrt 25.12**, choose the optional 52 MHz setting if needed, and select **Run workflow**.


