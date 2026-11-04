<div align="center">

# CMCC RAX3000M eMMC

**GitHub Actions 固件编译项目**

为 RAX3000M eMMC 提供三条构建路线：官方 OpenWrt、ImmortalWrt 开源驱动版，以及 ImmortalWrt MTK SDK 版。

[![OpenWrt 25.12](https://img.shields.io/badge/OpenWrt-25.12-00A5E5?logo=openwrt&logoColor=white)](README_openwrt_25.12.md)
[![ImmortalWrt 23.05](https://img.shields.io/badge/ImmortalWrt-23.05-orange)](README_mainline.md)
[![MTK SDK](https://img.shields.io/badge/Wi--Fi-MTK%20SDK-7B61A8)](.github/workflows/build-immortalwrt-mt798x.yml)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

---

## 选择构建路线

| 工作流 | 固件源码 | 无线驱动 | 主要特点 |
|:--|:--|:--|:--|
| **Build OpenWrt 25.12** | OpenWrt 官方 `openwrt-25.12` | 开源 `mt76` | 官方新版 · Linux 6.12 · APK |
| **Build ImmortalWrt** | ImmortalWrt 官方 `openwrt-23.05` | 开源 `mt76` | Linux 5.15 · 独立的配置与软件包集 |
| **Build ImmortalWrt-mt798x** | hanwckf `immortalwrt-mt798x` | MTK SDK `mt_wifi` | Linux 5.4.x · 可选 MTK 无线配置界面 |

> [!IMPORTANT]
> 三条路线的设备镜像、无线驱动和软件包生态不同。请勿跨路线混刷启动文件或内核模块。

## 快速开始

1. 前往仓库的 [Actions](../../actions) 页面。
2. 选择所需工作流并点击 **Run workflow**。
3. 设置该工作流提供的选项，启动构建。
4. 构建完成后，从对应的 [Releases](../../releases) 下载文件。

### 路线说明

- [OpenWrt 25.12 构建说明](README_openwrt_25.12.md)
- [ImmortalWrt 23.05 开源驱动版说明](README_mainline.md)
- [ImmortalWrt MTK SDK 工作流](.github/workflows/build-immortalwrt-mt798x.yml)

## OpenWrt 25.12 发布文件

| 文件 | 用途 |
|:--|:--|
| `*-emmc-ddr3-preloader.bin` | DDR3 eMMC 预加载程序 |
| `*-emmc-ddr3-bl31-uboot.fip` | DDR3 eMMC 的 BL31 与 U-Boot 启动镜像 |
| `*-emmc-gpt.bin` | eMMC GPT 分区布局 |
| `*-emmc-squashfs-sysupgrade.itb` | 系统升级镜像 |
| `*-emmc-initramfs-recovery.itb` | 临时恢复系统镜像 |
| `sha256sums` | 文件完整性校验清单 |

> [!WARNING]
> 本仓库目标设备为 **RAX3000M eMMC DDR3**。DDR4 启动文件不能用于 DDR3 设备。启动文件涉及底层存储写入，刷写前请遵循对应设备和 U-Boot 的说明。

## EEPROM 与 eMMC 频率

**EEPROM：** 各工作流可能提供 NX30 Pro EEPROM 选项。25.12 工作流会将选定的校准数据写入设备树覆盖配置；关闭选项时使用设备 factory 分区中的原厂校准数据。建议先备份本机原厂 EEPROM。第三方校准数据的无线效果会因设备而异。

**eMMC 频率：** 默认使用 26 MHz。部分工作流允许选择 52 MHz，但个别设备在较高频率下可能不稳定。若出现存储 I/O 错误或启动异常，请使用默认频率重新构建。

## 许可与致谢

本仓库遵循 [MIT License](LICENSE)。

感谢 [OpenWrt](https://github.com/openwrt/openwrt)、[ImmortalWrt](https://github.com/immortalwrt/immortalwrt)、[hanwckf/immortalwrt-mt798x](https://github.com/hanwckf/immortalwrt-mt798x)、[lgs2007m/Actions-OpenWrt](https://github.com/lgs2007m/Actions-OpenWrt)、[XiaoBinin/Actions-immortalwrt](https://github.com/XiaoBinin/Actions-immortalwrt)，以及所有软件包和驱动维护者。
