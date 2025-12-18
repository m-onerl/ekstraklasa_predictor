
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

        seasons_data = []
        for i,  season_element in enumerate(season_links):
            
            link = await season_element.query_selector("a.archiveLatte__text.archiveLatte__text--clickable")
            if link:
                text = await link.inner_text()
                href = await link.get_attribute("href")
                year = text.strip().split()[-1]
                
                seasons_data.append({
                    'index' : i,
                    'text' : text.strip(),
                    'href' : href,
                    'year' : year
                })
                
                logger.info(f"{i+1}. {text.strip()} -> {href}")
                
        logger.info(f"Total found seasons: {len(seasons_data)}")

        await asyncio.sleep(3)
        await browser.close()
    
if __name__ == "__main__":
    asyncio.run(test_basic_scraper())