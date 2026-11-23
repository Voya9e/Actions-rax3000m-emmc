#!/usr/bin/env python3
"""Require the eMMC data mount before starting the packaged Docker daemon."""

import re
import sys
from pathlib import Path


MARKER = "# Require the RAX3000M data mount before starting Docker."
GUARD = """\t# Require the RAX3000M data mount before starting Docker.
\tif [ "$(jsonfilter -i "$DOCKERD_CONF" -e '@["data-root"]' 2>/dev/null)" != /mnt/data/docker ] \\
\t\t|| ! awk '$1 == "/dev/mmcblk0p6" && $2 == "/mnt/data" { found = 1 } END { exit !found }' /proc/mounts; then
\t\tlogger -t dockerd-init "Docker requires /mnt/data on the eMMC data partition and data-root=/mnt/data/docker"
\t\treturn 1
\tfi
"""


def patch_source(source: str) -> str:
    if MARKER in source:
        return source
    function = re.search(r"^start_service\(\) \{\n.*?^\}\n", source, re.MULTILINE | re.DOTALL)
    if function is None:
        raise ValueError("Could not find dockerd start_service")
    body, count = re.subn(r"(^[ \t]*process_config[ \t]*\n)",
                          lambda match: match.group(0) + GUARD,
                          function.group(0), count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError("Could not find Docker configuration generation before startup")
    return source[:function.start()] + body + source[function.end():]


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch-rax3000m-dockerd.py OPENWRT_SOURCE")
    path = Path(sys.argv[1]) / "feeds/packages/utils/dockerd/files/dockerd.init"
    path.write_text(patch_source(path.read_text()))


if __name__ == "__main__":
    main()
