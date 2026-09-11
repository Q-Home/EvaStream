import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

PHP = os.environ.get('EVA_TEST_PHP') or shutil.which('php')
HELPER = Path(__file__).resolve().parents[1] / 'bin/network.php'


def interface(name, address, up=True, family='inet', scope='global'):
    return {'ifname':name, 'flags':['UP'] if up else [],
            'addr_info':[{'family':family,'scope':scope,'local':address}]}


@unittest.skipUnless(PHP, 'PHP CLI required')
class NetworkTests(unittest.TestCase):
    def detect(self, interfaces):
        code = 'require $argv[1]; echo json_encode(eva_lan_addresses(json_decode(stream_get_contents(STDIN),true)));'
        result = subprocess.run([PHP, '-r', code, str(HELPER)], input=json.dumps(interfaces),
                                text=True, capture_output=True, check=True, timeout=10)
        return json.loads(result.stdout)

    def test_eth0_precedes_eth1_regardless_of_order(self):
        self.assertEqual(self.detect([interface('eth1','192.0.2.20'),interface('eth0','192.0.2.10')]),
                         [{'interface':'eth0','address':'192.0.2.10'}, {'interface':'eth1','address':'192.0.2.20'}])

    def test_eth1_is_available_without_eth0(self):
        self.assertEqual(self.detect([interface('eth0','192.0.2.10',up=False),interface('eth1','192.0.2.20')]),
                         [{'interface':'eth1','address':'192.0.2.20'}])

    def test_vpn_loopback_and_ipv6_are_not_candidates(self):
        self.assertEqual(self.detect([interface('tun0','192.0.2.30'),interface('wg0','192.0.2.31'),
            interface('tailscale0','192.0.2.32'),interface('lo','127.0.0.1'),
            interface('eth0','2001:db8::1',family='inet6'),interface('eth1','169.254.1.2',scope='link')]), [])

    def test_missing_invalid_and_duplicate_addresses(self):
        self.assertEqual(self.detect([]), [])
        self.assertEqual(self.detect([{},interface('eth0','bad-address')]), [])
        record=interface('eth0','192.0.2.10')
        self.assertEqual(len(self.detect([record,record])),1)


if __name__ == '__main__':
    unittest.main()
