"""Exercise bridge discovery and persistent rules without changing a firewall."""

import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/vidbee-firewall.sh"
NETWORK_ID = "123456789abc" + "0" * 52
MOCKS = r"""
docker() {
    case "$*" in
        *'{{.Driver}}'*) printf '%s' "$driver" ;;
        *'{{.Id}}'*) printf '%s' "$network_id" ;;
        *) printf '%s' "$bridge_name" ;;
    esac
}
logger() { :; }
uci() {
    shift
    local command="$1" arg="$2" key value file found=no
    case "$command" in
        set)
            key="${arg%%=*}"
            value="${arg#*=}"
            printf '%s' "$value" > "$db/$key"
            ;;
        show)
            for file in "$db/$arg" "$db/$arg."*; do
                [ -f "$file" ] || continue
                found=yes
                printf '%s=%s\n' "${file##*/}" "$(cat "$file")"
            done
            [ "$found" = yes ]
            ;;
        commit) : ;;
        *) return 99 ;;
    esac
}
reload_firewall() {
    echo reload >> "$db/reloads"
    [ "$reload_result" = success ]
}
"""


class VidBeeFirewallTests(unittest.TestCase):
    def run_script(self, directory, bridge="", driver="bridge", network_id=NETWORK_ID,
                   reload="success", twice=False):
        bash = shutil.which("bash")
        self.assertIsNotNone(bash)
        root = Path(directory)
        db = root / "db"
        db.mkdir(exist_ok=True)
        source = SCRIPT.read_text().replace(
            "/etc/init.d/firewall reload", "reload_firewall").replace(
            "applied_file=/var/run/vidbee-firewall.applied",
            f"applied_file={shlex.quote((root / 'applied').as_posix())}")
        setup = MOCKS + "\n".join(
            f"{key}={shlex.quote(value)}" for key, value in {
                "db": db.as_posix(), "driver": driver, "network_id": network_id,
                "bridge_name": bridge, "reload_result": reload,
            }.items()) + "\n"
        return subprocess.run([bash, "-s"], input=setup + source + (source if twice else ""),
                              capture_output=True, text=True, check=False)

    def test_generated_bridge_rules_and_idempotence(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_script(directory, twice=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            db = Path(directory) / "db"
            expected = {
                "firewall.rax3000m_vidbee_zone.device": "br-123456789abc",
                "firewall.rax3000m_vidbee_lan.src": "lan",
                "firewall.rax3000m_vidbee_lan.dest": "vidbee",
                "firewall.rax3000m_vidbee_lan.proto": "tcp",
                "firewall.rax3000m_vidbee_lan.dest_port": "3000 3100",
                "firewall.rax3000m_vidbee_lan.target": "ACCEPT",
                "firewall.rax3000m_vidbee_wan.src": "vidbee",
                "firewall.rax3000m_vidbee_wan.dest": "wan",
            }
            for key, value in expected.items():
                self.assertEqual((db / key).read_text(), value)
            self.assertEqual((db / "reloads").read_text().splitlines(), ["reload"])

    def test_named_bridge_and_changed_network(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(self.run_script(directory, bridge="br-vidbee").returncode, 0)
            result = self.run_script(directory, bridge="br-vidbee2")
            self.assertEqual(result.returncode, 0, result.stderr)
            db = Path(directory) / "db"
            self.assertEqual((db / "firewall.rax3000m_vidbee_zone.device").read_text(), "br-vidbee2")
            self.assertEqual(len((db / "reloads").read_text().splitlines()), 2)

    def test_reload_failure_is_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertNotEqual(self.run_script(directory, reload="fail").returncode, 0)
            self.assertFalse((Path(directory) / "applied").exists())
            self.assertEqual(self.run_script(directory).returncode, 0)
            self.assertTrue((Path(directory) / "applied").exists())

    def test_unsupported_network_is_refused_before_writing_rules(self):
        for options in [{"driver": "host"}, {"bridge": "br-*"},
                        {"network_id": "invalid"}, {"bridge": "x" * 16}]:
            with self.subTest(options=options), tempfile.TemporaryDirectory() as directory:
                self.assertNotEqual(self.run_script(directory, **options).returncode, 0)
                self.assertEqual(list((Path(directory) / "db").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
