"""Overall third-down dropback conversion rates, 2022–2026 YTD.
Passes, sacks and scrambles; excludes handoffs, designed runs and nullified plays.
"""
from pathlib import Path
import json,urllib.request,concurrent.futures
import pandas as pd
B=Path(__file__).resolve().parent.parent;C=B/'.cache'
players=pd.read_csv(C/'players.csv',low_memory=False)
names=players[players.position.eq('QB')].set_index('gsis_id').display_name.to_dict()
cols=['game_id','play_id','season','season_type','game_date','down','play_type','qb_dropback','qb_scramble','sack','two_point_attempt','qb_spike','qb_kneel','passer_player_id','rusher_player_id','first_down','touchdown','ydstogo']
def read(y):
 p=C/f'average_int_pbp{y}.csv.gz'
 try:d=pd.read_csv(p,usecols=cols,low_memory=False)
 except (EOFError,FileNotFoundError):
  urllib.request.urlretrieve(f'https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{y}.csv.gz',p)
  d=pd.read_csv(p,usecols=cols,low_memory=False)
 d=d[d.season_type.eq('REG')&d.game_date.le('2026-10-12')&d.down.eq(3)&d.qb_dropback.eq(1)&d.play_type.ne('no_play')&d.two_point_attempt.ne(1)&d.qb_spike.ne(1)&d.qb_kneel.ne(1)].copy()
 d['qb_id']=d.passer_player_id.fillna(d.rusher_player_id)
 d['converted']=d.first_down.eq(1)|d.touchdown.eq(1)
 return d
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:q=pd.concat(pool.map(read,range(2022,2027)))
excluded=int((~q.qb_id.isin(names)).sum());q=q[q.qb_id.isin(names)]
assert not q.duplicated(['game_id','play_id']).any()
rows=[]
for pid,z in q.groupby('qb_id'):
 rows.append({'id':pid,'name':names[pid],'dropbacks':len(z),'conversions':int(z.converted.sum()),'conversion_pct':100*z.converted.mean(),'sacks':int(z.sack.eq(1).sum()),'scrambles':int(z.qb_scramble.eq(1).sum()),'mean_yards_to_go':float(z.ydstogo.mean())})
qualified=sorted([x for x in rows if x['dropbacks']>=100],key=lambda x:x['conversion_pct'],reverse=True)
for x in qualified:x['rank']=int(1+sum(y['conversion_pct']>x['conversion_pct'] for y in qualified))
def stats(z):return {'dropbacks':len(z),'conversions':int(z.converted.sum()),'conversion_pct':100*z.converted.mean()}
out={'scope':'2022–2026 YTD regular seasons through 2026-10-12','definition':'All valid third-down QB dropbacks, including pass attempts, sacks and scrambles. Conversion is a recorded first down or touchdown. Excludes designed runs, handoffs, spikes, kneels, two-point attempts, nullified plays and penalty-only plays.','minimum_dropbacks':100,'qualified_qbs':len(qualified),'excluded_non_qb_or_unattributed':excluded,'qbs':qualified,'all_qbs':rows,'allen':stats(q[q.qb_id.eq('00-0034857')]),'other_qbs':stats(q[~q.qb_id.eq('00-0034857')])}
(B/'data/third-down-conversion.json').write_text(json.dumps(out,indent=2,allow_nan=False));print('Allen',out['allen']);print('Others',out['other_qbs']);print('Qualified',len(qualified));print([(x['name'],round(x['conversion_pct'],1),x['dropbacks'],x['rank']) for x in qualified[:12]])
