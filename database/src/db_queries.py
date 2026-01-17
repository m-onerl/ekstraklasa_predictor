import logging
from psycopg import connect
from psycopg.rows import dict_row
import json
from .db_connect import CONNECTION_INFO

logger = logging.getLogger(__name__)

class DatabaseOperations:
    
    #apping from polish to english column names
    STATISTIC_TRANSLATIONS = {

        'Oczekiwane gole (xG)': 'xg',
        'Posiadanie piłki': 'ball_possession',
        'Strzały łącznie': 'total_shots',
        'Strzały na bramkę': 'shots_on_target',
        'Wielkie szanse': 'big_chances',
        'Rzuty rożne': 'corner_kicks',
        'Podania': 'passes',
        'Żółte kartki': 'yellow_cards',
        'Czerwone kartki': 'red_cards',

        'xG na bramkę (xGOT)': 'xgot',
        'Strzały niecelne': 'shots_off_target',
        'Strzały zablokowane': 'blocked_shots',
        'Strzały z pola karnego': 'shots_inside_box',
        'Strzały spoza pola karnego': 'shots_outside_box',
        'Strzał w poprzeczkę': 'hit_woodwork',
        'Bramki strzelone głową': 'headed_goals',

        'Kontakty w polu karnym przeciwnika': 'touches_in_opponent_box',
        'Celne podania prostopadłe': 'accurate_through_balls',
        'Spalone': 'offsides',
        'Rzuty wolne': 'free_kicks',

        'Długie podania': 'long_balls',
        'Podania w strefę obrony przeciwnika': 'passes_into_final_third',
        'Dośrodkowania': 'crosses',
        'Oczekiwane asysty (xA)': 'xa',
        'Wrzuty z autu': 'throw_ins',

        'Faule': 'fouls',
        'Próby odbioru piłki': 'tackle_success',
        'Wygrane pojedynki': 'duels_won',
        'Wybicia': 'clearances',
        'Przechwyty': 'interceptions',
        'Błędy skutkujące strzałem': 'errors_leading_to_shot',
        'Błędy skutkujące golem': 'errors_leading_to_goal',

        'Obrony bramkarza': 'goalkeeper_saves',
        'xGot przeciw': 'xgot_faced',
        'Zapobiegnięcia utracie gola': 'prevented_goals',
    }
    
    @staticmethod
    def translate_statistic_name(polish_name):
        return DatabaseOperations.STATISTIC_TRANSLATIONS.get(polish_name, polish_name.lower().replace(' ', '_'))
    
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
        """Insert a single match into the database with all statistics"""
        
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
        
        #  all statistics from both basic and detailed statistics
        all_stats = {}
        
        #  basic statistics
        if 'statistics' in match_data:
            for category, values in match_data['statistics'].items():
                all_stats[category] = values
        
        # detailed statistics
        if 'detailed_statistic' in match_data:
            for section_name, stats in match_data['detailed_statistic'].items():
                for category, values in stats.items():
                    all_stats[category] = values
        
        # statistics dictionary with English column names
        stats_dict = {}
        for polish_name, values in all_stats.items():
            english_name = DatabaseOperations.translate_statistic_name(polish_name)
            stats_dict[f'home_{english_name}'] = values.get('home')
            stats_dict[f'away_{english_name}'] = values.get('away')

        cur.execute("""
            INSERT INTO matches (
                match_id, home_team_id, away_team_id, 
                home_score, away_score, date_time, status,
                referee_id, stadium_id, attendance, url
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            match_data.get('attendance'),
            match_data.get('url')
        ))
        
        match_id = cur.fetchone()[0]
        
        # dynamic INSERT for match_statistics with all statistic columns
        stat_columns = list(stats_dict.keys())
        stat_values = list(stats_dict.values())
        
        if stat_columns:
            #  match_id column
            all_columns = ['match_id'] + stat_columns
            all_values = [match_id] + stat_values
            
            # the INSERT query
            columns_str = ', '.join(all_columns)
            placeholders = ', '.join(['%s'] * len(all_values))
            
            query = f"""
                INSERT INTO match_statistics ({columns_str})
                VALUES ({placeholders})
            """
            
            cur.execute(query, tuple(all_values))
        else:
            # no statistics, insert just the match_id
            cur.execute("""
                INSERT INTO match_statistics (match_id)
                VALUES (%s)
            """, (match_id,))
        
        return match_id