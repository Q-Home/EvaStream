import contextlib
import io
import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bin'))
import eva
import bridge


class Handler(BaseHTTPRequestHandler):
    writes = []
    fail_path = None
    status = {}
    zones = []

    def log_message(self, *args):
        pass

    def do_GET(self):
        data = {'/status': self.status,
                '/zones': self.zones,
                '/users': [{'id': 0, 'slots': [{'program': 0, 'speed_gain': 65}]}],
                '/programs': [{'id': 0, 'name': 'Training', 'cues': [{'id': 5}]},
                              {'id': 4, 'name': 'Custom', 'cues': [{'id': 8}]},
                              {'id': 6, 'name': 'Empty', 'cues': []}]}[self.path]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        self.writes.append((self.path, json.loads(raw) if raw else None))
        self.send_response(500 if self.path == self.fail_path else 200)
        self.end_headers()
        self.wfile.write(b'OK')


class ControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        Handler.writes = []
        Handler.fail_path = None
        Handler.status = {'standby': True, 'stream': {'state': 'idle'}}
        Handler.zones = [{'name': 'Pool', 'active': True}]
        original = eva.EVA.__init__
        def local(client, *args, **kwargs):
            original(client, *args, **kwargs)
            client.base = 'http://127.0.0.1:%s' % self.server.server_port
        self.patch = patch.object(eva.EVA, '__init__', local)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def run_command(self, command, arguments=None, preview=False):
        return bridge.run({'host': '192.0.2.18', 'preview': preview},
                          {'command': command, 'arguments': arguments or {}})

    def test_read_status(self):
        result = self.run_command('status')
        self.assertTrue(result['data']['standby'])
        self.assertEqual(Handler.writes, [])

    def test_preview_never_posts(self):
        for command, args in [('jet', {'speed':40,'minutes':15}),
                              ('light', {'color':'blue'}),
                              ('program', {'id':0,'user':0}), ('stop', {})]:
            self.assertTrue(self.run_command(command, args, preview=True)['ok'])
        self.assertEqual(Handler.writes, [])

    def test_light_color_and_brightness(self):
        self.assertTrue(self.run_command('light', {'color':'blue','brightness':50})['ok'])
        self.assertEqual(Handler.writes, [('/start_cue', {'id':261,'zone':0}),
                                          ('/intensity', {'zone':0,'intensity':50})])

    def test_light_off_does_not_change_standby(self):
        self.run_command('light', {'color':'off'})
        self.assertEqual(Handler.writes, [('/start_cue', {'id':256,'zone':0})])

    def test_brightness_does_not_change_color_or_standby(self):
        self.assertTrue(self.run_command('brightness', {'percent':60,'zone':0})['ok'])
        self.assertEqual(Handler.writes, [('/intensity', {'zone':0,'intensity':60})])

    def test_training_blocks_zone_zero_even_paused_in_standby(self):
        for state in ('running', 'paused'):
            for standby in (True, False):
                Handler.status = {'standby':standby,'stream':{'state':state,'cue':4}}
                for command, args in [('light', {'color':'blue'}),
                                      ('light', {'color':'off'}),
                                      ('brightness', {'percent':0}),
                                      ('brightness', {'percent':60})]:
                    result = self.run_command(command, args)
                    self.assertFalse(result['ok'], result)
                    self.assertIn('geblokkeerd', result['error'])
        self.assertEqual(Handler.writes, [])

    def test_standalone_swimming_does_not_lock_lighting(self):
        for state in ('running', 'paused'):
            Handler.status = {'standby':False,'stream':{'state':state,'cue':-2}}
            self.assertTrue(self.run_command('light', {'color':'blue'})['ok'])

    def test_other_light_zone_is_not_locked_by_training(self):
        Handler.status = {'standby':False,'stream':{'state':'paused','cue':4}}
        Handler.zones.append({'name':'Other','active':True})
        self.assertTrue(self.run_command('light', {'color':'blue','zone':1})['ok'])
        self.assertEqual(Handler.writes[0], ('/start_cue', {'id':261,'zone':1}))

    def test_unknown_training_status_blocks_shared_zone(self):
        for status in ({}, {'stream':{'state':'unexpected'}},
                       {'stream':{'state':'paused'}}):
            Handler.status = status
            self.assertFalse(self.run_command('light', {'color':'blue'})['ok'])
        self.assertEqual(Handler.writes, [])

    def test_jet_start_order_and_seconds(self):
        self.assertTrue(self.run_command('jet', {'speed':40,'minutes':15})['ok'])
        self.assertEqual(Handler.writes, [('/reset_graph',None),
            ('/standalone',{'duration':900,'intensity':40}),
            ('/standby',{'standby':False}),('/set_paused',{'pause':False})])

    def test_program_saved_slot_gain(self):
        self.assertTrue(self.run_command('program', {'id':0,'user':0})['ok'])
        self.assertEqual(Handler.writes[1], ('/prepare_program',
            {'user':0,'program':0,'slot':0,'start_cue':0,'speed_gain':65}))

    def test_custom_program_needs_explicit_speed(self):
        self.assertFalse(self.run_command('program', {'id':4,'user':0})['ok'])
        self.assertEqual(Handler.writes, [])
        self.assertTrue(self.run_command('program', {'id':4,'user':0,'speed':40})['ok'])
        self.assertEqual(Handler.writes[1][1]['program'], 4)

    def test_invalid_commands_do_not_write(self):
        for command, args in [('program',{'id':6,'user':0}),
                              ('program',{'id':0,'user':99}),
                              ('program',{'id':0,'user':0,'cue_index':1}),
                              ('speed',{'percent':101}),('jet',{'speed':20,'minutes':15}),
                              ('light',{'color':'blue','zone':3})]:
            self.assertFalse(self.run_command(command,args)['ok'])
        self.assertEqual(Handler.writes, [])

    def test_failure_aborts_start_without_retry(self):
        Handler.fail_path = '/prepare_program'
        self.assertFalse(self.run_command('program',{'id':0,'user':0})['ok'])
        self.assertEqual([p for p,d in Handler.writes], ['/reset_graph','/prepare_program'])

    def test_unknown_bridge_input_rejected(self):
        with self.assertRaises(ValueError): self.run_command('firmware')
        with self.assertRaises(ValueError): self.run_command('status',{'host':'evil'})
        with self.assertRaises(ValueError):
            bridge.run({'host':'127.0.0.1'}, {'command':'status'})
        self.assertEqual(Handler.writes, [])


if __name__ == '__main__':
    unittest.main()
