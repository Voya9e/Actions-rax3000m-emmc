#!/usr/bin/env python3
"""Make Argon and Footstrap settings menus follow the active LuCI theme."""

from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: apply-openwrt-25.12-theme-menu.py OPENWRT_SOURCE")

root = Path(sys.argv[1])


def replace_once(relative_path: str, old: str, new: str) -> None:
    path = root / relative_path
    source = path.read_text(encoding="utf-8")
    count = source.count(old)
    if count != 1:
        raise SystemExit(
            f"Expected one patch target in {path}, found {count}; "
            "upstream source may have changed"
        )
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


replace_once(
    "feeds/footstrap/luci-theme-footstrap/root/usr/share/luci/menu.d/"
    "luci-theme-footstrap.json",
    '''\t\t"depends": {
\t\t\t"acl": [ "luci-theme-footstrap" ]
\t\t}''',
    '''\t\t"depends": {
\t\t\t"acl": [ "luci-theme-footstrap" ],
\t\t\t"uci": {
\t\t\t\t"luci": {
\t\t\t\t\t"main": { "mediaurlbase": "/luci-static/footstrap" }
\t\t\t\t}
\t\t\t}
\t\t}''',
)

# The build installs Argon from the small feed, so patch its actual source path.
replace_once(
    "feeds/small/luci-theme-argon/root/usr/share/luci/menu.d/"
    "luci-app-argon-config.json",
    '''"uci": { "argon": true }''',
    '''"uci": {
\t\t\t\t"argon": true,
\t\t\t\t"luci": {
\t\t\t\t\t"main": { "mediaurlbase": "/luci-static/argon" }
\t\t\t\t}
\t\t\t}''',
)

replace_once(
    "feeds/luci/modules/luci-base/ucode/dispatcher.uc",
    '''cachefile = sprintf('%s.%08x.json', indexcache, hash_filelist(files));''',
    '''// Include the selected theme in the menu cache key because menu entries
\t\t// may depend on luci.main.mediaurlbase.
\t\tlet active_theme = uci.get('luci', 'main', 'mediaurlbase') || '';
\t\tcachefile = sprintf('%s.%08x.json', indexcache,
\t\t\thash(active_theme, hash_filelist(files)));''',
)

print("Added active-theme dependencies and theme-aware LuCI menu caching")
