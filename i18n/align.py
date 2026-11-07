import difflib, collections
from parse_msgs import *
um,uw,ut=us_msgs(); em,ew,et,_,_=eu_msgs('eu/MSG_E.DAT')
def toks(m):
    """list of (flag, code) with macro words as ('M', code, ref)"""
    out=[];i=0
    while i<len(m):
        w=m[i]
        if w&0x4000:
            out.append(('M',w&0x3fff, m[i+1] if i+1<len(m) else 0)); i+=2
        else:
            out.append((w>>13&1, w&0x1fff)); i+=1
    return out
ut_=[toks(m) for m in um]; et_=[toks(m) for m in em]
sig=lambda t: tuple(x[0] if x[0]=='M' else x[0] for x in t)
us_s=[sig(t) for t in ut_]; eu_s=[sig(t) for t in et_]
sm=difflib.SequenceMatcher(None,us_s,eu_s,autojunk=False)
pairs=[]
for b in sm.get_matching_blocks():
    for k in range(b.size): pairs.append((b.a+k,b.b+k))
print('anchor pairs',len(pairs))
gmap={}
def learn(pairs):
    co=collections.defaultdict(collections.Counter)
    for a,b in pairs:
        ta,tb=ut_[a],et_[b]
        if len(ta)!=len(tb): continue
        for x,y in zip(ta,tb):
            if x[0]!='M' and y[0]!='M': co[x[1]][y[1]]+=1
    m={}
    for g,c in co.items():
        (best,n),=c.most_common(1)
        m[g]=(best,n,sum(c.values()))
    return m
gm=learn(pairs)
print('glyphs learned',len(gm))
conf=sum(1 for g,(b,n,t) in gm.items() if n==t)
print('fully consistent',conf)
import pickle; pickle.dump((pairs,gm),open('stage1.pkl','wb'))
