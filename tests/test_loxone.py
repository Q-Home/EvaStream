import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

import test_php_bridge as php_test
PHP, ROOT = php_test.PHP, php_test.ROOT

TOKEN = 'a' * 64  # Fixed test-only key, never installed.


@unittest.skipUnless(PHP, 'PHP CLI required')
class LoxoneTests(unittest.TestCase):
    def setUp(self):
        php_test.PHPBridgeTests.setUp(self)
        self.settings = self.path / 'settings.json'
        self.config = {'host': '192.0.2.18', 'preview': True,
                       'loxone_enabled': True, 'loxone_token': TOKEN}
        self.settings.write_text(json.dumps(self.config))
        source = ROOT / 'webfrontend/html/loxone.php'
        (self.path / 'loxone.php').write_text(source.read_text(encoding='utf-8'), encoding='utf-8')
        (self.path / 'gateway.php').write_text('''<?php
$_SERVER['REQUEST_METHOD'] = 'GET';
$_GET = json_decode(stream_get_contents(STDIN), true);
require __DIR__ . '/loxone.php';
''', encoding='utf-8')

    def gateway(self, query):
        env = dict(os.environ, EVA_TEST_BIN=str(self.bin), EVA_TEST_PYTHON=sys.executable)
        r = subprocess.run([PHP, '-d', 'include_path=' + str(self.path), str(self.path / 'gateway.php')],
                           input=json.dumps(query), text=True, capture_output=True,
                           timeout=20, check=True, env=env)
        return r.stdout

    def fake_bridge(self, reply):
        # Capture what PHP actually sends, then return a controller fixture.
        (self.bin / 'bridge.py').write_text(
            'import json,sys\nfrom pathlib import Path\n'
            'Path(sys.argv[1]+".request").write_text(sys.stdin.read())\n'
            'print(' + repr(json.dumps(reply)) + ')\n', encoding='utf-8')

    def test_authentication_and_disable(self):
        self.fake_bridge({'ok': True})
        for query in ({}, {'token':'wrong'}, {'token': [TOKEN]}):
            self.assertFalse(json.loads(self.gateway(query))['ok'])
        self.assertFalse(Path(str(self.settings) + '.request').exists())
        self.config['loxone_enabled'] = False
        self.settings.write_text(json.dumps(self.config))
        self.assertFalse(json.loads(self.gateway({'token':TOKEN,'command':'stop'}))['ok'])

    def test_status_fields_and_off_light(self):
        self.fake_bridge({'ok': True, 'data': {'standby':False,'speed_gain':40,
            'stream':{'state':'running','cue':-2},'standalone_remaining_duration':900,
            'cur_program_user':0,'cur_program_slot':1,'cur_program_cue':2,
            'zones':[{'cue':261,'intensity':50,'status':'running'},
                     {'cue':256,'intensity':80,'status':'running'}]}})
        output = self.gateway({'token':TOKEN,'command':'status'})
        fields = dict(line.split('=') for line in output.strip().splitlines())
        self.assertEqual(fields['online'], '1')
        self.assertEqual(fields['jet_running'], '1')
        self.assertEqual(fields['speed_percent'], '40')
        self.assertEqual(fields['remaining_seconds'], '900')
        self.assertEqual(fields['light_0_on'], '1')
        self.assertEqual(fields['light_1_on'], '0')
        self.assertNotIn('light_2_on', fields)
        self.assertEqual(json.loads(Path(str(self.settings)+'.request').read_text())['arguments'], {})

    def test_offline_or_malformed_status_never_fakes_values(self):
        for reply in ({'ok':False}, {'ok':True,'data':{}}, {'ok':True,'data':'invalid'}):
            self.fake_bridge(reply)
            self.assertEqual(self.gateway({'token':TOKEN,'command':'status'}), 'online=0\n')

    def test_analogue_whole_decimal_and_preview(self):
        result = json.loads(self.gateway({'token':TOKEN,'command':'speed','percent':'40.000'}))
        self.assertTrue(result['ok'], result)
        self.assertTrue(result['preview'])
        self.assertIn('PREVIEW POST /speed_gain {"speed_gain": 40}', result['output'])
        result = json.loads(self.gateway({'token':TOKEN,'command':'stop'}))
        self.assertTrue(result['ok'], result)

    def test_unsafe_or_unknown_commands_rejected(self):
        for params in ({'command':'firmware'}, {'command':'speed','percent':'40.5'},
                       {'command':'speed','percent':'40;id'}, {'command':'stop','host':'example.com'},
                       {'command':'stop','percent':['1']}):
            self.assertFalse(json.loads(self.gateway({'token':TOKEN, **params}))['ok'])

    def test_saving_settings_preserves_token(self):
        result = php_test.PHPBridgeTests.request(self, {'command':'save','host':'10.0.0.2',
                                              'preview':True,'loxone_enabled':True})
        self.assertTrue(result['ok'], result)
        self.assertEqual(json.loads(self.settings.read_text())['loxone_token'], TOKEN)

    def test_enabling_generates_token_for_existing_installation(self):
        self.settings.write_text(json.dumps({'host':'10.0.0.2','preview':True}))
        result = php_test.PHPBridgeTests.request(self, {'command':'save','host':'10.0.0.2',
                                              'preview':True,'loxone_enabled':True})
        self.assertTrue(result['ok'], result)
        saved = json.loads(self.settings.read_text())
        self.assertEqual(len(saved['loxone_token']), 64)
        self.assertTrue(saved['loxone_enabled'])


if __name__ == '__main__':
    unittest.main()
