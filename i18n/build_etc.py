#!/usr/bin/env python3
"""Italian menu pictures: rewrites the labels of the US TEXETC.MRG (title menu) and writes it_TEXETC.MRG.
usage: build_etc.py <US TEXETC.MRG> <out it_TEXETC.MRG> [preview.png]"""
import sys
from texrender import *
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SRC, OUT = sys.argv[1:3]
d = bytearray(open(SRC, 'rb').read())
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
ITEM1 = 0x476a0
w, h, pal, px = pixels_gs(d, ITEM1)
px = bytearray(px)
WHITE, BLACK = 2, 1
def erase(x0, x1, y0, y1, ys, period):
    """fill the rectangle with the band's own brick pattern from a clean strip of `period` rows starting at row ys"""
    for y in range(y0, y1):
        sy = ys + ((y - ys) % period)
        for x in range(x0, x1):
            px[y * w + x] = px[sy * w + x]
def draw(text, cx, cy, maxw, cap_h=17, left=None, white=WHITE, shadow_idx=BLACK):
    size = 30
    while size > 8:
        f = ImageFont.truetype(FONT, size)
        l, t, r, b = f.getbbox('H' + text)
        if (b - t) <= cap_h + 2: break
        size -= 1
    f = ImageFont.truetype(FONT, size)
    l, t, r, b = f.getbbox(text)
    tw, th = r - l, b - t
    tmp = Image.new('L', (tw + 4, th + 4), 0)
    ImageDraw.Draw(tmp).text((2 - l, 2 - t), text, font=f, fill=255)
    if tw > maxw:                                   # squeeze sideways to fit
        tmp = tmp.resize((maxw + 4, th + 4), Image.LANCZOS); tw = maxw
    m = Image.new('L', (w, h), 0)
    x0 = (left if left is not None else cx - tw // 2) - 2
    m.paste(tmp, (x0, cy - th // 2 - 2))
    mask = m.point(lambda v: 255 if v >= 110 else 0)
    ink = mask.load()
    shadow = Image.new('L', (w, h), 0)
    sh = shadow.load()
    # outline: 1px all around + a 1px shadow down-right
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if ink[x, y]:
                for dy in (-1, 0, 1, 2):
                    for dx in (-1, 0, 1, 2):
                        if (dx <= 1 and dy <= 1) or (dx == 2 and dy == 2) or (dx == 2 and dy >= 0) or (dy == 2 and dx >= 0):
                            sh[x + dx, y + dy] = 255
    for y in range(h):
        for x in range(w):
            if sh[x, y] and not ink[x, y]: px[y * w + x] = shadow_idx
    for y in range(h):
        for x in range(w):
            if ink[x, y]: px[y * w + x] = white
    return size
labels = [("NUOVA PARTITA", 0), ("CONTINUA", 1), ("DUELLO PERSONALIZZATO", 2), ("SCAMBIO", 3)]
for text, band in labels:
    by = band * 48
    erase(16, 240, by + 8, by + 40, by + 38, 8)      # text rows were 15..31 with outline: clear 8..39
    s = draw(text, 128, by + 23, 214)
    print('label', text, 'font size', s)
# "PRESS START BUTTON" (title, rows 188..214, cols 0..196): the game's own cream-coloured text on black
for y in range(192, 208):                          # only the text rows: the frame ornament starts at row 208
    for x in range(0, 200): px[y * w + x] = 0
print('label', 'Premi tasto START', draw("PREMI TASTO START", 0, 199, 178, cap_h=11, left=2, white=55))
encode_gs(d, ITEM1, px)

# ---- the Rose cards (item 2, 512x384): titles and the three-line description of both cards
from PIL import ImageFont as _F
ITEM2 = 0x58000
w2, h2, pal2, px2 = pixels_gs(bytes(d), ITEM2); px2 = bytearray(px2)
def lum(i):
    r, g, b, a = rgb(pal2[i]); return r + g + b
def common(region, test):
    import collections
    c = collections.Counter(px2[y * w2 + x] for (x0, y0, x1, y1) in [region] for y in range(y0, y1) for x in range(x0, x1) if test(lum(px2[y * w2 + x])))
    return c.most_common(1)[0][0]
def wipe(x0, y0, x1, y1, sample_x):
    for y in range(y0, y1):
        bgi = px2[y * w2 + sample_x]
        for x in range(x0, x1): px2[y * w2 + x] = bgi
def put(text, cx, cy, size, idx, maxw, font='/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf', left=None):
    f = _F.truetype(font, size); l, t, r, b = f.getbbox(text); tw, th = r - l, b - t
    tmp = Image.new('L', (tw + 4, th + 4), 0); ImageDraw.Draw(tmp).text((2 - l, 2 - t), text, font=f, fill=255)
    if tw > maxw: tmp = tmp.resize((maxw + 4, th + 4), Image.LANCZOS); tw = maxw
    m = Image.new('L', (w2, h2), 0); x0 = (left if left is not None else cx - tw // 2) - 2
    m.paste(tmp, (x0, cy - th // 2 - 2)); mk = m.load()
    for y in range(h2):
        for x in range(w2):
            if mk[x, y] >= 120: px2[y * w2 + x] = idx
for off, name, dark_title in ((0, "Rosa Rossa", False), (256, "Rosa Bianca", True)):
    title_idx = common((70 + off, 26, 180 + off, 44), (lambda v: v < 200) if dark_title else (lambda v: v > 640))
    desc_idx = common((30 + off, 303, 236 + off, 344), lambda v: v < 200)
    wipe(28 + off, 25, 232 + off, 46, 26 + off)
    put(name, 124 + off, 36, 19, title_idx, 150)
    wipe(26 + off, 302, 238 + off, 345, 24 + off)
    for k, line in enumerate(('La Carta Rosa \u00e8 la "Carta Chiave Segreta".', '8 Rose Rosse e 8 Rose Bianche cadranno', 'nel "GOD".')):
        put(line, 0, 311 + 13 * k, 12, desc_idx, 204, left=31 + off)
encode_gs(d, ITEM2, px2)
open(OUT, 'wb').write(d)
if len(sys.argv) > 3:
    img = Image.new('RGB', (w, h))
    for y in range(h):
        for x in range(w):
            r, g, b, a = rgb(pal[px[y * w + x]]); img.putpixel((x, y), (r, g, b))
    img.save(sys.argv[3])
    im2 = Image.new('RGB', (w2, h2)); p2 = im2.load()
    for y in range(h2):
        for x in range(w2):
            r, g, b, a = rgb(pal2[px2[y * w2 + x]]); p2[x, y] = (r, g, b)
    im2.save(sys.argv[3].replace('.png', '_rose.png'))
