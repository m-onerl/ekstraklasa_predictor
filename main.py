import asyncio
import logging
from psycopg import connect
from database.src.db_connect import CONNECTION_INFO
from database.src.db_queries import DatabaseOperations
from scraper.src.scraper import Scraper

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def main():
    """Main function to scrape and save data to database"""

    all_matches_data = await Scraper.scraper()
    
    logger.info(f"Scraping completed. Total matches: {len(all_matches_data)}")
    
    if not all_matches_data:
        logger.warning("Got no matches to save")
        return

    logger.info("Connecting with database...")
    
    try:
        with connect(CONNECTION_INFO) as conn:
            with conn.cursor() as cur:
                success_count = 0
                error_count = 0
                
                for idx, match_data in enumerate(all_matches_data, 1):
                    try:
                        logger.info(f"Inserting match {idx}/{len(all_matches_data)}: "
                                  f"{match_data.get('home_team', 'Unknown')} vs "
                                  f"{match_data.get('away_team', 'Unknown')}")
                        
                        match_id = DatabaseOperations.insert_match_data(cur, match_data)
                        conn.commit()
                        
                        logger.info(f"Success ! inserted match: {match_id}")
                        success_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error inserting match {idx}: {e}")
                        conn.rollback()
                        error_count += 1
                        continue
                
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
