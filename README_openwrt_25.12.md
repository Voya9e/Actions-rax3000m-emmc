# OpenWrt 25.12 for CMCC RAX3000M eMMC

The `Build OpenWrt 25.12` workflow compiles the official OpenWrt `openwrt-25.12` stable branch for the `mediatek/filogic` CMCC RAX3000M target.

## Included customizations

- LAN address: `192.168.6.1`
- LuCI, Chinese base translation, and the native package manager interface for OpenWrt 25.12 (APK)
- Existing common utilities and selected LuCI apps, including OpenClash, AdGuard Home, Argon, disk management, file browser, Samba, and ttyd
- The default eMMC frequency is 26 MHz. The workflow can optionally build at 52 MHz; some devices may not be stable at the higher frequency.
- The stock EEPROM is retained. OpenWrt 25.12 reads the RAX3000M eMMC calibration data through the device tree's factory-partition NVMEM path, so the older NX30 Pro replacement step is not copied into this line.
- The MTK SDK-only hardware QoS app is omitted from this official mt76-driver line.

The release contains eMMC-specific firmware and boot artifacts only, with a generated SHA-256 list. The workflow does not remove prior releases automatically.

To build, open **Actions**, select **Build OpenWrt 25.12**, choose the optional 52 MHz setting if needed, and select **Run workflow**.
