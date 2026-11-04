<div align="center">

# CMCC RAX3000M eMMC 固件编译

基于 GitHub Actions 的在线构建项目

[![OpenWrt 25.12](https://img.shields.io/badge/OpenWrt-25.12-blue)](README_openwrt_25.12.md)
[![ImmortalWrt](https://img.shields.io/badge/ImmortalWrt-MT798x-orange)](README.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

</div>

> 支持 CMCC RAX3000M eMMC 版。仓库提供官方 OpenWrt 25.12（开源 mt76 驱动）和旧版 ImmortalWrt MT798x（MTK SDK mt_wifi 驱动）两条构建路线。

## 选择构建路线

| 路线 | 固件来源 | 无线驱动 | 说明 |
| --- | --- | --- | --- |
| **OpenWrt 25.12** | OpenWrt 官方 `openwrt-25.12` 分支 | 开源 `mt76` | 新版主线方案，推荐新装或迁移使用 |
| **ImmortalWrt MT798x** | hanwckf `openwrt-21.02` 分支 | MTK SDK `mt_wifi` | 旧版方案，包含 MTK SDK 无线配置选项 |

- [OpenWrt 25.12 构建说明](README_openwrt_25.12.md)
- [ImmortalWrt 开源驱动构建说明](README_mainline.md)
- [旧版 MTK SDK 工作流](.github/workflows/build-immortalwrt-mt798x.yml)

## 快速开始

1. 打开仓库的 [Actions 页面](../../actions)。
2. 选择 **Build OpenWrt 25.12**。
3. 点击 **Run workflow**，按需选择 eMMC 频率和 EEPROM 选项。
4. 构建完成后，在对应的 [Release](../../releases) 下载固件。

25.12 工作流默认使用 26 MHz eMMC 频率和仓库提供的 NX30 Pro EEPROM。52 MHz 选项可能不适用于所有设备；更改 EEPROM 前请先备份本机原厂校准数据。

## OpenWrt 25.12 发布文件

Release 会包含：

- `*-emmc-ddr3-preloader.bin` 与 `*-emmc-ddr3-bl31-uboot.fip`：DDR3 eMMC 启动文件。
- `*-emmc-gpt.bin`：eMMC GPT 分区布局文件。
- `*-emmc-squashfs-sysupgrade.itb`：系统升级镜像。
- `*-emmc-initramfs-recovery.itb`：临时恢复系统镜像。
- `sha256sums`：文件完整性校验清单。

**本项目面向 DDR3 eMMC 设备。** DDR4 启动文件是构建输出中的通用产物，不应刷入 DDR3 设备。刷写前请按照对应固件和 U-Boot 的安装说明操作。

## 旧版 ImmortalWrt MTK SDK 固件

旧版构建面向 CMCC RAX3000M eMMC，使用 hanwckf 的 `immortalwrt-mt798x` 项目 `openwrt-21.02` 分支，内核为 5.4.x，采用 MTK SDK `mt_wifi` 无线驱动。

该路线提供 `mtwifi-cfg` 与 MTK SDK `luci-app-mtk` 无线配置方式，并可选择是否替换 NX30 Pro EEPROM。详细说明见 [旧版 README](README_mainline.md) 及相关工作流。

## 致谢

感谢以下项目及贡献者：

- [ImmortalWrt](https://github.com/immortalwrt/immortalwrt) 与 [OpenWrt](https://github.com/openwrt/openwrt)
- [hanwckf/immortalwrt-mt798x](https://github.com/hanwckf/immortalwrt-mt798x)
- [lgs2007m/Actions-OpenWrt](https://github.com/lgs2007m/Actions-OpenWrt)
- [XiaoBinin/Actions-immortalwrt](https://github.com/XiaoBinin/Actions-immortalwrt)
- [padavanonly/immortalwrt-mt798x](https://github.com/padavanonly/immortalwrt-mt798x)
- [GitHub Actions](https://github.com/features/actions) 及所有软件包维护者

## 许可

本仓库遵循 [MIT License](LICENSE)。上游项目和集成软件包遵循各自的许可协议。
