import pandas as pd
from psycopg import connect
from database.src.db_connect import CONNECTION_INFO
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def load_match_data():
    query = """
    SELECT 
        m.match_id,
        m.home_team_id,
        m.away_team_id,
        ht.name as home_team_name,
        at.name as away_team_name,
        m.home_score,
        m.away_score, 
        m.date_time,
        m.attendance,
        ms.*
    FROM matches m
    LEFT JOIN match_statistics ms ON m.match_id = ms.match_id
    LEFT JOIN teams ht ON m.home_team_id = ht.team_id
    LEFT JOIN teams at ON m.away_team_id = at.team_id
    ORDER BY m.date_time
    """
    
    try:
        with connect(CONNECTION_INFO) as conn:
            df = pd.read_sql_query(query, conn)
            return df
          
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise

if __name__ == "__main__":
    data = load_match_data()
    
    ranges = [(0, 200), (200, 400), (400, 800), (800, 1600), (1600, 2000)]
    
    for start, end in ranges:
        if len(data) > start:
            subset = data.iloc[start:min(end, len(data))]
            row = subset.sample(1).iloc[0]
            
            print("\n" + "_"*20)
            print(f"RANGE: {start}-{end}")
            print(f"MATCH: {row['home_team_name']} vs {row['away_team_name']}")
            print(f"SCORE: {row['home_score']} - {row['away_score']}")
            print(f"Date: {row['date_time']} | Attendance: {row['attendance']}")
            print("\n" + "_"*20)
            print(f"xG: {row['home_xg']} - {row['away_xg']}")
            print(f"Possession: {row['home_ball_possession']} - {row['away_ball_possession']}")
            print(f"Total shots: {row['home_total_shots']} - {row['away_total_shots']}")
            print(f"Shots on target: {row['home_shots_on_target']} - {row['away_shots_on_target']}")
            print(f"Corners: {row['home_corner_kicks']} - {row['away_corner_kicks']}")
            print(f"Yellow cards: {row['home_yellow_cards']} - {row['away_yellow_cards']}")
            print(f"Fouls: {row['home_fouls']} - {row['away_fouls']}")
            print("\n" + "_"*20)
