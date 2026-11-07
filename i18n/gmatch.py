import re, difflib, collections, pickle
from decode import *
def norm(t): return re.sub(r'[^a-z0-9 ]','',re.sub(r'~',' ',t.lower())).split()
def run(lo=30,hi=3073, thr=0.82):
    us_t={i:norm(us_txt(um[i])) for i in range(lo,hi)}
    eu_t=[norm(eu_txt(m)) for m in em]
    inv=collections.defaultdict(set)
    for j,ws in enumerate(eu_t):
        for w in set(ws): inv[w].add(j)
    res={}
    for i,ws in us_t.items():
        if len(ws)<3: continue
        cnt=collections.Counter()
        for w in set(ws):
            js=inv.get(w)
            if js and len(js)<400:
                for j in js: cnt[j]+=1
        best=(0,None)
        for j,c in cnt.most_common(12):
            r=difflib.SequenceMatcher(None,ws,eu_t[j],autojunk=False).ratio()
            if r>best[0]: best=(r,j)
        if best[0]>=thr: res[i]=best
    return res,us_t
if __name__=='__main__':
    res,us_t=run()
    print('matched',len(res))
    import collections
    print('by range',[(lo,sum(1 for i in res if lo<=i<lo+200)) for lo in range(0,3073,200)])
    pickle.dump(res,open('gmatch.pkl','wb'))

def run_all(lo=30, hi=3073, thr=0.82):
    us_t = {i: norm(us_txt(um[i])) for i in range(lo, hi)}
    eu_t = [norm(eu_txt(m)) for m in em]
    inv = collections.defaultdict(set)
    for j, ws in enumerate(eu_t):
        for w in set(ws): inv[w].add(j)
    res = {}
    for i, ws in us_t.items():
        if len(ws) < 3: continue
        cnt = collections.Counter()
        for w in set(ws):
            js = inv.get(w)
            if js and len(js) < 400:
                for j in js: cnt[j] += 1
        cands = []
        for j, c in cnt.most_common(12):
            r = difflib.SequenceMatcher(None, ws, eu_t[j], autojunk=False).ratio()
            if r >= thr: cands.append((r, j, len(ws)))
        if cands:
            top = max(c[0] for c in cands)
            res[i] = [c for c in cands if c[0] >= top - 0.03]
    return res
