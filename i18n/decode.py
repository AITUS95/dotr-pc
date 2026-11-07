import difflib
from parse_msgs import *
import pair2
E2U={1:112}
for k in range(26): E2U[5+k]=86+k; E2U[31+k]=115+k
for k in range(10): E2U[57+k]=143+k
E2U.update({3:82,67:162,70:154,71:155,72:156,73:157,74:158,75:159,76:141,77:142,78:160,114:164,115:113,116:114,117:153,118:337})
U2E={v:k for k,v in E2U.items()}
CH={}
for k in range(26): CH[5+k]=chr(65+k); CH[31+k]=chr(97+k)
for k in range(9): CH[57+k]=str(k+1)
CH.update({66:'0',1:' ',3:',',114:'.',67:'-',70:'"',71:'#',72:'$',73:'%',74:'&',75:"'",76:'(',77:')',78:'=',115:'[',116:']',117:'!',118:'?'})
um,uw,ut=us_msgs('iso/SLUS_205.15'); em,_,_,_,_=eu_msgs('eu/MSG_E.DAT'); im,_,_,_,_=eu_msgs('eu/MSG_I.DAT')
uf=pair2.make_flat(um); ef=pair2.make_flat(em); iff=pair2.make_flat(im)
def us_txt(m): return ''.join(CH.get(U2E.get(c,-1),'~') for f,c in uf(m))
def eu_txt(m,fl=ef): return ''.join(CH.get(c,'~') for f,c in fl(m))
