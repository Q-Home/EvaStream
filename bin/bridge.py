#!/usr/bin/env python3
"""JSON stdin/stdout bridge; only fixed commands, never a shell command."""
import contextlib
import io
import ipaddress
import json
import sys
from pathlib import Path

from eva import main, COLORS

PARAMS = {
    'status': {}, 'zones': {}, 'programs': {}, 'users': {}, 'colors': {},
    'pause': {}, 'resume': {}, 'stop': {},
    'standby': {'state': None},
    'light': {'color': None, 'zone': '--zone', 'brightness': '--brightness'},
    'speed': {'percent': None},
    'jet': {'speed': '--speed', 'minutes': '--minutes'},
    'program': {'id': None, 'user': '--user', 'slot': '--slot',
                'speed': '--speed', 'cue_index': '--cue-index'},
}


def run(config, payload):
    host = str(config.get('host', ''))
    address = ipaddress.IPv4Address(host)
    if not address.is_private or address.is_loopback or address.is_multicast or address.is_unspecified:
        raise ValueError('Gebruik het lokale IPv4-adres van de EVA Controller.')
    command = payload.get('command')
    if command not in PARAMS:
        raise ValueError('Onbekende opdracht.')
    arguments = payload.get('arguments', {})
    if not isinstance(arguments, dict) or set(arguments) - set(PARAMS[command]):
        raise ValueError('Onbekende parameters.')
    argv = ['--host', host]
    if config.get('preview', True) is False:
        argv.append('--execute')
    argv.append(command)
    for key, flag in PARAMS[command].items():
        if key in arguments:
            value = arguments[key]
            if isinstance(value, bool) or not isinstance(value, (str, int)):
                raise ValueError('Ongeldige parameter: ' + key)
            if flag:
                argv.append(flag)
            argv.append(str(value))
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            main(argv)
    except (Exception, SystemExit) as exc:
        return {'ok': False, 'error': str(exc), 'output': output.getvalue(),
                'hint': 'Controleer de status: bij een verbindingsfout kan een deel al uitgevoerd zijn.'}
    text = output.getvalue()
    result = {'ok': True, 'preview': config.get('preview', True), 'output': text}
    if command in ('status', 'zones', 'programs', 'users', 'colors'):
        result['data'] = json.loads(text)
    return result


if __name__ == '__main__':
    try:
        config = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
        payload = json.loads(sys.stdin.read(8193))
        result = run(config, payload)
    except Exception as exc:
        result = {'ok': False, 'error': str(exc)}
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result['ok'] else 1)
