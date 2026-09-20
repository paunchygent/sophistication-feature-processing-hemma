from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MACOS = ROOT / "macos"
PORTS = (13000, 13001, 15174, 18085, 19000, 19100, 28085)


class SharedTunnelTests(unittest.TestCase):
    def test_shared_tunnel_owns_each_persistent_forward_once(self):
        script = (MACOS / "hemma-shared-tunnel.sh").read_text()

        self.assertEqual(script.count("exec /usr/bin/ssh"), 1)
        self.assertEqual(script.count("-L 127.0.0.1:"), len(PORTS))
        for port in PORTS:
            self.assertIn(f"-L 127.0.0.1:{port}:", script)

    def test_workshop_shortcut_never_creates_a_second_ssh_connection(self):
        script = (MACOS / "Workshop-Tunnel.command").read_text()

        self.assertNotIn("/usr/bin/ssh", script)
        self.assertNotIn(" -L ", script)
        self.assertIn("com.paunchygent.hemma-shared-tunnel", script)

    def test_launch_agent_is_the_single_restart_owner(self):
        plist = (MACOS / "com.paunchygent.hemma-shared-tunnel.plist.in").read_text()
        installer = (MACOS / "Install-Hemma-Shared-Tunnel.command").read_text()

        self.assertIn("<key>KeepAlive</key>", plist)
        self.assertIn("<key>RunAtLoad</key>", plist)
        for label in (
            "com.hemma.huleedu-tunnel",
            "com.hemma.gpu-tunnel",
            "com.hemma.sir-convert-a-lot-tunnel",
        ):
            self.assertIn(label, installer)


if __name__ == "__main__":
    unittest.main()
