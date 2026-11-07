from glyphs import *
from parse_msgs import *
from align import ut_, et_
OFFS=26880;VR=0x100000
us=open('iso/SLUS_205.15','rb').read()
va=lambda a: OFFS+(a-VR)
uimg=us[va(0x2F8DEC):va(0x31C070)]
d=open('eu/MSG_E.DAT','rb').read(); body=d[0x100:]
_,_,_,img_off,_=eu_msgs('eu/MSG_E.DAT')
EIMG=img_off+22   # glyph 0 start guess
def ug(c): return glyph_px(uimg[c*G:(c+1)*G])
def eg(c): return glyph_px(body[EIMG+c*G-0:EIMG+c*G+G])
def line_img(tokens,getg,maxv):
    cells=[]
    for x in tokens:
        if x[0]=='M': cells.append(None); continue
        w=12 if x[0] else 22
        cells.append((getg(x[1]),w))
    return cells
def render_msgs(items,path,scale=2):
    """items: list of (tokens,getg,maxv); each a row of glyphs"""
    rows=[]
    W=0
    for toks,getg,maxv in items:
        xs=0; segs=[]
        for x in toks:
            if x[0]=='M': segs.append((None,10)); xs+=10; continue
            w=12 if x[0] else 22
            segs.append((getg(x[1]),w)); xs+=w
        W=max(W,xs); rows.append((segs,maxv))
    H=len(rows)*24
    img=[[30]*(W+4) for _ in range(H)]
    for r,(segs,maxv) in enumerate(rows):
        x0=2
        for px,w in segs:
            if px is None: x0+=w; continue
            for y in range(22):
                for x in range(w):
                    v=px[y*22+x+((22-w)//2 if w<22 else 0)] if (y*22+x)<len(px) else 0
                    img[r*24+y+1][x0+x]=min(255,30+v*int(225/maxv))
            x0+=w
    big=[]
    for r in img:
        rr=[v for v in r for _ in range(scale)]; big+=[rr]*scale
    png(path,(W+4)*scale,H*scale,big)
if __name__=='__main__':
    import sys
    items=[]
    for i in (1700,1701,2000,2001,2600,3000):
        items.append((ut_[i],ug,13))
    render_msgs(items,'us_msgs.png')
    items=[(et_[j],eg,15) for j in (1700,1701,2000,2001,2600,3000)]
    render_msgs(items,'eu_msgs.png')
