#!/usr/bin/env python3
"""Build the Italian text patch for the US build from the European disc's MSG files.
usage: build_pack.py <SLUS_205.15> <MSG_E.DAT> <MSG_I.DAT> <out.bin> [report.txt]"""
import sys, struct, difflib, pickle, collections
from parse_msgs import us_msgs, eu_msgs, OFF, VR
US_EXE, MSG_E, MSG_I, OUT = sys.argv[1:5]
TAB_ADDR, BLOB_ADDR, IMG_ADDR = 0x2D19D0, 0x2D49D4, 0x2F8DEC
G = 242
um, uw, utab = us_msgs(US_EXE)
em, ew, etab, e_img_off, ebody = eu_msgs(MSG_E)
im, iw, itab, i_img_off, ibody = eu_msgs(MSG_I)
exe = open(US_EXE, 'rb').read()
def toks(m):
    out = []; i = 0
    while i < len(m):
        w = m[i]
        if w & 0x4000: out.append(('M', w & 0x3fff, m[i+1] if i+1 < len(m) else 0)); i += 2
        else: out.append((w >> 13 & 1, w & 0x1fff)); i += 1
    return out
# ---- glyph identity: EU narrow code -> US narrow code (letters, digits, punctuation present in both fonts)
E2U = {1: 112}
for k in range(26): E2U[5 + k] = 86 + k; E2U[31 + k] = 115 + k       # A-Z, a-z
for k in range(10): E2U[57 + k] = 143 + k                              # 1..9 0
E2U.update({3: 82, 67: 162, 70: 154, 71: 155, 72: 156, 73: 157, 74: 158, 75: 159, 76: 141, 77: 142, 78: 160,
            114: 164, 115: 113, 116: 114, 117: 153, 118: 337})
E2U_WIDE = {163 + k: 4 + k for k in range(26)}
U2E = {v: k for k, v in E2U.items()}
# ---- pairing US id -> EU id: (1) macro-expanded English text next to the same offset (UI texts, card names),
# gaps between pairs of one offset filled; (2) everywhere else (card effects, tutorial, story text) the same English
# sentence anywhere in the European English text, the copy nearest to the offset the neighbours have
import pair2, gmatch
pp = pair2.pairs(US_EXE, MSG_E, E2U, thr=0.85)
cand = {i: j for i, (j, r) in pp.items()}
ids = sorted(cand)
filled = 0
for x, y in zip(ids, ids[1:]):
    d = cand[x] - x
    if cand[y] - y == d and y - x <= 12:
        for i in range(x + 1, y):
            cand[i] = i + d; filled += 1
g_added = 0
gres = gmatch.run_all()          # {us id: [(ratio, eu id), ...]}
anchors = sorted((i, c[0][1] - i) for i, c in gres.items() if len(c) == 1 and c[0][0] >= 0.9 and gres[i][0][2] >= 6)
import bisect
aid = [a for a, _ in anchors]
def local_offset(i):
    if not anchors: return 0
    k = bisect.bisect_left(aid, i)
    lo = anchors[k-1][1] if k > 0 else anchors[0][1]
    hi = anchors[k][1] if k < len(anchors) else anchors[-1][1]
    return (lo + hi) / 2
for i, c in gres.items():
    if i in cand or i < 30: continue
    best = max(r for r, j, n in c)
    near = [(abs((j - i) - local_offset(i)), j) for r, j, n in c if r >= best - 0.03]
    cand[i] = min(near)[1]; g_added += 1
print('paired', len(pp), 'filled', filled, 'by content', g_added, 'total', len(cand))
# ---- the player-name messages are edited by the game while it runs: macros to them stay macros (EU 3 -> US 2, EU 5 -> US 4)
NAME_EU2US = {3: 2, 5: 4}
# ---- Italian messages are written without macros (expanded here), so they stand alone next to the English ones
def eu_flatten(words, depth=0):
    """tokens of an EU-I message with every macro expanded: ('G', flag, code) or ('M', macro word, US id) for a name"""
    out = []; i = 0
    while i < len(words):
        w = words[i]
        if w & 0x4000:
            w2 = words[i+1]; tid = w2 & 0x3fff
            if tid in NAME_EU2US:
                out.append(('M', w, NAME_EU2US[tid])); i += 2; continue
            tgt = im[tid]
            count = w & 0x3f; off = (w >> 6) & 0x7f
            q = off
            while count > 0 and q < len(tgt) and depth < 8:
                if tgt[q] & 0x4000:
                    out += eu_flatten(tgt[q:q+2], depth + 1); n = 2
                else:
                    out.append(('G', tgt[q] >> 13 & 1, tgt[q] & 0x1fff)); n = 1
                count -= n; q += n
                if tgt[q-1] & 0x8000: break
            i += 2
        else:
            out.append(('G', w >> 13 & 1, w & 0x1fff)); i += 1
    return out
used = set()
for m in um:
    for x in toks(m):
        if x[0] != 'M': used.add(x[1])
first_free = max(used) + 1
nl_us = uw[0] & 0x1fff; nl_eu = iw[0] & 0x1fff
newg = collections.OrderedDict()
def map_code(flag, e):
    if e == nl_eu: return nl_us
    if flag and e in E2U: return E2U[e]
    if not flag and e in E2U_WIDE: return E2U_WIDE[e]
    key = (flag, e)
    if key not in newg: newg[key] = first_free + len(newg)
    return newg[key]
def reflow(ws, maxlines=17, maxpx=384):
    """the engine keeps 17 lines per text: a longer message is wrapped again at the window width"""
    nl = nl_us
    def lines_of(w):
        n = 1
        for x in w:
            if not (x & 0x4000) and (x & 0x1fff) == nl: n += 1
        return n
    if lines_of(ws) <= maxlines: return ws
    end = ws[-1] & 0x8000
    toks = []                                    # words, with macro pairs kept together
    i = 0
    while i < len(ws):
        if ws[i] & 0x4000: toks.append((ws[i] & 0x7fff, ws[i + 1] & 0x7fff)); i += 2
        else: toks.append((ws[i] & 0x7fff,)); i += 1
    # split into words at spaces (code 112 narrow) and newlines
    words, cur = [], []
    for t in toks:
        if len(t) == 1 and (t[0] & 0x1fff) == nl and not (t[0] & 0x4000):
            if cur: words.append(cur); cur = []
        elif len(t) == 1 and t[0] == (1 << 13 | 112):
            if cur: words.append(cur); cur = []
        else: cur.append(t)
    if cur: words.append(cur)
    def wpx(wd): return sum((12 if (t[0] & 0x2000) else 22) if len(t) == 1 else 12 * 8 for t in wd)
    out, line, px = [], [], 0
    for wd in words:
        wp = wpx(wd)
        if line and px + 12 + wp > maxpx:
            out.append(line); line, px = [], 0
        if line: line.append((1 << 13 | 112,)); px += 12
        line += wd; px += wp
    if line: out.append(line)
    res = []
    for k, ln in enumerate(out):
        if k: res.append((nl,))
        res += ln
    flat = []
    for t in res:
        if len(t) == 2: flat += [t[0] | 0x4000, t[1]]
        else: flat.append(t[0])
    if end: flat[-1] |= 0x8000
    return flat if lines_of(flat) <= maxlines else None      # still too long: the English text stays
msgs = {}
for a, b in sorted(cand.items()):
    t = eu_flatten(im[b])
    if not t: continue
    ws = []
    for x in t:
        if x[0] == 'M': ws += [x[1] & 0x7fff | 0x4000, x[2]]
        else: ws.append((x[1] << 13) | map_code(x[1], x[2]))
    ws[-1] |= 0x8000
    ws = reflow(ws)
    if ws is None:
        print('kept in English (more than 17 lines in Italian):', a); continue
    msgs[a] = ws
print('Italian messages', len(msgs), 'new glyphs', len(newg), 'words', sum(len(v) for v in msgs.values()))
def eu_px(e):
    base = i_img_off + e * G
    b = ibody[base:base + G]
    px = []
    for x in b: px += [x & 15, x >> 4]
    return px[:484]
def to_us(px):
    W = 22
    sh = [0] * 484
    for y in range(22):
        for x in range(22):
            if y + 2 < 22: sh[(y + 2) * W + x] = px[y * W + x]
    out = [0] * 484
    for y in range(22):
        for x in range(22):
            v = sh[y * W + x]
            if v >= 12: out[y * W + x] = 15
            elif v >= 8: out[y * W + x] = 14
            elif v >= 4: out[y * W + x] = 13
            elif v >= 1: out[y * W + x] = 11
    for y in range(22):
        for x in range(22):
            if out[y * W + x] == 0:
                near = max(out[yy * W + xx] for yy in range(max(0, y-1), min(22, y+2)) for xx in range(max(0, x-1), min(22, x+2)))
                if near >= 11: out[y * W + x] = 4
    return out
# ---- the UI string table (menus drawn with the executable's own letters: A-Z, 0-9, space, '-', '?', '%' only; the
# strings sit in boxes made for the English words, so the Italian ones are chosen to fit; wording follows the
# European Italian release where it fits)
import json, os
UI_IT = {
 'NEWCOMER SORT': 'ORD PER NUOVO', 'NAME SORT': 'ORD PER NOME', 'AP SORT': 'ORD PER ATK', 'DP SORT': 'ORD PER DEF',
 'TYPE SORT': 'ORD PER TIPO', 'ATTRIBUTE SORT': 'ORD PER ATTRIB', 'LEVEL SORT': 'ORD PER LIV',
 'DECK-COSTS SORT': 'ORD PER COSTO', 'RANK SORT': 'ORD PER RANK', 'CARD-COLOR SORT': 'ORD PER COLORE',
 'ARE YOU READY ?': 'SEI PRONTO ?', 'YOU WIN': 'HAI VINTO', 'YOU LOSE': 'HAI PERSO', '1P WIN': '1P VINCE',
 '2P WIN': '2P VINCE', 'DRAW': 'PAREGGIO', 'OPTION': 'OPZIONI', 'SURRENDER': 'RESA', 'PROMOTION': 'PROMOZIONE',
 'DEMOTION': 'RETROCESSIONE', 'TREASURE': 'TESORO', 'GET CARD': 'OTTIENI CARTA',
 'GET SPECIAL CARD': 'OTTIENI CARTA SPECIALE', 'GRAVEYARD': 'CIMITERO', 'TUTORIAL': 'TUTORIAL',
 'CAUTION': 'ATTENZIONE', 'YES': 'SI', 'NO': 'NO', 'BUILD DECK': 'COSTRUISCI', 'CHEST': 'BAULE', 'BACK': 'TORNA',
 'EXIT': 'ESCI', 'REINCARNATION': 'REINCARNAZIONE', 'SELECT DECK': 'SELEZ DECK', 'DECK LEADER': 'LEADER DECK',
 'LIBRARY': 'BIBLIOT', '  NOW  \nLOADING': 'CARICAMENTO', 'NUMBER %03d': 'NUMERO %03d', 'MOVE': 'MOSSA',
 'DETAIL': 'INFO', '3D VIEW': 'VISTA 3D', 'LEADER': 'LEADER', 'PASSWORD': 'PASSWORD', 'TRADE': 'SCAMBIO',
 'EXPORTS': 'ESPORTA', 'IMPORTS': 'IMPORTA', '2P': '2P', '1P': '1P', 'TOTAL': 'TOTALE', 'IM': 'IM', 'EX': 'ES',
 'EX-SET': 'ES-IM', 'READY': 'PRONTO', 'NOTICE': 'AVVISO', 'CUSTOM': 'PERS', 'OPEN': 'APERTO', 'HIDE': 'NASC',
 'CHANGE': 'CAMBIA', 'USE': 'USO', 'NOT USE': 'NON USO', 'START': 'INIZIA', 'EDIT': 'MODIF', 'VS': 'VS',
}
ui_it = []
uijs = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui_strings.json')))
for addr, ln in uijs['strings']:
    o = addr - 0x100000 + 26880
    t = exe[o:o + ln].decode('latin1')
    if t in UI_IT: ui_it.append((addr, UI_IT[t]))
print('UI strings', len(ui_it), 'of', len(uijs['strings']))
with open(OUT, 'wb') as f:
    f.write(b'DOTRIT03')
    f.write(struct.pack('<I', len(newg)))
    for (flag, e), code in newg.items():
        img = to_us(eu_px(e))
        f.write(struct.pack('<H', code)); f.write(bytes(img[i] | (img[i+1] << 4) for i in range(0, 484, 2)))
    f.write(struct.pack('<I', len(msgs)))
    for a, ws in msgs.items():
        f.write(struct.pack('<HH', a, len(ws))); f.write(struct.pack('<%dH' % len(ws), *ws))
    f.write(struct.pack('<I', len(ui_it)))
    for addr, txt in ui_it:
        b = txt.encode('latin1'); f.write(struct.pack('<II', addr, len(b))); f.write(b)
if len(sys.argv) > 6:
    open(sys.argv[6], 'w').write('patched ids: %s\n' % sorted(msgs))
