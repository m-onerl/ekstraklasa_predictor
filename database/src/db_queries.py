import logging
from psycopg import connect
from psycopg.rows import dict_row
import json
from .db_connect import CONNECTION_INFO

logger = logging.getLogger(__name__)

class DatabaseOperations:
    
    @staticmethod
    def get_or_create_team(cur, team_name):
        if not team_name:
            return None
        
        cur.execute("SELECT team_id FROM teams WHERE name = %s", (team_name,))
        result = cur.fetchone()
        
        if result:
            return result[0]
        
        cur.execute("INSERT INTO teams (name) VALUES (%s) RETURNING team_id", (team_name,))
        return cur.fetchone()[0]
    
    @staticmethod
    def get_or_create_referee(cur, referee_name, nationality):   
        if not referee_name:
            return None 
        
        cur.execute("SELECT referee_id FROM referees WHERE name = %s AND nationality = %s", (referee_name, nationality))
        result = cur.fetchone()
        
        if result:
            return result[0]
        
        cur.execute("INSERT INTO referees (name, nationality) VALUES (%s, %s) RETURNING referee_id", (referee_name, nationality))
        return cur.fetchone()[0]

    @staticmethod
    def get_or_create_stadium(cur, stadium_name, city):
        if not stadium_name:
            return None 
        
        cur.execute("SELECT stadium_id FROM stadiums WHERE name = %s AND city = %s", (stadium_name, city))
        result = cur.fetchone()
        
        if result:
            return result[0]
        
        cur.execute("INSERT INTO stadiums (name, city) VALUES (%s, %s) RETURNING stadium_id", (stadium_name, city))
        return cur.fetchone()[0]
    
    @staticmethod
    def insert_match_data(cur, match_data):
        """Insert a single match into the database"""
        
        # using get or create functions for 2 teams and referee
        home_team_id = DatabaseOperations.get_or_create_team(cur, match_data.get('home_team'))
        away_team_id = DatabaseOperations.get_or_create_team(cur, match_data.get('away_team'))
        referee_id = DatabaseOperations.get_or_create_referee(
            cur, 
            match_data.get('referee_name'),
            match_data.get('referee_nationality')
        )
        stadium_id = DatabaseOperations.get_or_create_stadium(
            cur,
            match_data.get('stadium_name'),
            match_data.get('stadium_city')
        )
        
        cur.execute("""
            INSERT INTO matches (
                match_external_id, home_team_id, away_team_id, 
                home_score, away_score, match_date, status,
                referee_id, stadium_id, capacity, attendance, url
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING match_id
        """, (
            match_data.get('match_id'),
            home_team_id,
            away_team_id,
            match_data.get('home_score'),
            match_data.get('away_score'),
            match_data.get('date_time'),
            match_data.get('status'),
            referee_id,
            stadium_id,
            match_data.get('capacity'),
            match_data.get('attendance'),
            match_data.get('url')
        ))
    
    