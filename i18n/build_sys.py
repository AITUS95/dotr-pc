#!/usr/bin/env python3
"""Italian labels of the duel HUD (PLAYER / ENEMY / Effect) in the US TEXSYS.MRG, taken from the Italian
European TEXSYS file where the picture is the same, drawn here where the European one is laid out differently.
usage: build_sys.py <US TEXSYS.MRG> <EU Italian TEXSYS.MRG> <out it_TEXSYS.MRG> [preview.png]"""
import sys
from texrender import *
from PIL import Image, ImageDraw, ImageFont
SRC, EUF, OUT = sys.argv[1:4]
d = bytearray(open(SRC, 'rb').read()); eu = open(EUF, 'rb').read()
def items_of(b):
    pos = []; i = 0
    while True:
        i = b.find(b'RH2\0', i)
        if i < 0: break
        pos.append(i); i += 16
    return pos
pu = items_of(bytes(d))[7]; pe = items_of(eu)[7]
w, h, palu, pxu = pixels_gs(bytes(d), pu); pxu = bytearray(pxu)
w2, h2, pale, pxe = pixels_gs(eu, pe)
cols = [rgb(e)[:3] for e in palu]
cache = {}
def nearest(rgb3):
    if rgb3 in cache: return cache[rgb3]
    best = min(range(256), key=lambda i: sum((a - b) ** 2 for a, b in zip(cols[i], rgb3)))
    cache[rgb3] = best; return best
# the four plates PLAYER / ENEMY / PLAYER / ENEMY (x 0..190, y 100..115) from the Italian picture
for y in range(100, 116):
    for x in range(0, 191):
        pxu[y * w + x] = nearest(rgb(pale[pxe[y * w + x]])[:3])
# "Effect" plate: wipe the word row by row from the clean strip at its left, draw "Effetto"
X0, X1, Y0, Y1 = 197, 252, 101, 121
text_idx = pxu[108 * w + 199]
for y in range(Y0, Y1):
    bg = pxu[y * w + 196]
    for x in range(X0, X1): pxu[y * w + x] = bg
f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', 17)
l, t, r, b = f.getbbox('Effetto'); tw, th = r - l, b - t
tmp = Image.new('L', (tw + 4, th + 4), 0); ImageDraw.Draw(tmp).text((2 - l, 2 - t), 'Effetto', font=f, fill=255)
maxw = X1 - X0 - 2
if tw > maxw: tmp = tmp.resize((maxw + 4, th + 4), Image.LANCZOS); tw = maxw
cx = (X0 + X1) // 2; cy = (Y0 + Y1) // 2
m = Image.new('L', (w, h), 0); m.paste(tmp, (cx - tw // 2 - 2, cy - th // 2 - 2))
mk = m.load()
for y in range(h):
    for x in range(w):
        if mk[x, y] >= 120: pxu[y * w + x] = text_idx
encode_gs(d, pu, pxu)
open(OUT, 'wb').write(d)
if len(sys.argv) > 4:
    im = Image.new('RGB', (w, h)); pix = im.load()
    for y in range(h):
        for x in range(w): pix[x, y] = cols[pxu[y * w + x]]
    im.save(sys.argv[4])
