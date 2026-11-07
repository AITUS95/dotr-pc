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
# ---- pairing US id -> EU id (UI texts and card names), from the alignment of the English texts
res, _ = pickle.load(open('stage2.pkl', 'rb'))
def us_as_eu(t):
    return [('M',) if x[0] == 'M' else (None if x[1] not in U2E else U2E[x[1]]) for x in t]
cand = {}
for a, b in res:
    if not (30 <= a < 1576 and abs(b - a) <= 6): continue
    ta, tb = toks(um[a]), toks(em[b])
    if len(ta) != len(tb): continue
    xs = us_as_eu(ta); known = [(x, y[1]) for x, y in zip(xs, tb) if y[0] != 'M' and x is not None and x != ('M',)]
    if len(known) < max(2, len(ta) // 2): continue
    ok = sum(1 for x, y in known if x == y) / len(known)
    if ok >= 0.9: cand[a] = b
n0 = len(cand)

# ---- Italian messages are written without macros (expanded here), so they stand alone next to the English ones
def eu_flatten(words, depth=0):
    """list of tokens (flag, code) of an EU-I message with every macro expanded"""
    out = []; i = 0
    while i < len(words):
        w = words[i]
        if w & 0x4000:
            w2 = words[i+1]; tgt = im[w2 & 0x3fff]
            count = w & 0x3f; off = (w >> 6) & 0x7f
            q = off
            while count > 0 and q < len(tgt):
                sub = eu_flatten_one(tgt, q, depth + 1)
                toks_, n = sub
                out += toks_; count -= n; q += n
                if tgt[q-1] & 0x8000: break
            i += 2
        else:
            out.append((w >> 13 & 1, w & 0x1fff)); i += 1
    return out
def eu_flatten_one(words, q, depth):
    if depth > 8: return [], 1
    w = words[q]
    if w & 0x4000:
        toks_ = eu_flatten(words[q:q+2], depth)
        return toks_, 2
    return [(w >> 13 & 1, w & 0x1fff)], 1
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
    ws = [((f << 13) | map_code(f, c)) for f, c in t]
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
