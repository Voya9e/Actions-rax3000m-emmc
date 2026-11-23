"""Check that Docker cannot start with its data directory on overlay."""

import importlib.util
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


PATCH = Path(__file__).resolve().parents[1] / "scripts/patch-rax3000m-dockerd.py"
SPEC = importlib.util.spec_from_file_location("dockerd_patch", PATCH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
INIT = """start_service() {
    process_config
    procd_open_instance
}
"""


class DockerStartupTests(unittest.TestCase):
    def test_patch_is_idempotent(self):
        patched = MODULE.patch_source(INIT)
        self.assertEqual(MODULE.patch_source(patched), patched)

    def test_upstream_changes_fail_explicitly(self):
        with self.assertRaises(ValueError):
            MODULE.patch_source("start_service() {\n    changed_config\n}\n")

    def test_data_mount_and_root_are_required(self):
        bash = shutil.which("bash")
        self.assertIsNotNone(bash, "bash is required for Docker startup tests")
        cases = [
            ("/dev/mmcblk0p6 /mnt/data ext4 rw 0 0\n", "/mnt/data/docker", True),
            ("/dev/mmcblk0p6 /mnt/data f2fs rw 0 0\n", "/mnt/data/docker", True),
            ("", "/mnt/data/docker", False),
            ("overlayfs:/overlay /mnt/data overlay rw 0 0\n", "/mnt/data/docker", False),
            ("/dev/sda1 /mnt/data ext4 rw 0 0\n", "/mnt/data/docker", False),
            ("/dev/mmcblk0p6 /data ext4 rw 0 0\n", "/mnt/data/docker", False),
            ("/dev/mmcblk0p6 /mnt/data ext4 rw 0 0\n", "/opt/docker", False),
            ("/dev/mmcblk0p6 /mnt/data ext4 rw 0 0\n", "", False),
        ]
        with tempfile.TemporaryDirectory() as directory:
            mounts = Path(directory) / "mounts"
            for mounted, data_root, expected in cases:
                with self.subTest(mounted=mounted, data_root=data_root):
                    mounts.write_text(mounted)
                    script = MODULE.patch_source(INIT).replace(
                        "/proc/mounts", shlex.quote(mounts.as_posix()))
                    script += """
process_config() { DOCKERD_CONF=/tmp/docker-test.json; }
jsonfilter() { printf '%s' "$test_root"; }
logger() { :; }
procd_open_instance() { started=yes; }
started=no
"""
                    script += f"test_root={shlex.quote(data_root)}\n"
                    script += "if start_service; then status=0; else status=$?; fi\n"
                    script += f'[ "$started" = {"yes" if expected else "no"} ] || exit 10\n'
                    script += f'[ "$status" = {0 if expected else 1} ] || exit 11\n'
                    result = subprocess.run([bash, "-s"], input=script, text=True,
                                            capture_output=True, check=False)
                    self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
