import difflib
from parse_msgs import *
def make_flat(msgs):
    def flat(words, depth=0):
        out=[]; i=0
        while i<len(words):
            w=words[i]
            if w&0x4000:
                if i+1>=len(words): break
                tgt=msgs[words[i+1]&0x3fff] if (words[i+1]&0x3fff)<len(msgs) else []
                count=w&0x3f; q=(w>>6)&0x7f
                while count>0 and q<len(tgt) and depth<8:
                    w0=tgt[q]
                    if w0&0x4000:
                        out+=flat(tgt[q:q+2],depth+1); n=2
                    else:
                        out.append((w0>>13&1,w0&0x1fff)); n=1
                    count-=n; q+=n
                    if tgt[q-1]&0x8000: break
                i+=2
            else:
                out.append((w>>13&1,w&0x1fff)); i+=1
        return out
    return flat
def pairs(us_exe,msg_e,E2U,lo=30,hi=1576,win=(-8,10),thr=0.85):
    um,uw,ut=us_msgs(us_exe); em,_,_,_,_=eu_msgs(msg_e)
    uf=make_flat(um); ef=make_flat(em)
    U2E={v:k for k,v in E2U.items()}
    def us_s(m): return ''.join(chr(0x100+U2E[c]) if c in U2E else '\x01' for f,c in uf(m))
    def eu_s(m): return ''.join(chr(0x100+c) if c in E2U else '\x02' for f,c in ef(m))
    uS={i:us_s(um[i]) for i in range(lo,hi)}; eS=[eu_s(m) for m in em]
    out={}
    for i in range(lo,hi):
        a=uS[i]
        if len(a.replace('\x01',''))<2: continue
        best=(0,None)
        for j in range(max(0,i+win[0]),min(len(em),i+win[1])):
            b=eS[j]
            if not b: continue
            # wildcard-aware ratio
            sm=difflib.SequenceMatcher(None,a,b,autojunk=False); r=sm.ratio()
            # unknown glyphs on either side count as matches: compare lengths of known parts
            if r>best[0]: best=(r,j)
        if best[0]>=thr: out[i]=(best[1],best[0])
    return out
