import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import logging
from playwright.async_api import async_playwright
from scraper.src.scraper import Scraper
from database.src.db_queries import DatabaseOperations
from database.src.db_connect import CONNECTION_INFO
from psycopg import connect

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



TEST_MATCH_URL = "https://www.flashscore.pl/mecz/pilka-nozna/gornik-zabrze-2LH3Ywq4/korona-kielce-pp78XcbA/?mid=jkLJ5dBs"

@pytest.mark.asyncio
async def test_scrape_single_match():

    
    logger.info(f"Testing single match: {TEST_MATCH_URL}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        try:
            match_page = await browser.new_page()
            await match_page.goto(TEST_MATCH_URL, wait_until="networkidle", timeout=30000)

            await match_page.wait_for_timeout(2000)
            
            logger.info("Page loaded, extracting match data...")

            match_data = await Scraper.extract_match_data(match_page)
            match_data['url'] = TEST_MATCH_URL
            match_data['match_id'] = TEST_MATCH_URL.split('/')[-2] if '/' in TEST_MATCH_URL else TEST_MATCH_URL
            match_data['season'] = "Test Season"
            
            await match_page.close()
            

            assert match_data is not None, "Match data should not be None"
            assert 'home_team' in match_data, "Match data should contain home_team"
            assert 'away_team' in match_data, "Match data should contain away_team"
            assert match_data['home_team'], "Home team should not be empty"
            assert match_data['away_team'], "Away team should not be empty"
            

            logger.info(f"Home Team: {match_data.get('home_team', 'N/A')}")
            logger.info(f"Away Team: {match_data.get('away_team', 'N/A')}")
            logger.info(f"Score: {match_data.get('home_score', 'N/A')} - {match_data.get('away_score', 'N/A')}")
            logger.info(f"Date: {match_data.get('date_time', 'N/A')}")
            logger.info(f"Stadium: {match_data.get('stadium_name', 'N/A')}")
            logger.info(f"Referee: {match_data.get('referee_name', 'N/A')}")
            logger.info(f"Status: {match_data.get('status', 'N/A')}")
            logger.info(f"Statistics sections: {len(match_data.get('statistics', {}))}")
            logger.info(f"Detailed statistics sections: {len(match_data.get('detailed_statistic', {}))}")

            return match_data
                
        finally:
            await browser.close()

@pytest.mark.asyncio
async def test_save_into_database():
    logger.info(f"Starting test for save into database that match : {TEST_MATCH_URL}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless = True)
        
        try:
            match_page = await browser.new_page()
            await match_page.goto(TEST_MATCH_URL, wait_until = 'networkidle', timeout = 30000 )
            await match_page.wait_for_timeout(2000)

            logger.info("Page loaded ")
            
            match_data = await Scraper.extract_match_data(match_page)
            match_data['url'] = TEST_MATCH_URL
            match_data['match_id'] = TEST_MATCH_URL.split('?mid=')[-1]
            match_data['season'] = "Test Season"
            
            await match_page.close()
            
            logger.info(f"Extracted: {match_data.get('home_team', 'N/A')} vs {match_data.get('away_team', 'N/A')}")
            logger.info(f"Score: {match_data.get('home_score', 'N/A')} - {match_data.get('away_score', 'N/A')}")
            
            test_match_id = match_data['match_id']
            
            with connect(CONNECTION_INFO) as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM match_statistics WHERE match_id = %s", (test_match_id,))
                    cur.execute("DELETE FROM matches WHERE match_id = %s", (test_match_id,))
                    
                    DatabaseOperations.insert_match_data(cur, match_data)
                    conn.commit()
                    
                    logger.info(f"Successfully saved match {test_match_id} to database")
            
        finally:
            await browser.close()