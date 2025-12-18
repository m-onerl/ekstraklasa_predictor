
import asyncio
from playwright.async_api import async_playwright
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
async def test_basic_scraper():
    logger.info("Starting Playwright test...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  
        page = await browser.new_page()

        url = "https://www.flashscore.pl/pilka-nozna/polska/pko-bp-ekstraklasa/archiwum/"
        logger.info(f"Navigating to: {url}")
        
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(2)
        season_links = await page.query_selector_all(".archiveLatte__season")
        logger.info(f"Found out {len(season_links)} seasons")

        


if __name__ == "__main__":
    asyncio.run(test_basic_scraper())