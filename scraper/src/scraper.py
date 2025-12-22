
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
                
                url = f"https://www.flashscore.pl{href}wyniki/"
                
                seasons_data.append({
                    'index' : i,
                    'text' : text.strip(),
                    'href' : url,
                    'year' : year
                })
                
                logger.info(f"{i+1}. {text.strip()} -> {href}")
                
        logger.info(f"Total found seasons: {len(seasons_data)}")

        res = [d.get('href') for d in seasons_data if 'href' in d]
        
        for link in res:
            await page.goto(link, wait_until="networkidle")
            await asyncio.sleep(1)
            
            while True:
                if len(page.context.pages) > 1:
                    for extra_page in page.context.pages[1:]:
                        await extra_page.close()
                    logger.info("Closed add")
                try:
                    show_more = await page.query_selector('//*[@id="live-table"]/div[1]/div/div/a')
                    if show_more:
                        await asyncio.sleep(0.5)
                        await show_more.click()
                        await asyncio.sleep(1.5)
                        logger.info("Founded button to show more")
                    else:
                        logger.info("All matches loaded")
                        break
                    
                except Exception as e:
                    logger.error(f"Error with clicking into button")
                    break
                    
                    
        #TODO: add logic for click for more matches and 
        #               get every one match to get data about them 
        
        await asyncio.sleep(3)
        await browser.close()
    
if __name__ == "__main__":
    asyncio.run(test_basic_scraper())