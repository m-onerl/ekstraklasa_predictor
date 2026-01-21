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
        m.home_score,
        m.away_score,
        m.date_time,
        m.attendance,
        ms.*
    FROM matches m
    LEFT JOIN match_statistics ms ON m.match_id = ms.match_id
    ORDER BY m.date_time
    """
    
    try:
        with connect(CONNECTION_INFO) as conn:
            df = pd.read_sql_query(query, conn)
            
            logger.info(f"Loaded {len(df)} matches from database")
            logger.info(f"Number of columns: {len(df.columns)}")
            
            if 'status' in df.columns:
                logger.info(f"\nStatus values:")
                logger.info(df['status'].value_counts())
            
            logger.info(f"\nFirst few rows:")
            logger.info(df.head())
            
            return df
            
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise

if __name__ == "__main__":

    data = load_match_data()
    print(f"\nData shape: {data.shape}")  # (rows, columns)
    print(f"Columns: {list(data.columns)}")