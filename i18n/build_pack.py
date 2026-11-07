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
msgs = {}
for a, b in sorted(cand.items()):
    t = eu_flatten(im[b])
    if not t: continue
    ws = []
    for x in t:
        if x[0] == 'M': ws += [x[1] & 0x7fff | 0x4000, x[2]]
        else: ws.append((x[1] << 13) | map_code(x[1], x[2]))
    ws[-1] |= 0x8000
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
with open(OUT, 'wb') as f:
    f.write(b'DOTRIT02')
    f.write(struct.pack('<I', len(newg)))
    for (flag, e), code in newg.items():
        img = to_us(eu_px(e))
        f.write(struct.pack('<H', code)); f.write(bytes(img[i] | (img[i+1] << 4) for i in range(0, 484, 2)))
    f.write(struct.pack('<I', len(msgs)))
    for a, ws in msgs.items():
        f.write(struct.pack('<HH', a, len(ws))); f.write(struct.pack('<%dH' % len(ws), *ws))
if len(sys.argv) > 5:
    open(sys.argv[5], 'w').write('patched ids: %s\n' % sorted(msgs))
