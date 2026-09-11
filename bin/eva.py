#!/usr/bin/env python3
"""Local EVA controller client. Python 3.8+, no external dependencies.

Read commands run immediately. Writes are previewed unless --execute is set.
Protocol derived from the controller's webapp; not an official vendor SDK.
"""
import argparse
import json
import sys
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import URLError

COLORS = dict(zip(
    ['off', 'red', 'yellow', 'green', 'cyan', 'blue', 'purple',
     'lightblue', 'white', 'cyan-blue-gradient', 'cyan-blue-split'],
    range(256, 267)))


class EVA:
    def __init__(self, host='evacontroller.local', execute=False):
        self.base = 'http://' + host
        self.execute = execute
        self.http = build_opener(ProxyHandler({}))

    def request(self, method, path, data=None):
        body = None if data is None else json.dumps(data).encode()
        req = Request(self.base + path, data=body, method=method,
                      headers={'Content-Type': 'application/json'})
        # No automatic retries: a timed-out write may already have executed.
        with self.http.open(req, timeout=10) as response:
            text = response.read().decode('utf-8')
        try:
            return json.loads(text)
        except ValueError:
            return text

    def get(self, path):
        return self.request('GET', path)

    def check_light_control(self, zone):
        if zone != 0:
            return
        status = self.get('/status')
        stream = status.get('stream', {}) if isinstance(status, dict) else {}
        state = stream.get('state')
        if state not in ('idle', 'running', 'paused', 'stopped'):
            raise ValueError('Lichtopdracht geweigerd: de trainingsstatus is onbekend.')
        # The official webapp also locks zone 0 for paused training cues.
        # Standby does not release ownership; standalone cue -2 is exempt.
        if state in ('running', 'paused') and stream.get('cue') != -2:
            raise ValueError('EVAstream-verlichting (zone 0) is geblokkeerd door een '
                             'lopende of gepauzeerde training. Stop de sessie expliciet '
                             'voordat je deze verlichting bedient. Er is niets verstuurd.')

    def apply(self, commands):
        for path, data in commands:
            print(('SEND' if self.execute else 'PREVIEW') + ' POST ' + path,
                  '' if data is None else json.dumps(data))
            if self.execute:
                print(json.dumps(self.request('POST', path, data)))
        if self.execute:
            print('Status:', json.dumps(self.get('/status'), indent=2))
        else:
            print('Geen wijzigingen verstuurd. Gebruik --execute om uit te voeren.')


def bounded(low, high):
    def parse(value):
        n = int(value)
        if not low <= n <= high:
            raise argparse.ArgumentTypeError('Bereik: %s..%s' % (low, high))
        return n
    return parse


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='evacontroller.local')
    parser.add_argument('--execute', action='store_true', help='Voer wijzigingen echt uit')
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ['status', 'zones', 'programs', 'users', 'pause', 'resume', 'stop', 'colors']:
        sub.add_parser(name)
    p = sub.add_parser('standby')
    p.add_argument('state', choices=['on', 'off'])
    p = sub.add_parser('light')
    p.add_argument('color', choices=COLORS)
    p.add_argument('--zone', type=bounded(0, 3), default=0)
    p.add_argument('--brightness', type=bounded(0, 100), default=50)
    p = sub.add_parser('speed')
    p.add_argument('percent', type=bounded(30, 100))
    p = sub.add_parser('brightness')
    p.add_argument('percent', type=bounded(0, 100))
    p.add_argument('--zone', type=bounded(0, 3), default=0)
    p = sub.add_parser('jet')
    p.add_argument('--speed', required=True, type=bounded(30, 100))
    p.add_argument('--minutes', required=True, type=bounded(1, 120))
    p = sub.add_parser('program')
    p.add_argument('id', type=int)
    p.add_argument('--user', required=True, type=int)
    p.add_argument('--slot', type=bounded(0, 3), help='Optioneel bestaand gebruikersslot')
    p.add_argument('--speed', type=bounded(30, 100), help='Verplicht zonder passend slot')
    p.add_argument('--cue-index', type=bounded(0, 1000), default=0)
    args = parser.parse_args(argv)
    eva = EVA(args.host, args.execute)
    command = args.command
    if command in ['status', 'zones', 'programs', 'users']:
        print(json.dumps(eva.get('/' + command), ensure_ascii=False, indent=2))
        return
    if command == 'colors':
        print(json.dumps(COLORS, indent=2))
        return
    commands = []
    if command == 'standby':
        commands = [('/standby', {'standby': args.state == 'on'})]
    elif command in ['pause', 'resume']:
        commands = [('/set_paused', {'pause': command == 'pause'})]
    elif command == 'stop':
        commands = [('/stop_program', None)]
    elif command == 'speed':
        commands = [('/speed_gain', {'speed_gain': args.percent})]
    elif command == 'brightness':
        zones = eva.get('/zones')
        if args.zone >= len(zones):
            raise ValueError('Deze zone bestaat niet.')
        eva.check_light_control(args.zone)
        commands = [('/intensity', {'zone': args.zone, 'intensity': args.percent})]
    elif command == 'light':
        zones = eva.get('/zones')
        if args.zone >= len(zones):
            raise ValueError('Deze zone bestaat niet.')
        eva.check_light_control(args.zone)
        # Standby is global, so do not change it as a side effect of lighting.
        color = 'off' if args.brightness == 0 else args.color
        commands = [('/start_cue', {'id': COLORS[color], 'zone': args.zone})]
        if color != 'off':
            commands.append(('/intensity', {'zone': args.zone, 'intensity': args.brightness}))
    elif command == 'jet':
        commands = [('/reset_graph', None),
                    ('/standalone', {'duration': args.minutes * 60, 'intensity': args.speed}),
                    ('/standby', {'standby': False}),
                    ('/set_paused', {'pause': False})]
    elif command == 'program':
        programs, users = eva.get('/programs'), eva.get('/users')
        program = next((p for p in programs if p['id'] == args.id), None)
        user = next((u for u in users if u['id'] == args.user), None)
        if not program or not program.get('cues'):
            raise ValueError('Programma bestaat niet of is leeg.')
        if user is None:
            raise ValueError('Gebruiker bestaat niet.')
        if args.cue_index >= len(program['cues']):
            raise ValueError('Cue-index valt buiten dit programma.')
        slots = user.get('slots', [])
        slot = args.slot
        if slot is None:
            slot = next((i for i, s in enumerate(slots) if s.get('program') == args.id), None)
        if slot is not None and (slot >= len(slots) or slots[slot].get('program') != args.id):
            raise ValueError('Gekozen slot is niet gekoppeld aan dit programma.')
        speed = args.speed if args.speed is not None else (
            slots[slot].get('speed_gain') if slot is not None else None)
        if speed is None or not 30 <= speed <= 100:
            raise ValueError('Geef --speed 30..100 op; geen geldige snelheid in gebruikersslot.')
        # The webapp uses a temporary slot 0 for programs outside saved slots.
        payload = {'user': args.user, 'start_cue': args.cue_index,
                   'slot': slot if slot is not None else 0,
                   'program': args.id, 'speed_gain': speed}
        commands = [('/reset_graph', None), ('/prepare_program', payload),
                    ('/standby', {'standby': False}), ('/set_paused', {'pause': False})]
    eva.apply(commands)


if __name__ == '__main__':
    try:
        main()
    except (URLError, TimeoutError, OSError, ValueError, KeyError) as exc:
        print('Fout: %s. Bij een schrijffout kan een deel al uitgevoerd zijn; '
              'controleer de status voor je opnieuw probeert.' % exc, file=sys.stderr)
        sys.exit(1)
