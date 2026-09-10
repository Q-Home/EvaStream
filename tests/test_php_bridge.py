"""Exercise the real PHP endpoint and Python bridge, with no controller writes."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PHP = os.environ.get('EVA_TEST_PHP') or shutil.which('php')


@unittest.skipUnless(PHP, 'PHP CLI is required for the web-to-Python regression test')
class PHPBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        (self.path / 'settings.json').write_text(
            json.dumps({'host': '192.0.2.18', 'preview': True}), encoding='utf-8')
        shutil.copy(ROOT / 'webfrontend/htmlauth/common.php', self.path / 'common.php')
        (self.path / 'loxberry_system.php').write_text(
            '<?php $lbpconfigdir = __DIR__; $lbpbindir = getenv("EVA_TEST_BIN");', encoding='utf-8')
        endpoint = (ROOT / 'webfrontend/htmlauth/api.php').read_text(encoding='utf-8')
        # Adapt only runtime entry points for PHP CLI and the host's Python path.
        endpoint = endpoint.replace('php://input', 'php://stdin')
        endpoint = endpoint.replace("'/usr/bin/python3'", "getenv('EVA_TEST_PYTHON')")
        (self.path / 'api.php').write_text(endpoint, encoding='utf-8')
        (self.path / 'runner.php').write_text('''<?php
require_once __DIR__ . '/common.php';
eva_session();
$_SERVER['REQUEST_METHOD'] = 'POST';
$_SERVER['HTTP_X_CSRF_TOKEN'] = $_SESSION['csrf'];
require __DIR__ . '/api.php';
''', encoding='utf-8')

    def request(self, payload):
        env = dict(os.environ, EVA_TEST_BIN=str(ROOT / 'bin'), EVA_TEST_PYTHON=sys.executable)
        result = subprocess.run([PHP, '-d', 'include_path=' + str(self.path),
                                 str(self.path / 'runner.php')],
                                input=json.dumps(payload), capture_output=True, text=True,
                                env=env, timeout=20, check=True)
        return json.loads(result.stdout)

    def test_empty_object_survives_php_to_python(self):
        for command in ('colors', 'pause', 'resume', 'stop'):
            with self.subTest(command=command):
                result = self.request({'command': command, 'arguments': {}})
                self.assertTrue(result['ok'], result)
                if command != 'colors':
                    self.assertIn('PREVIEW POST', result['output'])

    def test_omitted_arguments_also_work(self):
        self.assertTrue(self.request({'command': 'colors'})['ok'])

    def test_nonempty_arguments_survive(self):
        result = self.request({'command': 'speed', 'arguments': {'percent': 40}})
        self.assertTrue(result['ok'], result)
        self.assertIn('"speed_gain": 40', result['output'])

    def test_array_or_unknown_parameters_still_rejected(self):
        for arguments in ([], {'unexpected': 1}):
            result = self.request({'command': 'colors', 'arguments': arguments})
            self.assertFalse(result['ok'], result)


if __name__ == '__main__':
    unittest.main()
