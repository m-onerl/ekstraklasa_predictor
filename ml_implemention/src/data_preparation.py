
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
    
    df = df.sort_values('date_time').copy()
    
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

def prepare_data(df, min_games = 3, n_games = 5):
    
    # calculate rolling stats
    features_df = calculate_rolling_stats(df, n_games = n_games)
    
    # drop out teams where are not avilable 5 matches in past
    features_df = features_df[features_df['home_games_played'] >= min_games]
    features_df = features_df[features_df['away_games_played'] >= min_games]

    # data which model will get 
    feature_columns = [
        'home_avg_goals_last_5', 'home_avg_conceded_last_5',
        'home_avg_xg_last_5', 'home_avg_shots_last_5',
        'home_avg_possession_last_5', 'home_win_rate_last_5', 'home_ppg_last_5',
        
        'away_avg_goals_last_5', 'away_avg_conceded_last_5',
        'away_avg_xg_last_5', 'away_avg_shots_last_5',
        'away_avg_possession_last_5', 'away_win_rate_last_5', 'away_ppg_last_5',
        
        'form_diff', 'xg_diff', 'goals_diff'
    ]
    
    #the result of match
    X = features_df[feature_columns].copy()
    y = features_df.apply(lambda row: 
        1 if row['home_score'] > row['away_score'] 
        else (0 if row['home_score'] == row['away_score']  
        else 2),
        axis=1  
    )
    return X, y, feature_columns



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