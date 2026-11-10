#!/usr/bin/env python3
"""Switch the jell FileBrowser Quantum package to its pinned ARM64 release binary."""

from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch-filebrowser-q-prebuilt.py OPENWRT_SOURCE")

makefile = Path(sys.argv[1]) / "feeds/jell/filebrowser-q/Makefile"
source = makefile.read_text(encoding="utf-8")

if "PKG_SOURCE:=linux-arm64-filebrowser" in source:
    print("FileBrowser Quantum already uses the pinned ARM64 release binary")
    raise SystemExit(0)

source, n = re.subn(
    r"PKG_SOURCE:=\$\(PKG_NAME\)-\$\(PKG_VERSION\)\.tar\.gz\n"
    r"PKG_SOURCE_URL:=https://codeload\.github\.com/gtsteffaniak/filebrowser/tar\.gz/v\$\(PKG_VERSION\)\?\n"
    r"PKG_HASH:=skip",
    "PKG_SOURCE:=linux-arm64-filebrowser\n"
    "PKG_SOURCE_URL:=https://github.com/gtsteffaniak/filebrowser/releases/download/v$(PKG_VERSION)\n"
    "PKG_HASH:=03eac074efc1b0ef3cb39882c04eeee26027049d261b6b6706650d4ac2d8e21c",
    source,
)
if n != 1:
    raise SystemExit(f"Expected one FileBrowser source block in {makefile}; found {n}")

source, n = re.subn(
    r"PKG_BUILD_DEPENDS:=golang/host node/host\n"
    r"PKG_BUILD_PARALLEL:=1\n"
    r"PKG_BUILD_FLAGS:=no-mips16\n\n"
    r"GO_PKG:=.*?\n"
    r"\t\$\(GO_PKG\)/internal/version.CommitSHA=\$\(PKG_VERSION\)\n\n"
    r"include \$\(INCLUDE_DIR\)/package.mk\n"
    r"include \$\(TOPDIR\)/feeds/packages/lang/golang/golang-package.mk",
    "PKG_BUILD_PARALLEL:=1\n"
    "PKG_LICENSE:=Apache-2.0\n\n"
    "include $(INCLUDE_DIR)/package.mk",
    source,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit(f"Expected one Go build configuration block in {makefile}; found {n}")

source = source.replace("PKG_LICENSE_FILES:=LICENSE\n", "")

source, n = re.subn(
    r"define Build/Prepare\n.*?endef\n\ndefine Build/Compile\n.*?endef",
    "define Build/Prepare\n"
    "\tmkdir -p $(PKG_BUILD_DIR)\n"
    "\tcp $(DL_DIR)/$(PKG_SOURCE) $(PKG_BUILD_DIR)/filebrowser\n"
    "endef\n\n"
    "define Build/Compile\n"
    "endef",
    source,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit(f"Expected one prepare/compile block in {makefile}; found {n}")

makefile.write_text(source, encoding="utf-8")
print("Patched FileBrowser Quantum to use the verified v2.0.2-stable ARM64 release binary")
