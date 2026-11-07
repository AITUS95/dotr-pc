import struct
OFF=26880;VR=0x100000
def us_msgs(path='iso/SLUS_205.15'):
    d=open(path,'rb').read()
    va=lambda a: OFF+(a-VR)
    tab=struct.unpack_from('<3073I',d,va(0x2D19D0))
    words=struct.unpack_from('<74252H',d,va(0x2D49D4))
    ends=list(tab[1:])+[len(words)]
    return [words[s:e] for s,e in zip(tab,ends)], words, tab
def eu_msgs(path):
    d=open(path,'rb').read(); body=d[0x100:]
    nt=4111
    tab=struct.unpack_from('<%dI'%nt,body,0)
    bs=nt*4
    # blob end = last message end
    allw=struct.unpack_from('<%dH'%((len(body)-bs)//2),body,bs)
    i=tab[-1]
    while not (allw[i]&0x8000): i+=1
    end=i+1
    ends=list(tab[1:])+[end]
    return [allw[s:e] for s,e in zip(tab,ends)], allw[:end], tab, bs+end*2, body
