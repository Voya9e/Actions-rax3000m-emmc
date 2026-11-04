<div align="center">

# CMCC RAX3000M eMMC

### GitHub Actions 固件编译项目

面向 RAX3000M eMMC 的三条构建路线：官方 OpenWrt、ImmortalWrt 开源驱动版，以及 ImmortalWrt MTK SDK 版。

</div>

## 构建路线

| GitHub Actions 工作流 | 固件源码 | 无线驱动 | 主要特点 |
| --- | --- | --- | --- |
| **Build OpenWrt 25.12** | OpenWrt 官方 `openwrt-25.12` | 开源 `mt76` | 官方新版；内核 6.12；软件包管理器为 APK |
| **Build ImmortalWrt** | ImmortalWrt 官方 `openwrt-23.05` | 开源 `mt76` | ImmortalWrt 23.05；内核 5.15；构建配置和软件包集不同于 25.12 |
| **Build ImmortalWrt-mt798x** | hanwckf `immortalwrt-mt798x` | MTK SDK `mt_wifi` | 内核 5.4.x；可选 MTK SDK 无线配置界面 |

三条路线的设备镜像、无线驱动和软件包生态不同。不要跨路线混刷启动文件或内核模块。

## 快速编译

1. 打开仓库 [Actions](../../actions) 页面。
2. 选择需要的工作流。
3. 点击 **Run workflow**，设置该工作流提供的选项。
4. 等待构建完成后，从对应 [Release](../../releases) 获取文件。

各路线的详细说明：

- [OpenWrt 25.12 构建说明](README_openwrt_25.12.md)
- [ImmortalWrt 23.05 开源驱动版说明](README_mainline.md)
- [ImmortalWrt MTK SDK 工作流](.github/workflows/build-immortalwrt-mt798x.yml)

## OpenWrt 25.12 发布文件

25.12 工作流为 eMMC 设备整理并发布以下文件：

- `*-emmc-ddr3-preloader.bin`、`*-emmc-ddr3-bl31-uboot.fip`：DDR3 eMMC 启动文件。
- `*-emmc-gpt.bin`：eMMC 分区布局文件。
- `*-emmc-squashfs-sysupgrade.itb`：系统升级镜像。
- `*-emmc-initramfs-recovery.itb`：临时恢复系统镜像。
- `sha256sums`：校验清单。

本仓库目标设备是 **RAX3000M eMMC DDR3**。DDR4 变体启动文件不可用于 DDR3 设备。启动文件写入涉及底层存储，刷写前请按设备和 U-Boot 的对应说明操作。

## EEPROM 与 eMMC 频率

各工作流可提供 NX30 Pro EEPROM 选项；25.12 工作流会把选择的校准数据写入设备树覆盖配置。关闭该选项时使用设备 factory 分区中的原厂校准数据。建议保留并备份本机原厂 EEPROM；第三方校准数据的无线效果因设备而异。

eMMC 默认频率为 26 MHz，部分工作流允许选择 52 MHz。较高频率可能在个别设备上不稳定；若出现存储 I/O 错误或启动问题，应使用默认频率构建。

## 许可与致谢

本仓库使用 [MIT License](LICENSE)。感谢 [OpenWrt](https://github.com/openwrt/openwrt)、[ImmortalWrt](https://github.com/immortalwrt/immortalwrt)、[hanwckf/immortalwrt-mt798x](https://github.com/hanwckf/immortalwrt-mt798x)、[lgs2007m/Actions-OpenWrt](https://github.com/lgs2007m/Actions-OpenWrt)、[XiaoBinin/Actions-immortalwrt](https://github.com/XiaoBinin/Actions-immortalwrt)，以及所有软件包和驱动维护者。
