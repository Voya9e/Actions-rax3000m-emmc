# OpenWrt 25.12 for CMCC RAX3000M eMMC

The `Build OpenWrt 25.12` workflow compiles the official OpenWrt `openwrt-25.12` stable branch for the `mediatek/filogic` CMCC RAX3000M target.

## Included customizations

- LAN address: `192.168.6.1`
- Default router time zone: Shanghai (`Asia/Shanghai`, `CST-8`, UTC+8).
- On first boot, both Wi-Fi radios are enabled: 2.4 GHz SSID `蓝袜子` and 5 GHz SSID `BlueSock`. Both are open networks without a password.
- LuCI, Simplified Chinese language packs for the base interface, package manager, firewall, Disk Manager, Samba, and ttyd, plus the native package manager interface for OpenWrt 25.12 (APK). Select Simplified Chinese under **System → System → Language and Style**.
- Existing common utilities and selected LuCI apps, including OpenClash, Argon and Footstrap themes, disk management, FileBrowser Quantum, Samba, and ttyd. OpenClash tracks its upstream `dev` feed; its Simplified Chinese translation is bundled in the app.
- Disk Manager uses [sbwml's ucode-based port](https://github.com/sbwml/luci-app-diskman), which declares support for OpenWrt 24.10 and newer.
- Footstrap is included as an additional LuCI theme; the **Footstrap** and **Argon Config** settings menus appear only while their respective theme is active. Choose Footstrap under **System → System → Language and Style → Design**. Its current translation packages cover Russian and Spanish, so the theme's own untranslated text falls back to English.
- USB drive support: USB mass storage and UAS drivers, block device mounting tools, and filesystem support for ext4, FAT32/VFAT, exFAT, NTFS3, Btrfs, XFS, and the already included F2FS. USB drive partitions can be mounted/configured through the system tools; automatic mounting can be configured with fstab. FileBrowser Quantum is included as an automatically started service at `http://192.168.6.1:8080`, with `/mnt` exposed as its file source. It can browse the router's locally mounted USB files without Samba; Samba remains installed for SMB/network-share clients. On first start, Quantum generates a one-time admin password in the system log; retrieve it with `logread | grep -i filebrowser` and sign in as `admin`. Previews and indexing are disabled by default to reduce router resource use; this also disables indexed search and folder-size statistics.
- The default eMMC frequency is 26 MHz. The workflow can optionally build at 52 MHz; some devices may not be stable at the higher frequency.
- The workflow defaults to the repository's NX30 Pro EEPROM. It embeds the first 4096 bytes into the RAX3000M eMMC device-tree overlay using mt76's `mediatek,eeprom-data` property. Untick “Use NX30 Pro EEPROM” to keep the factory-partition EEPROM. MAC addresses continue to come from the original factory NVMEM cells.
- The MTK SDK-only hardware QoS app is omitted from this official mt76-driver line.

The release contains eMMC-specific firmware and boot artifacts only, with a generated SHA-256 list. The workflow does not remove prior releases automatically.

To build, open **Actions**, select **Build OpenWrt 25.12**, choose the optional 52 MHz setting if needed, and select **Run workflow**.
