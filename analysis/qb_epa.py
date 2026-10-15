"""Shared QB EPA calculation, empirically benchmarked to nfelo, October 2026.

Run on one frozen nflverse PBP snapshot. Pass an explicit season_type and
quarterback ID set. Total, rate and success share exactly one play set.
"""
import pandas as pd
STANDARD_VERSION = 'nfelo-compatible-v1'
def eligible_plays(pbp, season_type='REG'):
    regular_qb_pass = pbp['pass'].eq(1)
    eligible_run = pbp['rush_attempt'].eq(1) & pbp['aborted_play'].ne(1)
    keep = (pbp['season_type'].eq(season_type)
            & (regular_qb_pass | eligible_run)
            & pbp['down'].notna() & pbp['epa'].notna()
            & pbp['qb_kneel'].ne(1) & pbp['qb_spike'].ne(1)
            & pbp['two_point_attempt'].ne(1) & pbp['id'].notna())
    return pbp.loc[keep].copy()
def aggregate_quarterbacks(pbp, quarterback_ids, season_type='REG'):
    plays = eligible_plays(pbp, season_type)
    plays = plays[plays['id'].isin(set(quarterback_ids))]
    result = plays.groupby('id')['epa'].agg(
        plays='size', total_epa='sum', epa_per_play='mean',
        positive_plays=lambda x: x.gt(0).sum(),
        success_rate=lambda x: x.gt(0).mean()).reset_index()
    return result
