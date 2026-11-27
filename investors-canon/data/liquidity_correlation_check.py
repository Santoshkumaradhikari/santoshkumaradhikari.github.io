# Re-check of Chapter 0.1, Table 0.1.1: block-shuffle test and the 60-combination search. Run: python3 liquidity_correlation_check.py
# Robustness check for Chapter 0.1's correlations (Table 0.1.1)
import csv, math, random
r=sorted(csv.DictReader(open(__import__('pathlib').Path(__file__).with_name('regime-test-data-2015-2026.csv'))),key=lambda x:x['month'])
n=len(r)
cg=[float(x['cg']) for x in r]; dg=[float(x['dg']) for x in r]; ib=[float(x['ib']) for x in r]; nx=[float(x['nepse']) for x in r]
def corr(x,y):
    p=[(a,b) for a,b in zip(x,y) if a is not None and b is not None]
    mx=sum(a for a,_ in p)/len(p); my=sum(b for _,b in p)/len(p)
    sxy=sum((a-mx)*(b-my) for a,b in p); sx=math.sqrt(sum((a-mx)**2 for a,_ in p)); sy=math.sqrt(sum((b-my)**2 for _,b in p))
    return sxy/sx/sy
lag=lambda a,k:[None]*k+a[:len(a)-k] if k else a
def series(nx):
    ch12=[None]*4+[nx[i]/nx[i-4]-1 for i in range(4,n)]
    f12=[nx[i+4]/nx[i]-1 for i in range(n-4)]+[None]*4
    f6=[nx[i+2]/nx[i]-1 for i in range(n-2)]+[None]*2
    return {'ch12':ch12,'fwd12':f12,'fwd6':f6}
dcg=[None]*4+[cg[i]-cg[i-4] for i in range(4,n)]
X={'cg':cg,'dg':dg,'ib':ib,'dcg':dcg}
def allc(nx):
    Y=series(nx); out={}
    for a,x in X.items():
        for L in range(5):
            for b,y in Y.items(): out[(a,L,b)]=corr(lag(x,L),y)
    return out
obs=allc(nx)
table=[('dcg',0,'ch12'),('dg',1,'ch12'),('ib',2,'ch12'),('ib',0,'fwd6'),('cg',0,'ch12'),('cg',0,'fwd12')]
# Null: rebuild NEPSE from its own quarterly returns in shuffled blocks of 4 quarters (keeps
# within-year momentum, breaks the link with the NRB series). Compare each table entry and the
# best of all 60 combinations tried.
ret=[nx[i]/nx[i-1] for i in range(1,n)]
random.seed(1); B=4000; cnt={k:0 for k in table}; cnt_max=0
best_obs=max(abs(v) for v in obs.values())
for _ in range(B):
    blocks=[ret[i:i+4] for i in range(0,len(ret),4)]; random.shuffle(blocks)
    rr=[x for b in blocks for x in b]; s=[nx[0]]
    for q in rr: s.append(s[-1]*q)
    c=allc(s)
    for k in table:
        if abs(c[k])>=abs(obs[k]): cnt[k]+=1
    if max(abs(v) for v in c.values())>=best_obs: cnt_max+=1
for k in table: print(k, round(obs[k],2), 'p=%.3f'%(cnt[k]/B))
print('combinations tried', len(obs), 'best', round(best_obs,2), 'chance the best of all 60 is this strong:', round(cnt_max/B,3))
