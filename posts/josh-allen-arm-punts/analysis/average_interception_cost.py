"""Compare six average QB interceptions with the arm-punt deficit illustration.
Uses the same 2022–2026 regular-season window through October 12, 2026.
The league-wide mean is a scale reference, not a matched causal comparison.
"""
from pathlib import Path
import json, concurrent.futures, urllib.request
import pandas as pd
B=Path(__file__).resolve().parent.parent
C=B/'.cache'
cols=['season','season_type','game_id','play_id','game_date','play_type','two_point_attempt','qb_kneel','qb_spike','passer_player_id','interception','pass_attempt','epa']
qbs=set(pd.read_csv(C/'players.csv',low_memory=False).query("position == 'QB'").gsis_id)
def load(y):
 url=f'https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{y}.csv.gz'
 path=C/f'average_int_pbp{y}.csv.gz'
 # Fresh cache: do not reuse partially persisted large files from another run.
 with urllib.request.urlopen(url,timeout=90) as r,path.open('wb') as w:
  while chunk:=r.read(1024*1024):w.write(chunk)
 p=pd.read_csv(path,usecols=cols,low_memory=False)
 z=p[p.season_type.eq('REG')&p.game_date.le('2026-10-12')&p.passer_player_id.isin(qbs)&p.interception.eq(1)&p.pass_attempt.eq(1)&p.epa.notna()&p.play_type.ne('no_play')&p.two_point_attempt.ne(1)&p.qb_kneel.ne(1)&p.qb_spike.ne(1)]
 print(y,'QB interceptions',len(z),flush=True)
 return z
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:frames=list(pool.map(load,range(2022,2027)))
z=pd.concat(frames);assert not z.duplicated(['game_id','play_id']).any()
def stats(x):return {'interceptions':len(x),'total_epa':float(x.epa.sum()),'epa_per_interception':float(x.epa.mean()),'six_average_interceptions_epa':float(6*x.epa.mean())}
result={'scope':'2022–2026 YTD regular seasons through 2026-10-12','source':'nflverse PBP releases; refreshed for this calculation','all_qbs':stats(z),'other_qbs_excluding_allen':stats(z[~z.passer_player_id.eq('00-0034857')]),'illustrative_arm_punt_extra_cost':{'epa_per_pick':-.45,'six_picks_epa':6*-.45},'comparison_note':'Average interception EPA is the full play cost; -0.45 is additional cost relative to the incompletion/punt fallback. These have different baselines and are not a matched estimate of savings.','yearly':[{'season':y,**stats(x)} for y,x in z.groupby('season')]}
(B/'data/average-interception-cost.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
