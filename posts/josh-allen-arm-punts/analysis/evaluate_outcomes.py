"""Compare all qualifying intercepted throws with an incomplete pass and typical punt.
Run reproduce.py first. Requires xgboost in addition to its dependencies.
This is conditional on observed interceptions, not a strategy expected-value estimate.
"""
from pathlib import Path
import json,hashlib,urllib.request,lzma,struct
import numpy as np
import pandas as pd
import xgboost as xgb
BASE=Path(__file__).resolve().parent.parent
CACHE=BASE/'.cache'
model_path=CACHE/'ep_model.ubj'
if not model_path.exists():
 raw_path=CACHE/'ep_model.rda'
 if not raw_path.exists():urllib.request.urlretrieve('https://raw.githubusercontent.com/nflverse/fastrmodels/f7c9d05bec81cd310bd1b4cc951b8a451b6aba6c/data/ep_model.rda',raw_path)
 raw=lzma.decompress(raw_path.read_bytes());pos=raw.index(b'{L');n=struct.unpack('>I',raw[pos-4:pos])[0]
 assert n>10000 and pos+n<=len(raw)
 model_path.write_bytes(raw[pos:pos+n])
model=xgb.Booster();model.load_model(model_path);model.set_param({'nthread':1})
assert model.num_features()==18
# Same feature order and score classes as nflfastR helper_add_ep_wp.R.
def ep(seconds,yardline,home,roof,ydstogo,down,offto,defto):
 row=[seconds,yardline,home,int(roof not in ['dome','outdoors']),int(roof=='dome'),int(roof=='outdoors'),ydstogo,0,0,0,0,1]+[int(down==d) for d in [1,2,3,4]]+[offto,defto]
 return float(model.predict(xgb.DMatrix(np.array([row],dtype='float32'),nthread=1))[0]@np.array([7,-7,3,-3,2,-2,0]))
games_path=CACHE/'games.csv'
if not games_path.exists():urllib.request.urlretrieve('https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv',games_path)
games=pd.read_csv(games_path).set_index('game_id')
a=pd.read_pickle(CACHE/'ftn_arm_punt_throws.pkl')
players=pd.read_csv(CACHE/'players.csv',low_memory=False)
qbs=players[players.position.eq('QB')].set_index('gsis_id').display_name.to_dict()
z=a[a.passer_player_id.isin(qbs)&a.eligible_arm_punt_throw&a.interception.eq(1)&a.season.ge(2022)&a.game_date.le('2026-10-12')].copy()
assert len(z)==41 and z.passer_player_id.eq('00-0034857').sum()==6
states_path=CACHE/'outcome_raw_states.pkl'
if not states_path.exists():
 states=[]
 for year in sorted(z.season.unique()):
  yy=pd.read_csv(CACHE/f'pbp{year}.csv.gz',usecols=['game_id','play_id','posteam','yardline_100','half_seconds_remaining','ep','epa','down','ydstogo','desc'],low_memory=False)
  states.append(yy[yy.game_id.isin(z.loc[z.season.eq(year),'game_id'])])
  print('Read unfiltered post-play states',year,flush=True)
 pd.concat(states).to_pickle(states_path)
p=pd.read_pickle(states_path)
rows=[]
# +/-10 yards are illustrative punt scenarios, not statistical confidence bounds.
scenarios={'central':(0,12),'shorter_punt':(-10,12),'longer_punt':(10,12),'faster_sequence':(0,10),'slower_sequence':(0,18)}
for _,r in z.iterrows():
 game=games.loc[r.game_id];roof=game.roof
 neutral=game.location=='Neutral';home=0 if neutral else int(r.posteam==r.home_team);recvhome=0 if neutral else int(r.defteam==r.home_team)
 reconstructed=ep(r.half_seconds_remaining,r.yardline_100,home,roof,r.ydstogo,3,r.posteam_timeouts_remaining,r.defteam_timeouts_remaining)
 row={k:(float(r[k]) if isinstance(r[k],(np.floating,float)) else int(r[k]) if isinstance(r[k],np.integer) else r[k]) for k in ['game_id','game_date','play_id','season','posteam','defteam','ydstogo','yardline_100','half_seconds_remaining','air_yards','return_yards','ep','epa','expected_punt_net','desc']}
 row.update({'qb':qbs[r.passer_player_id],'qb_id':r.passer_player_id,'roof':roof,'neutral_site':bool(neutral),'posteam_timeouts_remaining':float(r.posteam_timeouts_remaining),'defteam_timeouts_remaining':float(r.defteam_timeouts_remaining),'reconstructed_pre_ep':reconstructed,'pre_ep_error':reconstructed-r.ep,'scenarios':{}})
 td='TOUCHDOWN' in r.desc.upper()
 row['return_touchdown']=td
 nxt=p[(p.game_id.eq(r.game_id))&(p.play_id>r.play_id)&p.posteam.eq(r.defteam)&p.yardline_100.notna()].sort_values('play_id')
 row['actual_receiving_own_yardline']=None if td or not len(nxt) else float(100-nxt.iloc[0].yardline_100)
 if len(nxt) and not td:
  after=nxt.iloc[0]
  row['actual_next_play_id']=float(after.play_id)
  row['actual_post_ep_error']=float(-after.ep-r.ep-r.epa)
  assert abs(row['actual_post_ep_error'])<1e-5, (r.game_id,r.play_id,'post-state mismatch')
 for name,(offset,elapsed) in scenarios.items():
  net=r.expected_punt_net+offset;receiving_own=r.yardline_100-net
  # Scenarios exceeding the goal line are touchbacks, at the receiving 20.
  if receiving_own<=0:receiving_own=20.0
  receiving_own=min(receiving_own,99.0)
  seconds=max(0,r.half_seconds_remaining-elapsed)
  post=0 if seconds==0 else -ep(seconds,100-receiving_own,recvhome,roof,min(10,100-receiving_own),1,r.defteam_timeouts_remaining,r.posteam_timeouts_remaining)
  benchmark=post-r.ep;delta=r.epa-benchmark
  row['scenarios'][name]={'net_punt_yards_input':float(net),'receiving_own_yardline':float(receiving_own),'half_seconds_remaining':float(seconds),'combined_incompletion_punt_epa':float(benchmark),'actual_minus_punt_epa':float(delta)}
 central=row['scenarios']['central'];actual=row['actual_receiving_own_yardline']
 row['punt_like_field_position']=bool(not td and actual is not None and actual<=central['receiving_own_yardline']+10)
 row['materially_worse']=bool(central['actual_minus_punt_epa']<=-0.5)
 rows.append(row)
# Independently reviewed examples anchor field-position arithmetic and EP signs.
jax=next(r for r in rows if r['game_id']=='2023_05_JAX_BUF' and r['qb']=='Josh Allen')
assert abs(jax['scenarios']['central']['combined_incompletion_punt_epa']-(-0.4622898844536394))<1e-6
rams=next(r for r in rows if r['game_id']=='2026_05_BUF_LA' and r['qb']=='Josh Allen')
assert rams['actual_receiving_own_yardline']==43
maxerror=max(abs(r['pre_ep_error']) for r in rows)
print('Max reconstructed pre-EP error',maxerror,flush=True)
assert maxerror<1e-5, 'Roof/location/model mismatch: resolve before interpreting.'
def summarize(rr):
 out={'interceptions':len(rr),'actual_epa_total':sum(x['epa'] for x in rr),'return_touchdowns':sum(x['return_touchdown'] for x in rr),'punt_like_field_positions':sum(x['punt_like_field_position'] for x in rr),'materially_worse_interceptions':sum(x['materially_worse'] for x in rr),'scenarios':{}}
 for name in scenarios:
  ds=[x['scenarios'][name]['actual_minus_punt_epa'] for x in rr]
  out['scenarios'][name]={'punt_epa_total':sum(x['scenarios'][name]['combined_incompletion_punt_epa'] for x in rr),'delta_total':sum(ds),'delta_mean':float(np.mean(ds)) if ds else None,'delta_median':float(np.median(ds)) if ds else None,'worse_count':sum(d<0 for d in ds),'materially_worse_count':sum(d<=-0.5 for d in ds)}
 return out
A=[r for r in rows if r['qb']=='Josh Allen'];L=[r for r in rows if r['qb']!='Josh Allen']
result={'scope':'2022–2026 YTD regular seasons through 2026-10-12','assumptions':{'incompletion_seconds':5,'punt_seconds':7,'punt_net':'Same 2021–2025 field-position model used for qualification','delta':'actual interception EPA minus combined incompletion/punt EPA; positive favors actual pick','materially_worse_threshold':-0.5,'punt_like_field_position':'opponent no more than 10 yards farther forward than modeled punt, or deeper; touchdowns fail','model_sha256':hashlib.sha256(model_path.read_bytes()).hexdigest(),'max_reconstructed_pre_ep_error':maxerror,'model_feature_order':['half_seconds_remaining','yardline_100','home','retractable','dome','outdoors','ydstogo','era0','era1','era2','era3','era4','down1','down2','down3','down4','posteam_timeouts_remaining','defteam_timeouts_remaining']},'groups':{'allen':summarize(A),'others':summarize(L)},'yearly':[],'qbs':{},'plays':rows}
for year in range(2022,2027):result['yearly'].append({'season':year,'allen':summarize([r for r in A if r['season']==year]),'others':summarize([r for r in L if r['season']==year])})
for name in sorted({r['qb'] for r in rows}):result['qbs'][name]=summarize([r for r in rows if r['qb']==name])
(BASE/'data/interception-outcomes.json').write_text(json.dumps(result,indent=2,allow_nan=False))
print('GROUPS',json.dumps(result['groups'],indent=2),flush=True)
print('ALLEN',[(r['game_id'],r['actual_receiving_own_yardline'],r['scenarios']['central']) for r in A],flush=True)
print('WORST',[(r['qb'],r['game_id'],r['return_yards'],r['scenarios']['central']['actual_minus_punt_epa']) for r in sorted(rows,key=lambda r:r['scenarios']['central']['actual_minus_punt_epa'])[:5]],flush=True)
