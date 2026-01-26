
import pandas as pd
import numpy as np
from ml_implemention.src.data_loading import load_match_data
import logging

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def clean_numeric_column(series):
    
    if series.dtype == 'object':  
        series = series.astype(str).str.replace('%', '')
        series = pd.to_numeric(series, errors='coerce')
    return series

def calculate_rolling_stats(df, n_games = 5):
    # calculate moving average
    df = df.sort_values('data_time').copy()
    team_history = {}
    result_rows = []
    
    for idx, row in df.iterrows():
        home_id = row['home_team_id']
        away_id = row['away_team_id']
    
        home_hist = team_history.get(home_id, [])
        away_hist = team_history.get(away_id, [])
        
        if len(home_hist) >= 1:
            recent_home = home_hist[-n_games:] 
            home_avg_goals = np.mean([h['goals_for'] for h in recent_home])
            home_avg_conceded = np.mean([h['goals_against'] for h in recent_home])
            home_avg_xg = np.mean([h['xg'] for h in recent_home])
            home_avg_shots = np.mean([h['shots'] for h in recent_home])
            home_avg_possession = np.mean([h['possession'] for h in recent_home])
            home_win_rate = np.mean([h['win'] for h in recent_home])
            home_ppg = np.mean([h['points'] for h in recent_home])
        else:

            home_avg_goals = 1.0
            home_avg_conceded = 1.0
            home_avg_xg = 1.0
            home_avg_shots = 10.0
            home_avg_possession = 50.0
            home_win_rate = 0.33
            home_ppg = 1.0

        if len(away_hist) >= 1:
            recent_away = away_hist[-n_games:]
            away_avg_goals = np.mean([h['goals_for'] for h in recent_away])
            away_avg_conceded = np.mean([h['goals_against'] for h in recent_away])
            away_avg_xg = np.mean([h['xg'] for h in recent_away])
            away_avg_shots = np.mean([h['shots'] for h in recent_away])
            away_avg_possession = np.mean([h['possession'] for h in recent_away])
            away_win_rate = np.mean([h['win'] for h in recent_away])
            away_ppg = np.mean([h['points'] for h in recent_away])
        else:
            away_avg_goals = 1.0
            away_avg_conceded = 1.0
            away_avg_xg = 1.0
            away_avg_shots = 10.0
            away_avg_possession = 50.0
            away_win_rate = 0.33
            away_ppg = 1.0
            
        result_rows.append({
            'match_id' : row['match_id'],

            'home_avg_goals_last_5': home_avg_goals,
            'home_avg_conceded_last_5': home_avg_conceded,
            'home_avg_xg_last_5': home_avg_xg,
            'home_avg_shots_last_5': home_avg_shots,
            'home_avg_possession_last_5': home_avg_possession,
            'home_win_rate_last_5': home_win_rate,
            'home_ppg_last_5': home_ppg,
            'home_games_played': len(home_hist),
            

            'away_avg_goals_last_5': away_avg_goals,
            'away_avg_conceded_last_5': away_avg_conceded,
            'away_avg_xg_last_5': away_avg_xg,
            'away_avg_shots_last_5': away_avg_shots,
            'away_avg_possession_last_5': away_avg_possession,
            'away_win_rate_last_5': away_win_rate,
            'away_ppg_last_5': away_ppg,
            'away_games_played': len(away_hist),

            'form_diff': home_win_rate - away_win_rate,
            'xg_diff': home_avg_xg - away_avg_xg,
            'goals_diff': home_avg_goals - away_avg_goals,

            'home_score': row['home_score'],
            'away_score': row['away_score'],
        })
        
        if home_id not in team_history:
            team_history[home_id] = []
        if away_id not in team_history:
            team_history[away_id] = []

        if row['home_score'] > row['away_score']:
            home_points, away_points = 3, 0
            home_win, away_win = 1, 0
        elif row['home_score'] < row['away_score']:
            away_points, home_points = 3, 0
            away_win, home_win = 1, 0
        else:
            home_points, away_points = 1, 1
            away_win, home_win = 0, 0

        home_xg = clean_numeric_column(pd.Series([row.get('home_xg', 0)]))[0] or 0
        away_xg = clean_numeric_column(pd.Series([row.get('away_xg', 0)]))[0] or 0
        home_shots = clean_numeric_column(pd.Series([row.get('home_total_shots', 10)]))[0] or 10
        away_shots = clean_numeric_column(pd.Series([row.get('away_total_shots', 10)]))[0] or 10
        home_poss = clean_numeric_column(pd.Series([row.get('home_ball_possession', 50)]))[0] or 50
        away_poss = clean_numeric_column(pd.Series([row.get('away_ball_possession', 50)]))[0] or 50
        
        
        team_history[home_id].append({
            'goals_for': row['home_score'],
            'goals_against': row['away_score'],
            'xg': home_xg,
            'shots': home_shots,
            'possession': home_poss,
            'win': home_win,
            'points': home_points
        })
        
        team_history[away_id].append({
            'goals_for': row['away_score'],
            'goals_against': row['away_score'],
            'xg': away_xg,
            'shots': away_shots,
            'possession': away_poss,
            'win': away_win,
            'points': away_points
        })
        
    return pd.DataFrame(result_rows)

def prepare_data(df):
    
    df = df.copy()
    df = df.dropna(subset=['home_score', 'away_score'])

    df['result'] = df.apply(lambda row: 
        1 if row['home_score'] > row['away_score'] 
        else (0 if row['home_score'] == row['away_score']  
        else 2), axis=1  
    )
    feature_columns = [
        'home_avg_xg_last_5',         
        'home_win_rate_last_5',
        'home_ball_possession', 'away_ball_possession',
        'home_total_shots', 'away_total_shots',
        'home_shots_on_target', 'away_shots_on_target',
        'home_big_chances', 'away_big_chances',
        'home_corner_kicks', 'away_corner_kicks',
        'home_passes', 'away_passes',
        'home_yellow_cards', 'away_yellow_cards',
        'home_shots_inside_box', 'away_shots_inside_box',
        'home_shots_outside_box', 'away_shots_outside_box',
        'home_crosses', 'away_crosses',
        'home_fouls', 'away_fouls',
        'home_offsides', 'away_offsides',
    ]
    
    #  which columns exist
    existing_features = [col for col in feature_columns if col in df.columns]
    #  feature matrix
    X = df[existing_features].copy()
    y = df['result'].copy()
    
    #  all feature columns 
    for col in X.columns:
        X[col] = clean_numeric_column(X[col])
    
    # missing values
    missing_before = X.isnull().sum().sum()

    if missing_before > 0:
        X = X.fillna(0)  # 0 instead of median
    return X, y, existing_features


def main():

    df = load_match_data()
    X, y, features = prepare_data(df)
    
    logger.info("FEATURES USED:")
    for i, feature in enumerate(features, 1):
        logger.info(f"  {i:2}. {feature}")

    logger.info("SAMPLE DATA:")
    logger.info(X.head(10))
    logger.info(X.describe())


if __name__ == "__main__":
    main()