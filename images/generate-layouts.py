#!/usr/bin/env python3
"""Generate SVG references directly from the two Kanata configurations.

Run from any directory: python3 images/generate-layouts.py
Convert SVGs to PNG with rsvg-convert if desired.
"""
from pathlib import Path
import html
import re

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent


def parse_config(path):
    text = re.sub(r';;[^\n]*', '', path.read_text())
    tokens = iter(re.findall(r'\(|\)|[^\s()]+', text))

    def expression():
        result = []
        for token in tokens:
            if token == ')':
                return result
            result.append(expression() if token == '(' else token)
        return result

    forms = expression()
    source = next(f[1:] for f in forms if f[0] == 'defsrc')
    layers = {f[1]: dict(zip(source, f[2:], strict=True))
              for f in forms if f[0] == 'deflayer'}
    aliases = {}
    for f in forms:
        if f[0] == 'defalias':
            aliases.update(zip(f[1::2], f[2::2]))
    return layers, aliases


LABELS = {
    'esc': 'Esc', 'grv': '`', 'bspc': 'Delete', 'tab': 'Tab',
    'caps': 'Caps', 'ret': 'Enter', 'lsft': 'Shift', 'rsft': 'Shift',
    'lctl': 'Ctrl', 'lalt': 'Option', 'ralt': 'Option',
    'lmet': 'Cmd', 'rmet': 'Cmd', 'spc': 'Space',
    'left': '←', 'down': '↓', 'up': '↑', 'rght': '→',
    'brdn': 'Bright −', 'brup': 'Bright +', 'prev': 'Previous',
    'pp': 'Play / pause', 'next': 'Next', 'mute': 'Mute',
    'vold': 'Volume −', 'volu': 'Volume +',
    'C-S-tab': 'Ctrl ⇧ Tab', 'C-tab': 'Ctrl Tab', 'f13': 'F13',
}


def label(key):
    return LABELS.get(key, key.upper() if len(key) > 1 else key)


ROWS = [
    [('esc', 1)] + [(f'f{i}', 1) for i in range(1, 13)],
    [('grv', 1)] + [(k, 1) for k in '1234567890-='] + [('bspc', 2)],
    [('tab', 1.5)] + [(k, 1) for k in 'qwertyuiop[]'] + [('\\', 1.5)],
    [('caps', 1.75)] + [(k, 1) for k in "asdfghjkl;' ".strip()] + [('ret', 2.25)],
    [('lsft', 2.25)] + [(k, 1) for k in 'zxcvbnm,./'] + [('rsft', 2.75)],
    [('lctl', 1.25), ('lalt', 1.25), ('lmet', 1.25), ('spc', 6.25),
     ('rmet', 1.25), ('ralt', 1.25), ('left', .75), ('down', .75),
     ('up', .75), ('rght', .75)],
]
COLORS = {
    'normal': ('#1e293b', '#475569'), 'mod': ('#173e51', '#38bdf8'),
    'media': ('#3b3052', '#c4b5fd'), 'nav': ('#16483d', '#34d399'),
    'blocked': ('#34252e', '#9f526b'), 'pass': ('#192330', '#364152'),
}


def make_image(name, title):
    layers, aliases = parse_config(ROOT / 'layouts' / f'{name}.cfg')
    base = layers[name]
    nav = layers['nav']
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="1280" viewBox="0 0 1440 1280">',
             '<rect width="1440" height="1280" fill="#0b1220"/>',
             '<g font-family="DejaVu Sans, sans-serif">']

    def text(x, y, value, size=18, color='#e2e8f0', anchor='start', weight='normal'):
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{html.escape(value)}</text>')

    def keyboard(mapping, y, navigation=False):
        for row_index, row in enumerate(ROWS):
            x = 60
            for physical, units in row:
                action = mapping.get(physical, physical)
                category = 'pass' if navigation and physical not in mapping else 'normal'
                sub = 'passthrough' if category == 'pass' else ''
                if action == '_':
                    action = physical
                if action == 'XX':
                    main, sub, category = 'Blocked', '', 'blocked'
                elif action.startswith('@'):
                    alias = aliases[action[1:]]
                    tap, hold = alias[3:5]
                    if isinstance(tap, list):
                        main, sub = 'Shift', 'tap: one-shot · hold: Shift'
                    else:
                        main = label(tap)
                        sub = 'hold: Nav' if isinstance(hold, list) else f'hold: {label(hold)}'
                    category = 'nav' if physical == 'spc' else 'mod'
                else:
                    main = label(action)
                    if navigation and physical in mapping:
                        category = 'nav'
                    elif physical.startswith('f') and physical[1:].isdigit() and action != physical:
                        category = 'media'
                if navigation and physical == 'spc':
                    main, sub, category = 'Keep Space held', 'release to return to typing', 'nav'
                width = units * 84 - 6
                top = y + row_index * 67
                fill, stroke = COLORS[category]
                parts.append(f'<rect x="{x}" y="{top}" width="{width}" height="59" rx="8" fill="{fill}" stroke="{stroke}"/>')
                # Small labels always identify the physical QWERTY position.
                text(x + 7, top + 13, label(physical), 10, '#94a3b8')
                text(x + width / 2, top + 33, main, 12 if len(main) > 10 else 14 if len(main) > 6 else 20, anchor='middle', weight='bold')
                if sub:
                    text(x + width / 2, top + 49, sub, 8 if width < 65 else 9 if len(sub) > 17 else 11, '#b8c9db', 'middle')
                x += units * 84

    text(60, 58, title, 34, weight='bold')
    text(60, 88, f'layouts/{name}.cfg · macOS · Physical positions labeled in the upper-left of every key', 17, '#94a3b8')
    text(60, 134, '1  TYPING LAYER', 22, '#38bdf8', weight='bold')
    text(60, 161, 'Large label = tap output. Blue keys add hold modifiers; purple keys are media controls.', 16, '#b8c9db')
    keyboard(base, 181)
    text(60, 619, 'Home-row holds: Ctrl · Option · Shift · Cmd  |  Cmd · Shift · Option · Ctrl', 17)
    text(60, 646, 'Caps: tap Esc / hold Ctrl. Shift: tap for one-shot Shift (1s timeout), or hold normally.', 16, '#b8c9db')
    text(60, 699, '2  NAVIGATION LAYER — HOLD SPACE', 22, '#34d399', weight='bold')
    text(60, 726, 'Green = navigation action. Red = disabled. Gray = unintercepted physical key, passed through.', 16, '#b8c9db')
    keyboard(nav, 746, True)
    text(60, 1182, 'H/J/K/L: arrows · U/I: previous/next tab (Ctrl+Shift+Tab / Ctrl+Tab) · ;: Enter · F: F13', 16)
    text(60, 1210, 'Shift, Caps and intercepted home-row modifiers are blocked in Nav. F13 needs an external binding.', 15, '#b8c9db')
    text(60, 1238, 'Tab-switch shortcuts depend on the app. Unlisted keys pass through; Nav coverage differs between configs.', 15, '#94a3b8')
    parts.extend(['</g>', '</svg>'])
    (OUT / f'{name}.svg').write_text('\n'.join(parts) + '\n')


if __name__ == '__main__':
    make_image('qwerty', 'QWERTY — home-row modifiers + navigation')
    make_image('colemak-dh', 'Colemak-DH — home-row modifiers + navigation')
