import pandas as pd
import numpy as np
import logging

from ml_implemention.src.data_loading import load_match_data
from ml_implemention.src.data_preparation import calculate_rolling_stats
from ml_implemention.src.model_training import MatchPredictor

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def to_float(val, default):
    if val is None or val == '':
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def get_team_current_form(team_name, n_games=5):

    df = load_match_data()
    df = df.sort_values('date_time')

    team_matches = df[
        (df['home_team_name'] == team_name) | 
        (df['away_team_name'] == team_name)
    ].tail(n_games)
    
    if len(team_matches) == 0:
        logger.warning(f"Team '{team_name}' not found!")
        return None

    stats = {
        'goals_for': [],
        'goals_against': [],
        'xg': [],
        'shots': [],
        'possession': [],
        'wins': [],
        'points': [],
        'corners': [],
        'fouls': [],
        'yellow_cards': [],
        'red_cards': [],
        'free_kicks': [],
    }

    for _, row in team_matches.iterrows():
        if row['home_team_name'] == team_name:
            stats['goals_for'].append(to_float(row['home_score'], 0))
            stats['goals_against'].append(to_float(row['away_score'], 0))
            stats['xg'].append(to_float(row.get('home_xg'), 0))
            stats['shots'].append(to_float(row.get('home_total_shots'), 10))
            stats['possession'].append(to_float(row.get('home_ball_possession'), 50))
            stats['corners'].append(to_float(row.get('home_corner_kicks'), 5))
            stats['fouls'].append(to_float(row.get('home_fouls'), 12))
            stats['yellow_cards'].append(to_float(row.get('home_yellow_cards'), 2))
            stats['red_cards'].append(to_float(row.get('home_red_cards'), 0))
            stats['free_kicks'].append(to_float(row.get('home_free_kicks'), 12))
            
            home_score = to_float(row['home_score'], 0)
            away_score = to_float(row['away_score'], 0)
            if home_score > away_score:
                stats['wins'].append(1)
                stats['points'].append(3)
            elif home_score < away_score:
                stats['wins'].append(0)
                stats['points'].append(0)
            else:
                stats['wins'].append(0)
                stats['points'].append(1)
        else:
            stats['goals_for'].append(to_float(row['away_score'], 0))
            stats['goals_against'].append(to_float(row['home_score'], 0))
            stats['xg'].append(to_float(row.get('away_xg'), 0))
            stats['shots'].append(to_float(row.get('away_total_shots'), 10))
            stats['possession'].append(to_float(row.get('away_ball_possession'), 50))
            stats['corners'].append(to_float(row.get('away_corner_kicks'), 5))
            stats['fouls'].append(to_float(row.get('away_fouls'), 12))
            stats['yellow_cards'].append(to_float(row.get('away_yellow_cards'), 2))
            stats['red_cards'].append(to_float(row.get('away_red_cards'), 0))
            stats['free_kicks'].append(to_float(row.get('away_free_kicks'), 12))
            
            home_score = to_float(row['home_score'], 0)
            away_score = to_float(row['away_score'], 0)
            if away_score > home_score:
                stats['wins'].append(1)
                stats['points'].append(3)
            elif away_score < home_score:
                stats['wins'].append(0)
                stats['points'].append(0)
            else:
                stats['wins'].append(0)
                stats['points'].append(1)
    
    return {
        'avg_goals': np.mean(stats['goals_for']),
        'avg_conceded': np.mean(stats['goals_against']),
        'avg_xg': np.mean(stats['xg']),
        'avg_shots': np.mean(stats['shots']),
        'avg_possession': np.mean(stats['possession']),
        'win_rate': np.mean(stats['wins']),
        'ppg': np.mean(stats['points']),
        'games_played': len(team_matches),
        'avg_corners': np.mean(stats['corners']),
        'avg_fouls': np.mean(stats['fouls']),
        'avg_yellow': np.mean(stats['yellow_cards']),
        'avg_red': np.mean(stats['red_cards']),
        'avg_free_kicks': np.mean(stats['free_kicks']),
    }


def predict_match(home_team: str, away_team: str, model_path='models/match_predictor.pkl'):

    predictor = MatchPredictor()
    predictor.load(model_path)

    home_form = get_team_current_form(home_team)
    away_form = get_team_current_form(away_team)
    
    if home_form is None or away_form is None:
        return None

    result_features = pd.DataFrame([{
        'home_avg_goals_last_5': home_form['avg_goals'],
        'home_avg_conceded_last_5': home_form['avg_conceded'],
        'home_avg_xg_last_5': home_form['avg_xg'],
        'home_avg_shots_last_5': home_form['avg_shots'],
        'home_avg_possession_last_5': home_form['avg_possession'],
        'home_win_rate_last_5': home_form['win_rate'],
        'home_ppg_last_5': home_form['ppg'],
        
        'away_avg_goals_last_5': away_form['avg_goals'],
        'away_avg_conceded_last_5': away_form['avg_conceded'],
        'away_avg_xg_last_5': away_form['avg_xg'],
        'away_avg_shots_last_5': away_form['avg_shots'],
        'away_avg_possession_last_5': away_form['avg_possession'],
        'away_win_rate_last_5': away_form['win_rate'],
        'away_ppg_last_5': away_form['ppg'],
        
        'form_diff': home_form['win_rate'] - away_form['win_rate'],
        'xg_diff': home_form['avg_xg'] - away_form['avg_xg'],
        'goals_diff': home_form['avg_goals'] - away_form['avg_goals'],
    }])

    prediction = predictor.predict(result_features)[0]
    probabilities = predictor.predict_proba(result_features)[0]
    
    result_map = {0: 'Draw', 1: 'Home Win', 2: 'Away Win'}
    
    result = {
        'home_team': home_team,
        'away_team': away_team,
        'prediction': result_map[prediction],
        'probabilities': {
            'Home Win': f"{probabilities[1]:.1%}",
            'Draw': f"{probabilities[0]:.1%}",
            'Away Win': f"{probabilities[2]:.1%}"
        },
        'home_form': home_form,
        'away_form': away_form
    }

    if predictor.has_stats_models():
        stats_features = pd.DataFrame([{
            'home_avg_corners_last_5': home_form['avg_corners'],
            'home_avg_fouls_last_5': home_form['avg_fouls'],
            'home_avg_yellow_last_5': home_form['avg_yellow'],
            'home_avg_red_last_5': home_form['avg_red'],
            'home_avg_free_kicks_last_5': home_form['avg_free_kicks'],
            'home_avg_shots_last_5': home_form['avg_shots'],
            'home_avg_possession_last_5': home_form['avg_possession'],
            
            'away_avg_corners_last_5': away_form['avg_corners'],
            'away_avg_fouls_last_5': away_form['avg_fouls'],
            'away_avg_yellow_last_5': away_form['avg_yellow'],
            'away_avg_red_last_5': away_form['avg_red'],
            'away_avg_free_kicks_last_5': away_form['avg_free_kicks'],
            'away_avg_shots_last_5': away_form['avg_shots'],
            'away_avg_possession_last_5': away_form['avg_possession'],
        }])
        
        result['stats_predictions'] = predictor.predict_stats(stats_features)
    
    return result


def get_all_teams():

    df = load_match_data()
    home_teams = set(df['home_team_name'].dropna().unique())
    away_teams = set(df['away_team_name'].dropna().unique())
    return sorted(home_teams | away_teams)