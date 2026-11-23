"""Check latest-image deployment and rollback with a simulated Docker CLI."""

import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SOURCE = (Path(__file__).resolve().parents[1] / "scripts/diy-openwrt-25.12.sh").read_text()
SUPERVISOR = SOURCE.split('cat > "$VIDBEE_SUPERVISOR" <<\'EOF\'\n', 1)[1].split("\nEOF", 1)[0]
FUNCTIONS, LOOP = SUPERVISOR.split("while :; do", 1)
DOCKER = r"""
declare -A images states
log() { :; }
docker() {
    local command="$1" cname fmt
    shift
    case "$command" in
        image) echo new ;;
        container)
            shift
            if [ "${1:-}" = --format ]; then
                fmt="$2"; cname="$3"
                [ -n "${images[$cname]+exists}" ] || return 1
                case "$fmt" in
                    '{{.Image}}') echo "${images[$cname]}" ;;
                    '{{.State.Running}}') echo "${states[$cname]}" ;;
                    *) return 99 ;;
                esac
            else
                [ -n "${images[$1]+exists}" ]
            fi
            ;;
        stop) states[$1]=false ;;
        start) states[$1]=true ;;
        rename)
            images[$2]="${images[$1]}"; states[$2]="${states[$1]}"
            unset 'images[$1]' 'states[$1]'
            ;;
        rm)
            [ "$1" != -f ] || shift
            unset 'images[$1]' 'states[$1]'
            ;;
        run)
            printf '%s\n' "$*" >> "$calls"
            while [ "$1" != --name ]; do shift; done
            cname="$2"
            images[$cname]=new; states[$cname]=true
            [ "$mode" != fail ] || { states[$cname]=false; return 1; }
            ;;
        *) return 99 ;;
    esac
}
"""


class VidBeeImagesTests(unittest.TestCase):
    def shell(self, script):
        bash = shutil.which("bash")
        self.assertIsNotNone(bash)
        return subprocess.run([bash, "-s"], input=script, text=True,
                              capture_output=True, check=False)

    def test_container_replacement_and_recovery(self):
        cases = [
            ("fresh", "", "", False),
            ("current", "new", "true", False),
            ("stopped", "new", "false", False),
            ("outdated", "old", "true", False),
            ("fail", "old", "true", False),
            ("interrupted", "new", "false", True),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for mode, image, running, backup in cases:
                with self.subTest(mode=mode):
                    calls = Path(directory) / mode
                    setup = f"calls={shlex.quote(calls.as_posix())}\nmode={mode}\n"
                    if image:
                        setup += f"images[vidbee-api]={image}\nstates[vidbee-api]={running}\n"
                    if backup:
                        setup += "images[vidbee-api-previous]=old\nstates[vidbee-api-previous]=false\n"
                    check = """
if ensure_container vidbee-api example:latest --volume /data/vidbee/data:/data/vidbee; then
    status=0
else
    status=$?
fi
[ "$status" = EXPECTED_STATUS ] || exit 10
[ "${images[vidbee-api]}" = EXPECTED_IMAGE ] || exit 11
[ "${states[vidbee-api]}" = true ] || exit 12
[ -z "${images[vidbee-api-previous]+exists}" ] || exit 13
"""
                    check = check.replace("EXPECTED_STATUS", "1" if mode == "fail" else "0")
                    check = check.replace("EXPECTED_IMAGE", "old" if mode == "fail" else "new")
                    result = self.shell(FUNCTIONS + DOCKER + setup + check)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    if mode in ("current", "stopped"):
                        self.assertFalse(calls.exists())
                    else:
                        self.assertIn("--volume /data/vidbee/data:/data/vidbee", calls.read_text())

    def test_pull_readiness_and_retry(self):
        # End the main loop immediately after successful pulling to isolate
        # the readiness gate from container creation and network setup.
        loop = LOOP.split("    if ! docker network inspect vidbee", 1)[0] + "    break\ndone\n"
        for mode in ("ready", "web_retry", "wrong_root", "daemon_down"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                calls = Path(directory) / "calls"
                failure = Path(directory) / "failed_once"
                setup = f"calls={shlex.quote(calls.as_posix())}\n"
                setup += f"failure={shlex.quote(failure.as_posix())}\nmode={mode}\n"
                mocks = r"""
log() { :; }
data_is_ready() { return 0; }
dockerd_start() { :; }
sleep() {
    case "$mode" in wrong_root|daemon_down) exit 77;; esac
}
docker() {
    case "$1" in
        info)
            [ "$mode" != daemon_down ] || return 1
            if [ "${2:-}" = --format ]; then
                if [ "$mode" = wrong_root ]; then echo /overlay/docker; else echo /mnt/data/docker; fi
            fi
            ;;
        pull)
            echo "$2" >> "$calls"
            if [ "$mode" = web_retry ] && [ "$2" = "$WEB_IMAGE" ] && [ ! -e "$failure" ]; then
                touch "$failure"
                return 1
            fi
            ;;
        *) return 99 ;;
    esac
}
"""
                loop = loop.replace("/etc/init.d/dockerd start", "dockerd_start")
                result = self.shell(FUNCTIONS + setup + mocks + "while :; do" + loop)
                if mode in ("wrong_root", "daemon_down"):
                    self.assertEqual(result.returncode, 77, result.stderr)
                    self.assertFalse(calls.exists())
                else:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(calls.read_text().splitlines(),
                                     ["ghcr.io/nexmoe/vidbee-api:latest", "ghcr.io/nexmoe/vidbee-web:latest"]
                                     * (2 if mode == "web_retry" else 1))


if __name__ == "__main__":
    unittest.main()
