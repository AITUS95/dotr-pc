import difflib, collections, pickle, bisect
from align import ut_, et_, pairs as anchors, gm as gm0
NU,NE=len(ut_),len(et_)
def eu_str(t): return ''.join('\x01' if x[0]=='M' else chr(0x100+x[1]) for x in t)
def us_str(t,gm):
    return ''.join('\x01' if x[0]=='M' else (chr(0x100+gm[x[1]][0]) if x[1] in gm else chr(0x2000+x[1])) for x in t)
es=[eu_str(t) for t in et_]
def run(gm, anchors, band=80):
    ua=[a for a,b in anchors]; 
    def offs(i):
        k=bisect.bisect_left(ua,i)
        nxt=anchors[k][1]-anchors[k][0] if k<len(anchors) else anchors[-1][1]-anchors[-1][0]
        prv=anchors[k-1][1]-anchors[k-1][0] if k>0 else 0
        return min(prv,nxt),max(prv,nxt)
    us_=[us_str(t,gm) for t in ut_]
    NEG=-1e9; GAP=-0.15
    # banded NW
    import math
    best={}  # (i,j)->score
    ptr={}
    def sim(i,j):
        a,b=us_[i],es[j]
        if not a or not b: return 0.0
        sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
        if sm.real_quick_ratio()<0.5 or sm.quick_ratio()<0.5: return 0.0
        return sm.ratio()
    # DP over i with window of j
    prev={}
    prevptr=[]
    rows=[]
    jl=lambda i:max(0,i+offs(i)[0]-band); jh=lambda i:min(NE,i+offs(i)[1]+band+1)
    # represent row i as dict j->score for j in window; also j=-1 style skip handled by transitions
    S=[None]*(NU+1); P=[None]*(NU+1)
    S[0]={j:GAP*j for j in range(0,min(NE,band)+1)}; P[0]={j:('L',j-1) for j in S[0]}
    for i in range(1,NU+1):
        lo,hi=jl(i),jh(i)+1
        row={};prow={}
        pr=S[i-1]
        js=sorted(set(range(lo,min(hi,NE)+1))|set(pr)|{j+1 for j in pr if j+1<=NE})
        for j in js:
            cand=[]
            if j in pr: cand.append((pr[j]+GAP,'U'))            # skip US msg i-1
            if j-1 in pr and j-1<NE and j>=1:
                s=sim(i-1,j-1)
                cand.append((pr[j-1]+ (s*2-0.9 if s>=0.45 else -1.0),'D'))
            if j-1 in row: cand.append((row[j-1]+GAP,'L'))      # skip EU msg
            if cand:
                v,p=max(cand); row[j]=v; prow[j]=p
        if row:
            bst=max(row.values()); 
            row={j:v for j,v in row.items() if v>=bst-8}; prow={j:prow[j] for j in row}
        S[i]=row;P[i]=prow
    # traceback from best final
    j=max(S[NU],key=lambda k:S[NU][k]); i=NU
    res=[]
    while i>0 or j>0:
        p=P[i].get(j)
        if p is None: break
        if p=='D': 
            res.append((i-1,j-1)); i-=1;j-=1
        elif p=='U': i-=1
        else: j-=1
    res.reverse()
    return res, us_
def learn(res, us_,thr=0.8):
    co=collections.defaultdict(collections.Counter); good=0
    for a,b in res:
        ta,tb=ut_[a],et_[b]
        if len(ta)!=len(tb): continue
        # use only near-exact
        if sum(1 for x,y in zip(ta,tb) if x[0]==y[0])<len(ta)*0.9: continue
        good+=1
        for x,y in zip(ta,tb):
            if x[0]!='M' and y[0]!='M': co[x[1]][y[1]]+=1
    m={}
    for g,c in co.items():
        best,n=c.most_common(1)[0]
        if n>=2 and n>=0.8*sum(c.values()): m[g]=(best,n,sum(c.values()))
    return m,good
if __name__=='__main__':
    gm=dict(gm0); anchors2=anchors
    for it in range(3):
        res,us_=run(gm,anchors2)
        # quality: exact translated equality
        exact=sum(1 for a,b in res if us_[a]==es[b])
        gm2,good=learn(res,us_)
        print('iter',it,'aligned',len(res),'exact-text',exact,'glyphs',len(gm2),'good pairs',good)
        gm=gm2; anchors2=[(a,b) for a,b in res if us_[a]==es[b]] or anchors2
        pickle.dump((res,gm),open('stage2.pkl','wb'))
