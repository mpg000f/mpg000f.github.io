"""Supplement short-of-sticks rates with observed completions and conversions.
Uses the existing eligibility snapshot. Does not modify the article.
"""
from pathlib import Path
import json
import pandas as pd
BASE=Path(__file__).resolve().parent.parent
CACHE=BASE/'.cache'
a=pd.read_pickle(CACHE/'ftn_arm_punt_throws.pkl')
qbs=pd.read_csv(CACHE/'players.csv',low_memory=False);names=qbs[qbs.position.eq('QB')].set_index('gsis_id').display_name.to_dict()
a=a[a.passer_player_id.isin(names)&a.likely_punt&a.season.ge(2022)&a.game_date.le('2026-10-12')].copy()
cache=CACHE/'pass_outcome_fields.pkl'
if not cache.exists():
 pieces=[]
 for year in range(2022,2027):
  p=pd.read_csv(CACHE/f'pbp{year}.csv.gz',usecols=['game_id','play_id','complete_pass','first_down','touchdown'],low_memory=False)
  pieces.append(p);print('Outcome fields',year,flush=True)
 pd.concat(pieces).to_pickle(cache)
a=a.merge(pd.read_pickle(cache),on=['game_id','play_id'],how='left',validate='one_to_one')
assert len(a)==10905 and a.complete_pass.notna().all()
f=pd.concat([pd.read_csv(CACHE/f'ftn{year}.csv',usecols=['nflverse_game_id','nflverse_play_id','read_thrown','is_throw_away'],low_memory=False) for year in range(2022,2027)])
a=a.merge(f,on=['nflverse_game_id','nflverse_play_id'],validate='one_to_one')
a['short']=a.air_yards.lt(a.ydstogo)&a.air_yards.notna()
a['converted']=a.first_down.eq(1)|a.touchdown.eq(1)
a['completed']=a.complete_pass.eq(1)
a['throwaway']=a.is_throw_away.astype(str).str.lower().isin(['true','1'])
def summary(z):
 s=z[z.short];c=s[s.completed];checks=z[z.read_thrown.eq('CHK')];sc=checks[checks.short]
 return {'eligible_attempts':len(z),'short_attempts':len(s),'short_completions':len(c),'short_completion_pct':100*s.completed.mean() if len(s) else None,'short_conversions':int(s.converted.sum()),'short_conversion_pct':100*s.converted.mean() if len(s) else None,'completed_short_conversions':int(c.converted.sum()),'completed_short_conversion_pct':100*c.converted.mean() if len(c) else None,'completed_short_without_conversion':int((~c.converted).sum()),'short_completions_epa_per_play':float(c.epa.mean()) if len(c) else None,'short_attempts_epa_per_play':float(s.epa.mean()) if len(s) else None,'charted_checkdowns':len(checks),'charted_short_checkdowns':len(sc),'charted_short_checkdown_completions':int(sc.completed.sum()),'charted_short_checkdown_conversions':int(sc.converted.sum()),'short_throwaways':int(s.throwaway.sum())}
rows=[]
for pid,z in a.groupby('passer_player_id'):
 r={'id':pid,'name':names[pid],**summary(z)};rows.append(r)
r={'scope':'2022–2026 YTD regular seasons through 2026-10-12','definition':'Same likely-punt third-down pass attempts; short means air_yards < ydstogo; completions are official complete_pass==1; conversion is first_down==1 or touchdown==1. Broad short rate includes known-depth throwaways.','groups':{'all':summary(a),'allen':summary(a[a.passer_player_id.eq('00-0034857')]),'others':summary(a[~a.passer_player_id.eq('00-0034857')])},'qbs':rows}
(BASE/'data/short-pass-outcomes.json').write_text(json.dumps(r,indent=2,allow_nan=False))
print('GROUPS',json.dumps(r['groups'],indent=2),flush=True)
for row in rows:
 if row['name'] in ['Josh Allen','Patrick Mahomes','Jordan Love','Lamar Jackson','Joe Burrow']:print(row,flush=True)
