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
        'points': []
    }
    
    def to_float(val, default):
        """Convert value to float, handling None and string types."""
        if val is None or val == '':
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    for _, row in team_matches.iterrows():
        if row['home_team_name'] == team_name:

            stats['goals_for'].append(to_float(row['home_score'], 0))
            stats['goals_against'].append(to_float(row['away_score'], 0))
            stats['xg'].append(to_float(row.get('home_xg'), 0))
            stats['shots'].append(to_float(row.get('home_total_shots'), 10))
            stats['possession'].append(to_float(row.get('home_ball_possession'), 50))
            
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
        'games_played': len(team_matches)
    }


def predict_match(home_team: str, away_team: str, model_path='models/match_predictor.pkl'):

    predictor = MatchPredictor()
    predictor.load(model_path)

    home_form = get_team_current_form(home_team)
    away_form = get_team_current_form(away_team)
    
    if home_form is None or away_form is None:
        return None

    features = pd.DataFrame([{
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

    prediction = predictor.predict(features)[0]
    probabilities = predictor.predict_proba(features)[0]
    
    result_map = {0: 'Draw', 1: 'Home Win', 2: 'Away Win'}
    
    return {
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


def main():

    print("  EKSTRAKLASA MATCH PREDICTOR")

    
    home_team = input("\nEnter HOME team name: ").strip()
    away_team = input("Enter AWAY team name: ").strip()
    
    print(f"\nPredicting: {home_team} vs {away_team}...")
    
    result = predict_match(home_team, away_team)
    
    if result is None:
        print("Error: Could not find one or both teams!")
        return

    print(f"\n  PREDICTION: {result['prediction']}")
    print(f"\n  PROBABILITIES:")
    print(f"    Home Win ({home_team}): {result['probabilities']['Home Win']}")
    print(f"    Draw:                   {result['probabilities']['Draw']}")
    print(f"    Away Win ({away_team}): {result['probabilities']['Away Win']}")


if __name__ == "__main__":
    main()