import json, collections, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'serif','font.size':8.5,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
S=json.load(open('studies.json'))
yrs=list(range(1994,2027))
cl=collections.Counter(r['year'] for r in S if r['fam']); bl=collections.Counter(r['year'] for r in S if not r['fam'])
fig,ax=plt.subplots(figsize=(6.6,2.4))
a=[cl[y] for y in yrs]; b=[bl[y] for y in yrs]
n_cl=sum(a); n_bl=sum(b)
ax.bar(yrs,a,color='#2b5c8a',width=0.8,label=f'Classificados (n = {n_cl})')
if n_bl:
    ax.bar(yrs,b,bottom=a,color='#b9c7d6',width=0.8,label=f'Apenas título, não classificados (n = {n_bl})')
ax.set_xlim(1993.3,2026.7); ax.set_ylabel('Estudos'); ax.set_xticks(range(1994,2027,2)); ax.tick_params(axis='x',rotation=45)
ax.legend(frameon=False,loc='lower left',bbox_to_anchor=(0,1.0),ncol=2); ax.grid(axis='y',color='#dddddd',lw=0.5); ax.set_axisbelow(True)
ax.text(2026,cl[2026]+bl[2026]+0.8,'parcial',ha='center',fontsize=6.5,color='#555')
fig.tight_layout(); fig.savefig('figs/years_pt.pdf')
# bubble map
per=[('1994–2005',1994,2005),('2006–2013',2006,2013),('2014–2019',2014,2019),('2020–2026',2020,2026)]
fams=[('TF-PM','Mineração de processos (TF-PM)'),('TF-ST','Modelo estocástico (TF-ST)'),('TF-FC','Previsão (TF-FC)'),('TF-MSR','Mineração de repositórios (TF-MSR)')]
fig,ax=plt.subplots(figsize=(6.4,2.9))
for i,(f,lab) in enumerate(fams):
  for j,(p,a0,a1) in enumerate(per):
    n=sum(1 for r in S if f in r['fam'] and a0<=r['year']<=a1)
    tot=sum(1 for r in S if r['fam'] and a0<=r['year']<=a1)
    ax.scatter(j,len(fams)-1-i,s=n*14,color='#2b5c8a',alpha=0.75,edgecolor='white')
    ax.text(j+0.08+0.0105*(n*14)**0.5,len(fams)-1-i,f'{n}\n({100*n/tot:.0f}%)',va='center',fontsize=7)
ax.set_yticks(range(len(fams))); ax.set_yticklabels([l for _,l in fams][::-1])
ax.set_xticks(range(len(per))); ax.set_xticklabels([f'{p}\n(n = {sum(1 for r in S if r["fam"] and a0<=r["year"]<=a1)})' for p,a0,a1 in per])
ax.set_xlim(-0.5,3.7); ax.set_ylim(-0.6,3.6)
for s in ['left','bottom']: ax.spines[s].set_visible(False)
ax.tick_params(length=0)
fig.tight_layout(); fig.savefig('figs/bubble_pt.pdf')
