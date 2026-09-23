"""
Generate Public/css/theme-base.css: a dark remap of every colour FreeScout's
own stylesheets set.

Hand-picking selectors can't keep up with FreeScout's ~11k lines of CSS, and
any rule that gets missed shows up as white-on-white or black-on-ink. Instead,
walk every rule in the core stylesheets, keep only colour-bearing
declarations, map each colour onto the Masjid Media palette, and re-emit the
rule scoped under `body.mm-theme` (which also out-specifies the original).

Run from the FreeScout root after every FreeScout upgrade:

    pip install tinycss2
    python Modules/MasjidMediaBrand/Tools/build_theme_base.py

Hand-tuned exceptions belong in theme.css, which loads after this file.
"""
import colorsys
import os
import re
import sys

import tinycss2

ROOT = os.getcwd()
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Public', 'css', 'theme-base.css')

SOURCES = [
    'public/css/bootstrap.css',
    'public/css/select2/select2.min.css',
    'public/js/featherlight/featherlight.min.css',
    'public/js/featherlight/featherlight.gallery.min.css',
    'public/css/magic-check.css',
    'public/js/summernote/summernote.css',
    'public/js/flatpickr/flatpickr.min.css',
    'public/js/bootstrap3-editable/css/bootstrap-editable.css',
    'public/js/datatables/datatables.min.css',
    'public/css/style.css',
]

# Selectors whose colours stay as authored: the email body "paper" and the
# editor's editing surface are deliberately light (see theme.css).
KEEP_LIGHT = re.compile(r'thread-content|note-editable|note-codable|thread-original')

# Palette (masjid-media-website resources/css/app.css).
INK = '#0e1318'
INK_SOFT = '#14191f'
INK_RAISED = '#1a2026'
INK_LINE = '#252c33'
INK_LINE_STRONG = '#343c45'
BONE = '#efe6d4'
BONE_SOFT = '#d9cfb9'
BONE_DIM = '#b7ac93'
MUTED = '#8b8a82'
BRASS = '#c9a864'
BRASS_DEEP = '#a5894f'
BRASS_SOFT = '#e1c68e'
SAGE = '#3f564e'
DANGER = '#d9876b'
SUCCESS = '#8fa876'

NAMED = {
    'white': (255, 255, 255), 'black': (0, 0, 0), 'red': (255, 0, 0), 'green': (0, 128, 0),
    'blue': (0, 0, 255), 'gray': (128, 128, 128), 'grey': (128, 128, 128), 'silver': (192, 192, 192),
    'lightgray': (211, 211, 211), 'lightgrey': (211, 211, 211), 'darkgray': (169, 169, 169),
    'whitesmoke': (245, 245, 245), 'gainsboro': (220, 220, 220), 'deepskyblue': (0, 191, 255),
    'lightskyblue': (135, 206, 250), 'yellow': (255, 255, 0), 'orange': (255, 165, 0),
    'lightgreen': (144, 238, 144), 'lightblue': (173, 216, 230),
}

COLOR_RE = re.compile(
    r'#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)|\b(?:' + '|'.join(NAMED) + r')\b', re.I)

COLOR_PROPS = {
    'color': 'fg', 'background': 'bg', 'background-color': 'bg', 'background-image': 'bg',
    'border': 'border', 'border-color': 'border', 'border-top': 'border', 'border-bottom': 'border',
    'border-left': 'border', 'border-right': 'border', 'border-top-color': 'border',
    'border-bottom-color': 'border', 'border-left-color': 'border', 'border-right-color': 'border',
    'outline': 'border', 'outline-color': 'border', 'box-shadow': 'shadow', 'text-shadow': 'tshadow',
    'fill': 'fg', 'stroke': 'fg', 'caret-color': 'fg', 'column-rule': 'border',
}


def parse_color(tok):
    t = tok.lower()
    if t in NAMED:
        return NAMED[t] + (1.0,)
    if t.startswith('#'):
        h = t[1:]
        if len(h) in (3, 4):
            h = ''.join(c * 2 for c in h)
        if len(h) not in (6, 8):
            return None
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return (r, g, b, a)
    m = re.match(r'rgba?\(([^)]*)\)', t)
    if m:
        parts = [p.strip() for p in re.split(r'[ ,/]+', m.group(1)) if p.strip()]
        try:
            vals = [float(p.rstrip('%')) * (2.55 if p.endswith('%') else 1) for p in parts[:3]]
            a = float(parts[3].rstrip('%')) / (100 if parts[3].endswith('%') else 1) if len(parts) > 3 else 1.0
            return (vals[0], vals[1], vals[2], a)
        except (ValueError, IndexError):
            return None
    return None


def hexa(hexcol, a):
    if a >= 0.999:
        return hexcol
    r, g, b = int(hexcol[1:3], 16), int(hexcol[3:5], 16), int(hexcol[5:7], 16)
    return f'rgba({r},{g},{b},{round(a, 3)})'


def tint(hexcol, alpha):
    r, g, b = int(hexcol[1:3], 16), int(hexcol[3:5], 16), int(hexcol[5:7], 16)
    return f'rgba({r},{g},{b},{alpha})'


def hue_family(h):
    deg = h * 360
    if deg < 20 or deg >= 330:
        return 'red'
    if deg < 70:
        return 'amber'
    if deg < 170:
        return 'green'
    return 'blue'


def map_color(rgba, kind):
    r, g, b, a = rgba
    if a == 0:
        return None
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    # Only clearly saturated colours are accents. FreeScout's body text is a
    # dark slate (#2a3b47, s≈0.26) that must read as text (bone), not as a
    # blue link that would turn brass.
    chromatic = s > 0.4 and 0.18 < l < 0.92

    if kind == 'shadow':
        if chromatic and hue_family(h) == 'blue':
            return tint(BRASS, round(min(a, 0.6), 2))
        return f'rgba(0,0,0,{round(min(1, a * 1.5 + 0.1), 2)})' if l < 0.5 else hexa(INK_LINE, a)
    if kind == 'tshadow':
        return 'rgba(0,0,0,0)' if l > 0.5 else 'rgba(0,0,0,0.4)'

    if chromatic:
        fam = hue_family(h)
        accent = {'blue': BRASS, 'amber': BRASS_SOFT, 'green': SUCCESS, 'red': DANGER}[fam]
        if kind == 'fg':
            return hexa(accent, a)
        if kind == 'bg':
            if l > 0.78:
                # FreeScout's pale blues are chrome (toolbars, section bars,
                # table heads, selected rows), not accents: raised ink. Pale
                # amber/green/red are alert washes and keep a tint.
                if fam == 'blue':
                    return hexa(INK_RAISED, a)
                return tint({'amber': BRASS, 'green': SUCCESS, 'red': DANGER}[fam], 0.14)
            return hexa({'blue': BRASS, 'amber': BRASS, 'green': SAGE, 'red': DANGER}[fam], a)
        if kind == 'border':
            if l > 0.78:
                return tint(accent, 0.4)
            return hexa({'blue': BRASS_DEEP, 'amber': BRASS_DEEP, 'green': SUCCESS, 'red': DANGER}[fam], a)

    if kind == 'fg':
        if l < 0.3:
            return hexa(BONE, a)
        if l < 0.55:
            return hexa(BONE_SOFT, a)
        if l < 0.8:
            return hexa(MUTED, a)
        if l < 0.97:
            return hexa(BONE_DIM, a)
        return hexa(BONE, a)
    if kind == 'bg':
        if a < 0.35:
            return f'rgba(239,230,212,{round(a * 0.5, 3)})' if l < 0.5 else f'rgba(0,0,0,{round(a, 3)})'
        if l >= 0.985:
            return hexa(INK_SOFT, a)
        if l >= 0.92:
            return hexa(INK_RAISED, a)
        if l >= 0.75:
            return hexa(INK_LINE, a)
        if l >= 0.45:
            return hexa(INK_LINE_STRONG, a)
        return hexa(INK_RAISED, a) if l > 0.08 else hexa(INK, a)
    if kind == 'border':
        return hexa(INK_LINE, a) if l >= 0.55 else hexa(INK_LINE_STRONG, a)
    return None


def remap_value(value, kind):
    changed = False

    def sub(m):
        nonlocal changed
        rgba = parse_color(m.group(0))
        if rgba is None:
            return m.group(0)
        new = map_color(rgba, kind)
        if new is None:
            return m.group(0)
        changed = True
        return new

    return COLOR_RE.sub(sub, value), changed


def scope_selector(sel):
    sel = sel.strip()
    if not sel or sel.startswith(':root'):
        return None
    m = re.match(r'^(html\s*)?(body)?(.*)$', sel, re.S)
    has_html, has_body, rest = m.group(1), m.group(2), m.group(3)
    if has_body:
        return 'body.mm-theme' + rest
    if has_html:
        rest = rest.strip()
        return 'body.mm-theme' + ((' ' + rest) if rest else '')
    return 'body.mm-theme ' + sel


def process_rules(rules, out):
    for rule in rules:
        if rule.type == 'qualified-rule':
            prelude = tinycss2.serialize(rule.prelude).strip()
            if KEEP_LIGHT.search(prelude):
                continue
            decls = tinycss2.parse_declaration_list(rule.content, skip_comments=True, skip_whitespace=True)
            new_decls = []
            for d in decls:
                if d.type != 'declaration':
                    continue
                kind = COLOR_PROPS.get(d.lower_name)
                if not kind:
                    continue
                value = tinycss2.serialize(d.value).strip()
                # Skip IE hacks such as `#fff\9`: once minified, the stray
                # backslash escapes the rule's closing brace and swallows
                # every rule after it.
                if '\\' in value:
                    continue
                imp = ' !important' if d.important else ''
                if 'gradient' in value:
                    # Remap every stop but keep the gradient: FreeScout uses
                    # transparent-to-white fades (e.g. .conv-fader) that must
                    # become transparent-to-ink, not a flat fill.
                    new_value, changed = remap_value(value, 'bg')
                    if changed:
                        new_decls.append(f'{d.name}:{new_value}{imp}')
                    continue
                if 'url(' in value:
                    continue
                new_value, changed = remap_value(value, kind)
                if changed:
                    new_decls.append(f'{d.name}:{new_value}{imp}')
            if not new_decls:
                continue
            # Light text that now sits on a solid brass/danger fill must flip
            # to ink, or it lands cream-on-gold.
            joined = ';'.join(new_decls)
            if re.search(r'background(-color)?:(%s|%s)' % (BRASS, DANGER), joined):
                new_decls = [re.sub(r'^color:(%s|%s|%s)' % (BONE, BONE_DIM, BONE_SOFT), 'color:' + INK, d) for d in new_decls]
            selectors = [scope_selector(s) for s in prelude.split(',')]
            selectors = [s for s in selectors if s]
            if selectors:
                out.append(f"{','.join(selectors)}{{{';'.join(new_decls)}}}")
        elif rule.type == 'at-rule' and rule.lower_at_keyword in ('media', 'supports') and rule.content:
            inner = []
            process_rules(tinycss2.parse_rule_list(rule.content, skip_comments=True, skip_whitespace=True), inner)
            if inner:
                out.append(f"@{rule.at_keyword} {tinycss2.serialize(rule.prelude).strip()}{{" + ''.join(inner) + '}')


def main():
    out = [
        '/* GENERATED by Tools/build_theme_base.py from FreeScout core CSS. Do not edit;',
        '   put hand-tuned overrides in theme.css. */',
    ]
    for src in SOURCES:
        path = os.path.join(ROOT, src)
        if not os.path.exists(path):
            print('missing', src, file=sys.stderr)
            continue
        with open(path, encoding='utf-8', errors='replace') as f:
            rules = tinycss2.parse_stylesheet(f.read(), skip_comments=True, skip_whitespace=True)
        before = len(out)
        out.append(f'/* {src} */')
        process_rules(rules, out)
        print(f'{src}: {len(out) - before - 1} rules')
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    print('wrote', OUT)


if __name__ == '__main__':
    main()
