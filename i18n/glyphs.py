import zlib,struct
G=242
def png(path,w,h,rows):
    raw=b''.join(b'\0'+bytes(r) for r in rows)
    def ch(t,dat):
        c=struct.pack('>I',len(dat))+t+dat; return c+struct.pack('>I',zlib.crc32(t+dat)&0xffffffff)
    open(path,'wb').write(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',w,h,8,0,0,0,0))+ch(b'IDAT',zlib.compress(raw))+ch(b'IEND',b''))
def glyph_px(blk):
    out=[]
    for x in blk: out+=[x&15,x>>4]
    return out[:484]
def sheet(blocks,path,cols=16,scale=2,maxv=15,start=0):
    n=len(blocks); rows_g=(n+cols-1)//cols; GW=GH=22
    W=cols*(GW+2); H=rows_g*(GH+2)
    img=[[30]*W for _ in range(H)]
    for gi,blk in enumerate(blocks):
        px=glyph_px(blk); gx=(gi%cols)*(GW+2); gy=(gi//cols)*(GH+2)
        for y in range(GH):
            for x in range(GW):
                img[gy+y][gx+x]=min(255,30+px[y*GW+x]*int(225/maxv))
    big=[]
    for r in img:
        rr=[v for v in r for _ in range(scale)]; big+=[rr]*scale
    png(path,W*scale,H*scale,big)
