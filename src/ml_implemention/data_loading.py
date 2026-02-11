import pandas as pd
from psycopg import connect
from ..database.db_connect import CONNECTION_INFO
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
