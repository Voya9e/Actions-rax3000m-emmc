#!/usr/bin/env python3
"""Use the feed-selected ARM64 FileBrowser Quantum release binary without Go."""

from pathlib import Path
import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

if len(sys.argv) != 2:
    raise SystemExit("usage: patch-filebrowser-q-prebuilt.py OPENWRT_SOURCE")


def apk_version_from_release_tag(release_tag: str) -> str:
    """Convert a FileBrowser release tag to APK's Alpine-style version syntax."""
    match = re.fullmatch(
        r"(?P<base>[0-9]+(?:\.[0-9]+)*)(?:-(?P<suffix>stable|alpha|beta|pre|rc)(?:[.-]?(?P<number>[0-9]+))?)?",
        release_tag,
        flags=re.IGNORECASE,
    )
    if not match:
        raise SystemExit(
            f"Unsupported FileBrowser release tag {release_tag!r}; "
            "expected a numeric version with optional stable/alpha/beta/pre/rc suffix"
        )

    base = match.group("base")
    suffix = match.group("suffix")
    number = match.group("number") or ""
    if not suffix or suffix.lower() == "stable":
        return base
    return f"{base}_{suffix.lower()}{number}"


def github_asset_sha256(release_tag: str, asset_name: str) -> str:
    """Read GitHub's published SHA-256 digest for the named release asset."""
    tag = f"v{release_tag}"
    api_url = (
        "https://api.github.com/repos/gtsteffaniak/filebrowser/releases/tags/"
        f"{quote(tag, safe='')}"
    )
    request = Request(
        api_url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Actions-rax3000m-emmc",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            release = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read GitHub release metadata for {tag}: {exc}") from exc

    if release.get("tag_name") != tag:
        raise SystemExit(
            f"GitHub returned release tag {release.get('tag_name')!r}, expected {tag!r}"
        )
    assets = [asset for asset in release.get("assets", []) if asset.get("name") == asset_name]
    if len(assets) != 1:
        raise SystemExit(
            f"Expected one {asset_name!r} asset in GitHub release {tag}; found {len(assets)}"
        )
    digest = assets[0].get("digest")
    if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-fA-F]{64}", digest):
        raise SystemExit(f"GitHub release asset {asset_name!r} in {tag} has no valid SHA-256 digest")
    return digest.removeprefix("sha256:").lower()


makefile = Path(sys.argv[1]) / "feeds/jell/filebrowser-q/Makefile"
source = makefile.read_text(encoding="utf-8")

version_match = re.search(r"(?m)^PKG_VERSION:=([^\r\n]+)$", source)
if not version_match:
    raise SystemExit(f"Expected one literal PKG_VERSION declaration in {makefile}")
upstream_version = version_match.group(1).strip()
apk_version = apk_version_from_release_tag(upstream_version)
asset_name = "linux-arm64-filebrowser"
asset_sha256 = github_asset_sha256(upstream_version, asset_name)

# Select the upstream ARM64 release asset and take its checksum from GitHub's
# release metadata so source upgrades do not require a hard-coded hash change.
source, n = re.subn(
    r"(?m)^PKG_SOURCE:=.*\nPKG_SOURCE_URL:=.*\nPKG_HASH:=.*$",
    f"PKG_SOURCE:={asset_name}\n"
    "PKG_SOURCE_URL:=https://github.com/gtsteffaniak/filebrowser/releases/download/v$(PKG_UPSTREAM_VERSION)\n"
    f"PKG_HASH:={asset_sha256}",
    source,
    count=1,
)
if n != 1:
    raise SystemExit(f"Expected one FileBrowser source block in {makefile}; found {n}")

# Keep the feed's upstream tag for downloading, but use an APK-compatible
# version in package metadata. Stable tags lose their label; known prerelease
# labels use Alpine/APK's underscore suffix notation.
source, n = re.subn(
    r"(?m)^PKG_VERSION:=.*$",
    f"PKG_VERSION:={apk_version}\nPKG_UPSTREAM_VERSION:={upstream_version}",
    source,
    count=1,
)
if n != 1:
    raise SystemExit(f"Expected one FileBrowser version declaration in {makefile}; found {n}")

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
print(
    "Patched FileBrowser Quantum version "
    f"{upstream_version} as APK version {apk_version}; "
    f"using GitHub SHA-256 {asset_sha256} and installing the ARM64 binary without Go compilation"
)
