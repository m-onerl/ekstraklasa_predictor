import asyncio
import logging
from psycopg import connect
from database.src.db_connect import CONNECTION_INFO
from database.src.db_queries import DatabaseOperations
from scraper.src.scraper import scraper

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def main():
    """Main function to scrape and save data to database"""
    await scraper(batch_size=5, start_season_year=2012)



if __name__ == "__main__":
    asyncio.run(main())