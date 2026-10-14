"""Reproduce the article counts from public nflverse and FTN releases.
Run: python analysis/reproduce.py
Requires pandas, numpy, scipy and scikit-learn.
Live source corrections may change results; data/*.json records the article snapshot.
"""
from pathlib import Path
import concurrent.futures, urllib.request
BASE=Path(__file__).resolve().parent.parent
CACHE=str(BASE/'.cache')
Path(CACHE).mkdir(exist_ok=True)
def download(item):
    url,path=item
    if not Path(path).exists():urllib.request.urlretrieve(url,path)
items=[(f'https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{y}.csv.gz',f'{CACHE}/pbp{y}.csv.gz') for y in range(2021,2027)]
items += [(f'https://github.com/nflverse/nflverse-data/releases/download/ftn_charting/ftn_charting_{y}.csv',f'{CACHE}/ftn{y}.csv') for y in range(2022,2027)]
items += [('https://github.com/nflverse/nflverse-data/releases/download/players/players.csv',f'{CACHE}/players.csv')]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(download,items))

import json
import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score,brier_score_loss
cols=['season','season_type','game_id','game_date','play_id','play_type','down','ydstogo','yardline_100','qtr','half_seconds_remaining','game_seconds_remaining','score_differential','posteam_timeouts_remaining','defteam_timeouts_remaining','posteam','defteam','home_team','punt_attempt','field_goal_attempt','pass_attempt','rush_attempt','interception','two_point_attempt','qb_spike','qb_kneel','passer_player_id','passer_player_name','air_yards','return_yards','epa','ep','desc','kick_distance','touchback','penalty','punt_blocked']
fs=[]
for y in range(2021,2027):
 p=pd.read_csv(f'{CACHE}/pbp{y}.csv.gz',usecols=cols,low_memory=False)
 p=p[(p.season_type=='REG')&(p.two_point_attempt!=1)]
 print('QC',y,'games',p.game_id.nunique(),'maxdate',p.game_date.max(),'duplicate keys',p.duplicated(['game_id','play_id']).sum(),flush=True)
 fs.append(p)
p=pd.concat(fs,ignore_index=True)
p=p[(p.play_type!='no_play')&(p.qb_kneel!=1)&(p.qb_spike!=1)].copy()
p['home']=p.posteam.eq(p.home_team).astype(float)
features=['ydstogo','yardline_100','qtr','half_seconds_remaining','game_seconds_remaining','score_differential','posteam_timeouts_remaining','defteam_timeouts_remaining','home']
fourth=p[(p.down==4)&p.play_type.isin(['pass','run','punt','field_goal'])].copy()
third=p[(p.down==3)&(p.pass_attempt==1)&p.passer_player_id.notna()].copy()
ints=p[(p.interception==1)&p.passer_player_id.notna()].copy()
# Predict from a hypothetical incomplete pass: same field position/distance,
# fourth down, five seconds elapsed. Fourth down is implicit in training.
third['punt_probability']=np.nan
predrows=[]
for year in range(2021,2027):
 train=fourth[(fourth.season<=2025)&(fourth.season!=year)]
 model=HistGradientBoostingClassifier(max_iter=160,max_leaf_nodes=15,min_samples_leaf=60,l2_regularization=2,learning_rate=.07,random_state=8)
 model.fit(train[features],train.punt_attempt.eq(1))
 test=fourth[fourth.season==year]
 if len(test):
  probs=model.predict_proba(test[features])[:,1]
  z=test[['season','punt_attempt']].copy();z['prob']=probs;predrows.append(z)
  hi=probs>=.8
  print('VALIDATION',year,len(test),'AUC',roc_auc_score(test.punt_attempt.eq(1),probs),'Brier',brier_score_loss(test.punt_attempt.eq(1),probs),'highprobN',hi.sum(),'actualPuntRate',test.loc[hi,'punt_attempt'].mean(),flush=True)
 idx=third.index[third.season==year];x=third.loc[idx,features].copy()
 x['half_seconds_remaining']=(x.half_seconds_remaining-5).clip(lower=0)
 x['game_seconds_remaining']=(x.game_seconds_remaining-5).clip(lower=0)
 third.loc[idx,'punt_probability']=model.predict_proba(x)[:,1]
ints=ints.merge(third[['game_id','play_id','punt_probability']],on=['game_id','play_id'],how='left',validate='one_to_one')
# At least 15 seconds before snap: enough time for incompletion then punt.
for df in [ints,third]:
 df['likely_punt']=(df.down==3)&(df.punt_probability>=.8)&(df.half_seconds_remaining>=15)
 df['majority_punt']=(df.down==3)&(df.punt_probability>=.5)&(df.half_seconds_remaining>=15)
 df['strict_rule']=(df.down==3)&(df.ydstogo>=5)&(df.yardline_100>=55)&(df.half_seconds_remaining>=15)&~((df.qtr>=4)&(df.score_differential<0)&(df.game_seconds_remaining<=300))
allen=ints[ints.passer_player_id=='00-0034857'].copy()
print('ALLEN INTS',allen.groupby('season').size().to_dict(),flush=True)
summary=[]
for year in list(range(2021,2027))+['2021-25','2021-26']:
 scope=ints[ints.season==year] if isinstance(year,int) else ints[ints.season<= (2025 if year=='2021-25' else 2026)]
 at=third[third.season==year] if isinstance(year,int) else third[third.season<= (2025 if year=='2021-25' else 2026)]
 row={'season':year}
 for label,group in [('allen',scope[scope.passer_player_id=='00-0034857']),('rest',scope[scope.passer_player_id!='00-0034857'])]:
  row[label+'_ints']=len(group)
  for flag in ['likely_punt','majority_punt','strict_rule']:
   row[label+'_'+flag+'_n']=int(group[flag].sum());row[label+'_'+flag+'_pct']=100*group[flag].mean()
  row[label+'_third_n']=int(group.down.eq(3).sum());row[label+'_third_pct']=100*group.down.eq(3).mean()
  opp=at[(at.passer_player_id=='00-0034857') if label=='allen' else (at.passer_player_id!='00-0034857')]
  eligible=opp[opp.likely_punt&(opp.play_type=='pass')&(opp.punt_attempt!=1)]
  row[label+'_eligible_attempts']=len(eligible);row[label+'_eligible_int_pct']=100*eligible.interception.mean()
  row[label+'_eligible_air_yards']=eligible.air_yards.mean()
 summary.append(row)
s=pd.DataFrame(summary)
print('SUMMARY',s.round(3).to_string(index=False),flush=True)
print('ALLEN QUALIFYING',allen[allen.likely_punt][['season','game_id','play_id','down','ydstogo','yardline_100','qtr','half_seconds_remaining','score_differential','punt_probability','air_yards','return_yards','epa','desc']].round(3).to_string(index=False),flush=True)
print('ALLEN OTHER THIRD',allen[(allen.down==3)&~allen.likely_punt][['season','game_id','ydstogo','yardline_100','qtr','half_seconds_remaining','score_differential','punt_probability','epa']].round(3).to_string(index=False),flush=True)
s.to_json(f'{CACHE}/arm_punt_summary.json',orient='records',indent=2)
ints.to_pickle(f'{CACHE}/arm_punt_ints.pkl');third.to_pickle(f'{CACHE}/arm_punt_thirds.pkl');p.to_pickle(f'{CACHE}/arm_punt_pbp.pkl')

import pandas as pd,numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
p=pd.read_pickle(f'{CACHE}/arm_punt_pbp.pkl');t=pd.read_pickle(f'{CACHE}/arm_punt_thirds.pkl')
f=pd.concat([pd.read_csv(f'{CACHE}/ftn{y}.csv',usecols=['nflverse_game_id','nflverse_play_id','is_interception_worthy'],low_memory=False) for y in range(2022,2027)],ignore_index=True)
assert not f.duplicated(['nflverse_game_id','nflverse_play_id']).any()
pu=p[(p.punt_attempt==1)&(p.punt_blocked!=1)&(p.penalty!=1)&(p.season<=2025)].copy()
pu['net']=np.where(pu.touchback==1,pu.yardline_100-20,pu.kick_distance-pu.return_yards.fillna(0));pu=pu[pu.net.notna()]
m=HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=6,min_samples_leaf=100,random_state=8).fit(pu[['yardline_100']],pu.net)
a=t[(t.season>=2022)&~t.desc.fillna('').str.contains('sacked',case=False)].copy()
a['expected_punt_net']=m.predict(a[['yardline_100']])
a['eligible_arm_punt_throw']=a.likely_punt&(a.air_yards>=a.expected_punt_net-10)
a=a.merge(f,left_on=['game_id','play_id'],right_on=['nflverse_game_id','nflverse_play_id'],how='left',validate='one_to_one')
a['ftn_risky']=a.is_interception_worthy.astype(str).str.lower().isin(['true','1'])
a['risk_or_actual_pick']=a.ftn_risky|a.interception.eq(1)
print('COVERAGE')
for y,z in a.groupby('season'):print(y,'thirdAttempts',len(z),'matched',z.is_interception_worthy.notna().sum(),'riskFlag',z.ftn_risky.sum())
print('ALLEN ADDITIONAL RISKY PLAYS')
z=a[(a.passer_player_id=='00-0034857')&a.eligible_arm_punt_throw&a.ftn_risky&(a.interception!=1)]
print(z[['season','game_id','qtr','ydstogo','yardline_100','air_yards','expected_punt_net','epa','desc']].to_string(index=False))
for end in [2025,2026]:
 s=a[a.season<=end]
 for name,sel in [('Allen',True),('Rest',False)]:
  z=s[(s.passer_player_id.eq('00-0034857')==sel)]
  print(end,name,'allthirds',len(z),'likelyPuntThirds',z.likely_punt.sum(),'deepEligible',z.eligible_arm_punt_throw.sum(),'actualArm', (z.eligible_arm_punt_throw&z.interception.eq(1)).sum(),'extraRisk', (z.eligible_arm_punt_throw&z.ftn_risky&z.interception.ne(1)).sum(),'totalRiskArm',(z.eligible_arm_punt_throw&z.risk_or_actual_pick).sum(),'all3rdRisk',z.risk_or_actual_pick.sum())
a.to_pickle(f'{CACHE}/ftn_arm_punt_throws.pkl')


players=pd.read_csv(f'{CACHE}/players.csv',low_memory=False)
qbs=set(players.loc[players.position=='QB','gsis_id'])
a=a[a.passer_player_id.isin(qbs)]
result={'scope':'2022–2025 regular seasons','groups':{},'yearly':[]}
for name,s in [('allen',a[(a.season<=2025)&a.passer_player_id.eq('00-0034857')]),('others',a[(a.season<=2025)&~a.passer_player_id.eq('00-0034857')])]:
    q=s[s.likely_punt];d=q[q.eligible_arm_punt_throw]
    result['groups'][name]={'opportunities':len(q),'deep':len(d),'interceptions':int(d.interception.sum()),'extra_risk':int((d.ftn_risky&d.interception.ne(1)).sum()),'risk':int(d.risk_or_actual_pick.sum()),'ftn_only_risk':int(d.ftn_risky.sum()),'deep_pct':100*len(d)/len(q),'risk_pct':100*d.risk_or_actual_pick.sum()/len(q),'risk_on_deep_pct':100*d.risk_or_actual_pick.mean()}
for yr,z in a[a.season<=2025].groupby('season'):
    row={'season':int(yr)}
    for name,s in [('allen',z[z.passer_player_id.eq('00-0034857')]),('others',z[~z.passer_player_id.eq('00-0034857')])]:
        q=s[s.likely_punt];d=q[q.eligible_arm_punt_throw]
        row[name]={'opportunities':len(q),'deep':len(d),'risk':int(d.risk_or_actual_pick.sum())}
    result['yearly'].append(row)
Path(f'{CACHE}/reproduced-results.json').write_text(json.dumps(result,indent=2))
original=json.loads((BASE/'data/results.json').read_text())
assert result['groups']==original['groups'], 'Source or dependency revisions changed the headline counts. Compare the snapshot with .cache/reproduced-results.json.'
assert result['yearly']==original['yearly']
print('Verified headline counts against the article snapshot.')
