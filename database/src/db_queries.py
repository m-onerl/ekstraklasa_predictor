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
    def get_or_create_stadium(cur, stadium_name, place):
        if not stadium_name:
            return None 
        
        cur.execute("SELECT stadium_id FROM stadiums WHERE name = %s AND city = %s", (stadium_name, place))
        result = cur.fetchone()
        
        if result:
            return result[0]
        
        cur.execute("INSERT INTO stadiums (name, city) VALUES (%s, %s) RETURNING stadium_id", (stadium_name, place))
        return cur.fetchone()[0]
    