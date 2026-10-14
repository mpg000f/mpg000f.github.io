"""Validate threshold robustness and selected editorial/data-quality questions.
Requires reproduce.py and compare_qbs.py caches; does not refit either model.
"""
from pathlib import Path
import json
import pandas as pd
BASE=Path(__file__).resolve().parent.parent
C=BASE/'.cache'
players=pd.read_csv(C/'players.csv',low_memory=False)
names=players[players.position.eq('QB')].set_index('gsis_id').display_name.to_dict()
a=pd.read_pickle(C/'ftn_arm_punt_throws.pkl')
a=a[a.passer_player_id.isin(names)&a.game_date.le('2026-10-12')&a.season.ge(2022)].copy()
assert not a.duplicated(['game_id','play_id']).any()
rows=[]
for probability in [.7,.8,.9]:
 for shortfall in [5,10,15]:
  q=a[(a.punt_probability>=probability)&(a.half_seconds_remaining>=15)].copy()
  q['deep']=q.air_yards.ge(q.expected_punt_net-shortfall)
  q['risk']=q.deep&q.risk_or_actual_pick
  qb=q.groupby('passer_player_id').agg(attempts=('risk','size'),risk=('risk','sum'))
  qb['rate']=100*qb.risk/qb.attempts
  qualified=qb[qb.attempts>=100]
  A=qb.loc['00-0034857'];O=q[~q.passer_player_id.eq('00-0034857')]
  rank=int(qualified.rate.rank(method='min',ascending=False).loc['00-0034857'])
  rows.append({'punt_probability':probability,'depth_shortfall_yards':shortfall,'allen_attempts':int(A.attempts),'allen_risk':int(A.risk),'allen_rate':float(A.rate),'others_attempts':len(O),'others_risk':int(O.risk.sum()),'others_rate':100*O.risk.mean(),'allen_rank':rank,'qualified_qbs':len(qualified)})
f=pd.concat([pd.read_csv(C/f'ftn{y}.csv',usecols=['nflverse_game_id','nflverse_play_id','read_thrown'],low_memory=False).assign(season_source=y) for y in range(2022,2027)])
assert not f.duplicated(['nflverse_game_id','nflverse_play_id']).any()
f['normalized_read']=f.read_thrown.astype('string').str.strip()
q=a[a.likely_punt].merge(f,on=['nflverse_game_id','nflverse_play_id'],validate='one_to_one')
coverage=[]
for y,z in f.groupby('season_source'):
 t=q[q.season.eq(y)]
 coverage.append({'season':int(y),'all_charting_checkdowns':int(z.normalized_read.eq('CHK').sum()),'eligible_attempts':len(t),'eligible_checkdowns':int(t.normalized_read.eq('CHK').sum()),'eligible_missing_read':int(t.normalized_read.isna().sum()),'allen_attempts':int(t.passer_player_id.eq('00-0034857').sum()),'allen_checkdowns':int((t.passer_player_id.eq('00-0034857')&t.normalized_read.eq('CHK')).sum())})
check_rows=[]
for pid,z in q[q.season.ge(2023)].groupby('passer_player_id'):
 if len(z)>=100:check_rows.append({'name':names[pid],'attempts':len(z),'checkdowns':int(z.normalized_read.eq('CHK').sum()),'rate':100*z.normalized_read.eq('CHK').mean()})
check_rows=sorted(check_rows,key=lambda x:x['rate'])
plays=json.loads((BASE/'data/interception-outcomes.json').read_text())['plays']
assert len(plays)==41 and len({(p['game_id'],p['play_id']) for p in plays})==41
same_game=[]
for game in ['2025_10_BUF_MIA','2023_16_DET_MIN']:
 z=[p for p in plays if p['game_id']==game]
 raw=pd.read_csv(C/f'pbp{z[0]["season"]}.csv.gz',usecols=['game_id','play_id','interception','epa'],low_memory=False)
 for p in z:
  x=raw[raw.game_id.eq(game)&raw.play_id.eq(p['play_id'])]
  assert len(x)==1 and x.interception.iloc[0]==1 and abs(x.epa.iloc[0]-p['epa'])<1e-10
 same_game.append({'game_id':game,'distinct_play_ids':[p['play_id'] for p in z]})
result={'scope':'2022–2026 YTD through 2026-10-12','minimum_qb_attempts':100,'rank_method':'competition rank, ties share rank','models':'Frozen original punt-probability and net-distance predictions; no refitting','thresholds':rows,'checkdown_coverage':coverage,'checkdowns_2023_onward':check_rows,'distinct_same_game_interceptions':same_game,'unique_interception_game_play_keys':41}
(BASE/'data/validation-checks.json').write_text(json.dumps(result,indent=2))
for x in rows:print(x)
print('2022 coverage',coverage[0]);print('2023+ lowest',check_rows[:5]);print('same game',same_game)
