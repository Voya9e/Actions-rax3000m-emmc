"""Exercise partition planning against sfdisk dumps without touching a disk."""

import shutil
import subprocess
import unittest
from pathlib import Path


PLANNER = Path(__file__).resolve().parents[1] / "scripts/plan-rax3000m-data.awk"
DISK_SECTORS = 122126336
KERNEL_LAYOUT = "8192:1024;9216:4096;13312:8192;24576:65536;131072:1048576;"
LAYOUT = """label: gpt
label-id: 12345678-1234-1234-1234-123456789abc
device: /dev/mmcblk0
unit: sectors
first-lba: 34
last-lba: 1179647
sector-size: 512

/dev/mmcblk0p1 : start=8192, size=1024, type=83, name="ubootenv"
/dev/mmcblk0p2 : start=9216, size=4096, type=83, name="factory"
/dev/mmcblk0p3 : start=13312, size=8192, type=EF, name="fip"
/dev/mmcblk0p4 : start=24576, size=65536, type=EF, name="recovery"
/dev/mmcblk0p5 : start=131072, size=1048576, type=2E, name="production"
/dev/mmcblk0p128 : start=34, size=8158, type=83
"""


class DataPartitionPlanTests(unittest.TestCase):
    def plan(self, layout=LAYOUT, sectors=DISK_SECTORS, kernel=KERNEL_LAYOUT):
        awk = shutil.which("awk")
        if not awk:
            self.fail("awk is required to test the firmware partition planner")
        return subprocess.run(
            [awk, "-v", f"disk_sectors={sectors}", "-v", f"kernel_layout={kernel}",
             "-f", str(PLANNER)],
            input=layout, text=True, capture_output=True, check=False,
        )

    def assert_refused(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr)

    def test_standard_layout_uses_unused_tail(self):
        result = self.plan()
        self.assertEqual(result.returncode, 0, result.stderr)
        start, size = map(int, result.stdout.split())
        self.assertEqual(start, 1179648)
        self.assertEqual(start % 2048, 0)
        self.assertEqual(size % 2048, 0)
        self.assertLessEqual(start + size, DISK_SECTORS - 2048)

    def test_existing_448_mib_production_is_preserved(self):
        result = self.plan(
            LAYOUT.replace("size=1048576", "size=917504"),
            kernel=KERNEL_LAYOUT.replace("131072:1048576", "131072:917504"),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(int(result.stdout.split()[0]), 1048576)

    def test_reserved_partition_is_optional(self):
        layout = "\n".join(line for line in LAYOUT.splitlines() if "mmcblk0p128" not in line)
        self.assertEqual(self.plan(layout).returncode, 0)

    def test_existing_partition_six_is_refused(self):
        self.assert_refused(self.plan(LAYOUT + '/dev/mmcblk0p6 : start=1263616, size=10000, name="data"\n'))

    def test_other_partition_is_refused(self):
        self.assert_refused(self.plan(LAYOUT + '/dev/mmcblk0p7 : start=1263616, size=10000, name="other"\n'))

    def test_kernel_and_gpt_mismatch_is_refused(self):
        self.assert_refused(self.plan(kernel=KERNEL_LAYOUT.replace("131072:1048576", "131072:917504")))

    def test_unsupported_layout_is_refused(self):
        for old, new in [("label: gpt", "label: dos"), ("sector-size: 512", "sector-size: 4096"),
                         ('name="factory"', 'name="unknown"'), ("start=34, size=8158", "start=34, size=20000")]:
            with self.subTest(new=new):
                self.assert_refused(self.plan(LAYOUT.replace(old, new)))

    def test_missing_boot_partition_is_refused(self):
        layout = "\n".join(line for line in LAYOUT.splitlines() if "mmcblk0p2" not in line)
        self.assert_refused(self.plan(layout))

    def test_duplicate_entry_is_refused(self):
        self.assert_refused(self.plan(LAYOUT + '/dev/mmcblk0p1 : start=8192, size=1024, name="ubootenv"\n'))

    def test_small_free_tail_is_refused(self):
        self.assert_refused(self.plan(sectors=5000000))

    def test_invalid_disk_size_is_refused(self):
        for size in ["", "invalid", "123456;bad"]:
            with self.subTest(size=size):
                self.assert_refused(self.plan(sectors=size))


if __name__ == "__main__":
    unittest.main()
