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
open(OUT, 'wb').write(d)
if len(sys.argv) > 3:
    img = Image.new('RGB', (w, h))
    for y in range(h):
        for x in range(w):
            r, g, b, a = rgb(pal[px[y * w + x]]); img.putpixel((x, y), (r, g, b))
    img.save(sys.argv[3])
