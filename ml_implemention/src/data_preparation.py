
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


def prepare_data(df):
    
    df = df.copy()
    df = df.dropna(subset=['home_score', 'away_score'])

    df['result'] = df.apply(lambda row: 
        1 if row['home_score'] > row['away_score'] 
        else (0 if row['home_score'] == row['away_score']  
        else 2), axis=1  
    )
    feature_columns = [
        'home_xg', 'away_xg',
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