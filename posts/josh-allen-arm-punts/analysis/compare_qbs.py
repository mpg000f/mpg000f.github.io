"""Individual QB comparisons using the same snapshot and likely-punt rule.
Run reproduce.py first, then this script. No extra FTN flags required.
"""
from pathlib import Path
import json
import pandas as pd
BASE=Path(__file__).resolve().parent.parent
CACHE=BASE/'.cache'
a=pd.read_pickle(CACHE/'ftn_arm_punt_throws.pkl')
players=pd.read_csv(CACHE/'players.csv',low_memory=False)
qbs=players[players.position.eq('QB')].set_index('gsis_id').display_name.to_dict()
a=a[a.passer_player_id.isin(qbs)&a.game_date.le('2026-10-12')&a.season.ge(2022)]
assert not a.duplicated(['game_id','play_id']).any()
extra=pd.concat([pd.read_csv(CACHE/f'pbp{y}.csv.gz',usecols=['game_id','play_id','yards_gained','first_down','complete_pass','touchdown'],low_memory=False) for y in range(2022,2027)])
a=a.merge(extra,on=['game_id','play_id'],validate='one_to_one',how='left')
q=a[a.likely_punt].copy()
q['short']=q.air_yards.lt(q.ydstogo)&q.air_yards.notna()
q['converted']=q.first_down.eq(1)|q.touchdown.eq(1)
rows=[]
for pid,z in q.groupby('passer_player_id'):
 known=z[z.air_yards.notna()];short=z[z.short];deep=z[z.eligible_arm_punt_throw]
 rows.append({'id':pid,'name':qbs[pid],'opportunities':len(z),'known_depth':len(known),'unknown_depth':int(z.air_yards.isna().sum()),'mean_ydstogo':float(z.ydstogo.mean()),'deep':len(deep),'deep_pct':100*len(deep)/len(z),'risk':int(deep.risk_or_actual_pick.sum()),'risk_pct':100*deep.risk_or_actual_pick.sum()/len(z),'interceptions':int(deep.interception.sum()),'short':len(short),'short_pct':100*len(short)/len(known) if len(known) else None,'short_conversions':int(short.converted.sum()),'short_conversion_pct':100*short.converted.mean() if len(short) else None,'short_epa_per_play':float(short.epa.mean()) if len(short) else None})
rows=sorted(rows,key=lambda r:r['deep_pct'],reverse=True)
qualified=[r for r in rows if r['opportunities']>=100]
for metric in ['deep_pct','risk_pct','short_pct']:
 for i,r in enumerate(sorted(qualified,key=lambda r:r[metric],reverse=True),1):r[metric+'_rank']=i
scope={'scope':'2022–2026 YTD regular seasons through 2026-10-12','minimum_opportunities':100,'qualified_count':len(qualified),'all_qbs':rows,'short_baseline':{'opportunities':len(q),'known_depth':int(q.air_yards.notna().sum()),'unknown_depth':int(q.air_yards.isna().sum()),'short':int(q.short.sum()),'short_pct':100*q.short.sum()/q.air_yards.notna().sum(),'short_conversion_pct':100*q.loc[q.short,'converted'].mean()}}
assert q[q.passer_player_id.eq('00-0034857')].shape[0]==284
# FTN progression labels distinguish checkdowns from designed short passes.
f=pd.concat([pd.read_csv(CACHE/f'ftn{y}.csv',usecols=['nflverse_game_id','nflverse_play_id','read_thrown','is_throw_away'],low_memory=False) for y in range(2022,2027)])
qf=q.merge(f,on=['nflverse_game_id','nflverse_play_id'],validate='one_to_one')
assert qf.shape[0]==q.shape[0]
for row in rows:
 z=qf[qf.passer_player_id.eq(row['id'])]
 throwaway=z.is_throw_away.astype(str).str.lower().isin(['true','1'])
 known=z[z.air_yards.notna()&~throwaway];short=known[known.air_yards.lt(known.ydstogo)]
 row.update({'charted_checkdowns':int(z.read_thrown.eq('CHK').sum()),'charted_checkdown_pct':100*z.read_thrown.eq('CHK').mean(),'read_unclassified':int(z.read_thrown.isna().sum()),'throwaways':int(throwaway.sum()),'non_throwaway_known_depth':len(known),'short_excluding_throwaways':len(short),'short_excluding_throwaways_pct':100*len(short)/len(known) if len(known) else None})
for i,row in enumerate(sorted(qualified,key=lambda r:r['charted_checkdown_pct'],reverse=True),1):row['checkdown_rank']=i
(BASE/'data/qb-comparison.json').write_text(json.dumps(scope,indent=2,allow_nan=False))
print(pd.DataFrame(qualified)[['name','opportunities','deep','deep_pct','risk','risk_pct','short_pct','short_conversion_pct']].round(2).to_string(index=False))
print('BASELINE',scope['short_baseline'])
print('MAHOMES 2025 PICKS',a[(a.passer_player_name.eq('P.Mahomes'))&a.season.eq(2025)&a.interception.eq(1)][['game_id','play_id','down','ydstogo','yardline_100','air_yards','punt_probability','expected_punt_net','eligible_arm_punt_throw','desc']].to_string(index=False))
