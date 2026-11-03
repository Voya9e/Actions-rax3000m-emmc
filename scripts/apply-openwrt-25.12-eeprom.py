#!/usr/bin/env python3
"""Replace the RAX3000M eMMC DTS EEPROM cell with the selected EEPROM bytes."""

from pathlib import Path
import re
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: apply-openwrt-25.12-eeprom.py EEPROM_BIN DEVICE_DTso")

eeprom_path = Path(sys.argv[1])
dtso_path = Path(sys.argv[2])
data = eeprom_path.read_bytes()

# The RAX3000M Wi-Fi EEPROM NVMEM cell is 0x1000 bytes at factory offset 0.
if len(data) < 0x1000:
    raise SystemExit(f"EEPROM file is too short: {len(data)} bytes; need at least 4096")

pattern = re.compile(
    r'(?m)^([ \t]*)nvmem-cells = <&eeprom_factory_0>;\r?\n'
    r'\1nvmem-cell-names = "eeprom";[ \t]*$'
)
source = dtso_path.read_text(encoding="utf-8")
matches = list(pattern.finditer(source))
if len(matches) != 1:
    raise SystemExit(
        f"Expected one RAX3000M EEPROM NVMEM reference in {dtso_path}; "
        f"found {len(matches)}"
    )

indent = matches[0].group(1)
lines = [f"{indent}mediatek,eeprom-data = ["]
for offset in range(0, 0x1000, 16):
    chunk = data[offset : offset + 16]
    lines.append(f"{indent}\t" + " ".join(f"{byte:02x}" for byte in chunk))
lines.append(f"{indent}];")
replacement = "\n".join(lines)

updated, count = pattern.subn(lambda _match: replacement, source, count=1)
if count != 1:
    raise SystemExit("Could not insert EEPROM data into the device tree overlay")

dtso_path.write_text(updated, encoding="utf-8")
print(f"Inserted first 4096 bytes of {eeprom_path.name} into the eMMC Wi-Fi calibration node")
