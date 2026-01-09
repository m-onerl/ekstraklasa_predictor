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
        
        cur.execute("SELECT team_id from teams WHERE name = %s", (team_name,))
        result = cur.fetchone()
        
        if result:
            return result[0]
        
        cur.execute("INSERT INTO teams (name) VALUES (%s) RETURNING team_id", (team_name,))
        return cur.fetchone()[0]
    
    @staticmethod
    def get_or_create_referee(cur, name, nationality):
        
        pass

    @staticmethod
    def get_or_create_stadium(cur, name, place):
        
        pass
    
    @staticmethod
    def instert_match_data(match_data):
        pass