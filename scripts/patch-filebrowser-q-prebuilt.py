#!/usr/bin/env python3
"""Use the pinned ARM64 FileBrowser Quantum release binary without invoking Go."""

from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch-filebrowser-q-prebuilt.py OPENWRT_SOURCE")

makefile = Path(sys.argv[1]) / "feeds/jell/filebrowser-q/Makefile"
source = makefile.read_text(encoding="utf-8")

# Pin the upstream ARM64 release asset and its SHA-256.
source, n = re.subn(
    r"(?m)^PKG_SOURCE:=.*\nPKG_SOURCE_URL:=.*\nPKG_HASH:=.*$",
    "PKG_SOURCE:=linux-arm64-filebrowser\n"
    "PKG_SOURCE_URL:=https://github.com/gtsteffaniak/filebrowser/releases/download/v$(PKG_VERSION)\n"
    "PKG_HASH:=03eac074efc1b0ef3cb39882c04eeee26027049d261b6b6706650d4ac2d8e21c",
    source,
    count=1,
)
if n != 1:
    raise SystemExit(f"Expected one FileBrowser source block in {makefile}; found {n}")

# Remove the Go package integration and its build dependencies, if present.
source, n = re.subn(
    r"(?ms)^PKG_BUILD_DEPENDS:=.*?^(?=include \$\(INCLUDE_DIR\)/package\.mk)",
    "",
    source,
    count=1,
)
# A previously patched Makefile has no Go block; in either case remove any
# remaining Go include and architecture dependency.
source = re.sub(
    r"(?m)^include \$\(TOPDIR\)/feeds/packages/lang/golang/golang-package\.mk\n?",
    "",
    source,
)
source = source.replace("  DEPENDS:=$(GO_ARCH_DEPENDS)\n", "")
source = source.replace("PKG_LICENSE_FILES:=LICENSE\n", "")

# Copy the already-built ARM64 executable into the package build directory.
# The explicit ':' recipe prevents package.mk from falling back to Go compile.
source, n = re.subn(
    r"(?ms)^define Build/Prepare\n.*?^endef\n\n^define Build/Compile\n.*?^endef",
    "define Build/Prepare\n"
    "\tmkdir -p $(PKG_BUILD_DIR)\n"
    "\tcp $(DL_DIR)/$(PKG_SOURCE) $(PKG_BUILD_DIR)/filebrowser\n"
    "endef\n\n"
    "define Build/Compile\n"
    "\t:\n"
    "endef",
    source,
    count=1,
)
if n != 1:
    raise SystemExit(f"Expected one prepare/compile block in {makefile}; found {n}")

if "golang-package.mk" in source or "GO_PKG" in source or "go build" in source:
    raise SystemExit("Go build configuration remains in the patched FileBrowser Makefile")
if not re.search(r"(?ms)^define Build/Compile\n\t:\nendef", source):
    raise SystemExit("FileBrowser compile target is not an explicit no-op")

makefile.write_text(source, encoding="utf-8")
print("Patched FileBrowser Quantum to install the pinned ARM64 release binary without Go compilation")
