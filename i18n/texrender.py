import struct,sys
sys.path.insert(0,'/tmp/claude-1000/-home-aitus--claude-spares-spare-uYBWet/477a41e3-a70e-41c0-a582-cac9997c0431/scratchpad')
from glyphs import png
def align_items(d):
    pos=0; out=[]
    while pos+0x60<=len(d):
        if d[pos:pos+4]!=b'RH2\0': break
        size=struct.unpack_from('<I',d,pos+8)[0]; out.append(pos); pos=(pos+size+0x7ff)&~0x7ff
    return out
def info(d,pos):
    doff,dsize=struct.unpack_from('<II',d,pos+0x10)
    psm=struct.unpack_from('<H',d,pos+0x50)[0]; w,h=struct.unpack_from('<HH',d,pos+0x54); pc=struct.unpack_from('<I',d,pos+0x58)[0]
    pk=[struct.unpack_from('<I',d,pos+doff+k*0x30+4)[0] for k in range(pc)]
    return psm,w,h,pk
def swz(i): return (i&0xe7)|((i&8)<<1)|((i&16)>>1)
def pixels(d,pos):
    psm,w,h,pk=info(d,pos)
    ents=struct.unpack_from('<256H',d,pos+pk[0]+0x60)
    pal=[ents[swz(i)] for i in range(256)]
    raw=bytearray()
    for a in pk[1:]:
        raw+=d[pos+a+0x60:pos+a+0x60+0x2000]
    return psm,w,h,pal,raw[:w*h],pk
def rgb(e): return ((e&31)<<3,((e>>5)&31)<<3,((e>>10)&31)<<3,(e>>15)*255)
def render(d,pos,path,scale=1):
    psm,w,h,pal,raw,pk=pixels(d,pos)
    import zlib
    rows=[]
    for y in range(h):
        row=bytearray()
        for x in range(w):
            r,g,b,a=rgb(pal[raw[y*w+x]]) if y*w+x<len(raw) else (0,0,0,0)
            row+=bytes((r,g,b))
        rows.append(b'\0'+bytes(row))
    def ch(t,dat):
        c=struct.pack('>I',len(dat))+t+dat; return c+struct.pack('>I',zlib.crc32(t+dat)&0xffffffff)
    open(path,'wb').write(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+ch(b'IDAT',zlib.compress(b''.join(rows)))+ch(b'IEND',b''))
def unswizzle8_index(x,y,w):
    block_location=(y&~0xf)*w+(x&~0xf)*2
    swap_selector=(((y+2)>>2)&1)*4
    posY=(((y&~3)>>1)+(y&1))&7
    column_location=posY*w*2+((x+swap_selector)&7)*4
    byte_num=((y>>1)&1)+((x>>2)&2)
    return block_location+column_location+byte_num
def unswizzle8(raw,w,h):
    out=bytearray(w*h)
    for y in range(h):
        for x in range(w):
            i=unswizzle8_index(x,y,w)
            out[y*w+x]=raw[i] if i<len(raw) else 0
    return out
def render2(d,pos,path):
    import zlib
    psm,w,h,pal,raw,pk=pixels(d,pos)
    px=unswizzle8(raw,w,h)
    rows=[]
    for y in range(h):
        row=bytearray()
        for x in range(w):
            r,g,b,a=rgb(pal[px[y*w+x]]); row+=bytes((r,g,b))
        rows.append(b'\0'+bytes(row))
    def ch(t,dat):
        c=struct.pack('>I',len(dat))+t+dat; return c+struct.pack('>I',zlib.crc32(t+dat)&0xffffffff)
    open(path,'wb').write(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+ch(b'IDAT',zlib.compress(b''.join(rows)))+ch(b'IEND',b''))

# ---- exact GS memory model for the pictures: chunks are 64x32 PSMCT32 rects, one per page; read back as PSMT8
BT=[[0,1,4,5,16,17,20,21],[2,3,6,7,18,19,22,23],[8,9,12,13,24,25,28,29],[10,11,14,15,26,27,30,31]]
CW32=[0,1,4,5,8,9,12,13, 2,3,6,7,10,11,14,15]
CT8=[
 [0,4,16,20,32,36,48,52,2,6,18,22,34,38,50,54],
 [8,12,24,28,40,44,56,60,10,14,26,30,42,46,58,62],
 [33,37,49,53,1,5,17,21,35,39,51,55,3,7,19,23],
 [41,45,57,61,9,13,25,29,43,47,59,63,11,15,27,31],
 [96,100,112,116,64,68,80,84,98,102,114,118,66,70,82,86],
 [104,108,120,124,72,76,88,92,106,110,122,126,74,78,90,94],
 [65,69,81,85,97,101,113,117,67,71,83,87,99,103,115,119],
 [73,77,89,93,105,109,121,125,75,79,91,95,107,111,123,127],
 [128,132,144,148,160,164,176,180,130,134,146,150,162,166,178,182],
 [136,140,152,156,168,172,184,188,138,142,154,158,170,174,186,190],
 [161,165,177,181,129,133,145,149,163,167,179,183,131,135,147,151],
 [169,173,185,189,137,141,153,157,171,175,187,191,139,143,155,159],
 [224,228,240,244,192,196,208,212,226,230,242,246,194,198,210,214],
 [232,236,248,252,200,204,216,220,234,238,250,254,202,206,218,222],
 [193,197,209,213,225,229,241,245,195,199,211,215,227,231,243,247],
 [201,205,217,221,233,237,249,253,203,207,219,223,235,239,251,255]]
def ct32_word(x,y):          # (x,y) inside a 64x32 page -> word index in the 2048-word page
    bx,by=x>>3,y>>2          # blocks are 8 wide, 8 tall: grid 8x4  (y>>3)
    by=y>>3; blk=BT[by][bx]
    return blk*64+((y>>1)&3)*16+CW32[(y&1)*8+(x&7)]
def t8_byte(x,y):            # (x,y) inside a 128x64 page -> byte index in the 8192-byte page
    bx,by=x>>4,y>>4; blk=BT[by][bx]
    return blk*256+CT8[y&15][x&15]
def pixels_gs(d,pos):
    psm,w,h,pk=info(d,pos)
    ents=struct.unpack_from('<256H',d,pos+pk[0]+0x60)
    pal=[ents[swz(i)] for i in range(256)]
    pages=[]
    for a in pk[1:]:
        chunk=d[pos+a+0x60:pos+a+0x60+0x2000]
        page=bytearray(0x2000)
        for y in range(32):
            for x in range(64):
                wd=ct32_word(x,y)
                page[wd*4:wd*4+4]=chunk[(y*64+x)*4:(y*64+x)*4+4]
        pages.append(page)
    ppr=(w+127)//128           # pages per row
    out=bytearray(w*h)
    for y in range(h):
        for x in range(w):
            pg=(y//64)*ppr+(x//128)
            if pg<len(pages): out[y*w+x]=pages[pg][t8_byte(x%128,y%64)]
    return w,h,pal,out
def render3(d,pos,path):
    import zlib
    w,h,pal,px=pixels_gs(d,pos)
    rows=[]
    for y in range(h):
        row=bytearray()
        for x in range(w):
            r,g,b,a=rgb(pal[px[y*w+x]]); row+=bytes((r,g,b))
        rows.append(b'\0'+bytes(row))
    def ch(t,dat):
        c=struct.pack('>I',len(dat))+t+dat; return c+struct.pack('>I',zlib.crc32(t+dat)&0xffffffff)
    open(path,'wb').write(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+ch(b'IDAT',zlib.compress(b''.join(rows)))+ch(b'IEND',b''))

def encode_gs(d,pos,px):
    """write the 8-bit index image px (w*h) back into the item at pos (inverse of pixels_gs); d is a bytearray"""
    psm,w,h,pk=info(d,pos)
    ppr=(w+127)//128; npages=len(pk)-1
    pages=[bytearray(0x2000) for _ in range(npages)]
    for y in range(h):
        for x in range(w):
            pg=(y//64)*ppr+(x//128)
            if pg<npages: pages[pg][t8_byte(x%128,y%64)]=px[y*w+x]
    for k,page in enumerate(pages):
        chunk=bytearray(0x2000)
        for y in range(32):
            for x in range(64):
                wd=ct32_word(x,y)
                chunk[(y*64+x)*4:(y*64+x)*4+4]=page[wd*4:wd*4+4]
        a=pk[k+1]
        d[pos+a+0x60:pos+a+0x60+0x2000]=chunk
