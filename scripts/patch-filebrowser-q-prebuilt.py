
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


package_dir = Path(sys.argv[1]) / "feeds/kiddin9/filebrowser-q"
makefile = package_dir / "Makefile"
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

# Install a one-shot first-start helper. It changes only a newly initialized
# database; existing installations and their credentials are left untouched.
bootstrap = package_dir / "files/filebrowser.bootstrap"
bootstrap.parent.mkdir(parents=True, exist_ok=True)
bootstrap.write_text(
    """#!/bin/sh
set -eu

CONF_PATH=/etc/filebrowser-q/config.yaml
PENDING=/etc/filebrowser-q/.admin-password-pending
PORT=${1:-8787}

[ -e "$PENDING" ] || exit 0

attempt=0
while [ "$attempt" -lt 300 ]; do
    if wget -q -O /dev/null "http://127.0.0.1:${PORT}/health"; then
        break
    fi
    attempt=$((attempt + 1))
    sleep 1
done
[ "$attempt" -lt 300 ] || exit 1

/usr/bin/filebrowser-q -c "$CONF_PATH" user set admin --password admin
sed -i '/^[[:space:]]*adminPassword:/d' "$CONF_PATH"
rm -f "$PENDING"
""",
    encoding="utf-8",
    newline="\n",
)

# Add the helper to the feed package without bringing back the old template
# files or any Go build integration.
package_makefile = makefile.read_text(encoding="utf-8")
if "filebrowser-q-bootstrap" not in package_makefile:
    package_makefile, n = re.subn(
        r"(?m)^(\s*\$\(INSTALL_BIN\).*filebrowser\.init.*)$",
        r"\1\n\t$(INSTALL_DIR) $(1)/usr/libexec\n"
        "\t$(INSTALL_BIN) $(CURDIR)/files/filebrowser.bootstrap $(1)/usr/libexec/filebrowser-q-bootstrap",
        package_makefile,
        count=1,
    )
    if n != 1:
        raise SystemExit("Could not find the FileBrowser init-script install rule in the feed Makefile")
    makefile.write_text(package_makefile, encoding="utf-8")

init_script = package_dir / "files/filebrowser.init"
init_source = init_script.read_text(encoding="utf-8")
if "admin-password-pending" not in init_source:
    # Generate a private temporary password so upstream does not interpret
    # the literal default password as a request to force a password change.
    init_source, n = re.subn(
        r'(?m)^\s*if \[ ! -f "\$CONF_PATH" \]; then\s*$',
        '      if [ ! -f "$CONF_PATH" ]; then\n'
        '          bootstrap_password="$(hexdump -n 16 -e \'16/1 "%02x"\' /dev/urandom 2>/dev/null)"\n'
        '          [ "${#bootstrap_password}" -eq 32 ] || return 1',
        init_source,
        count=1,
    )
    if n != 1:
        raise SystemExit("Could not locate the fresh-config branch in filebrowser.init")

    init_source, n = re.subn(
        r'(?m)^\s*adminPassword: "admin"\s*$',
        '        adminPassword: "$bootstrap_password"',
        init_source,
        count=1,
    )
    if n != 1:
        raise SystemExit("Could not locate the initial admin password in filebrowser.init")

    init_source, n = re.subn(
        r'(?m)^(\s*EOF\s*)$',
        r'\1\n          chmod 600 "$CONF_PATH"\n'
        '          if [ ! -s "$DB_PATH" ]; then\n'
        '              touch /etc/filebrowser-q/.admin-password-pending\n'
        '          fi',
        init_source,
        count=1,
    )
    if n != 1:
        raise SystemExit("Could not locate the generated config heredoc terminator in filebrowser.init")

    init_source, n = re.subn(
        r'(?m)^(\s*procd_close_instance\s*)$',
        r'\1\n\n'
        '      procd_open_instance admin_password\n'
        '      procd_set_param command /usr/libexec/filebrowser-q-bootstrap "$listen_port"\n'
        '      procd_set_param stdout 1\n'
        '      procd_set_param stderr 1\n'
        '      procd_close_instance',
        init_source,
        count=1,
    )
    if n != 1:
        raise SystemExit("Could not locate the FileBrowser procd instance in filebrowser.init")

    init_script.write_text(init_source, encoding="utf-8", newline="\n")

print(
    "Patched FileBrowser Quantum version "
    f"{upstream_version} as APK version {apk_version}; "
    f"using GitHub SHA-256 {asset_sha256} and selecting the ARM64 binary without Go compilation; "
    "fresh installs will initialize the admin password to admin"
)

