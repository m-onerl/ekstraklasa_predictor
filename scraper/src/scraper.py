
import asyncio
from playwright.async_api import async_playwright
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
class Scraper:
    async def scraper():

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless = False)  
            page = await browser.new_page()
        
                    
            url = "https://www.flashscore.pl/pilka-nozna/polska/pko-bp-ekstraklasa/archiwum/"
            logger.info(f"Navigating to: {url}")
            # go to scrap page
            
            await page.goto(url, wait_until = "networkidle")
            await asyncio.sleep(2)
            
            # get for every one season links
            season_links = await page.query_selector_all(".archiveLatte__season")
            logger.info(f"Found out {len(season_links)} seasons")

            #keep into list season informamtion and links
            seasons_data = []
            for i,  season_element in enumerate(season_links):
                
                link = await season_element.query_selector("a.archiveLatte__text.archiveLatte__text--clickable")
                #name of atributes to keep
                if link:
                    text = await link.inner_text()
                    href = await link.get_attribute("href")
                    year = text.strip().split()[-1]
                    
                    url = f"https://www.flashscore.pl{href}wyniki/"
                    # append into list
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
                
                await page.goto(link, wait_until = "networkidle")
                await asyncio.sleep(1)
                
                # exit extra pages like adds pages
                while True:
                    
                    if len(page.context.pages) > 1:
                        for extra_page in page.context.pages[1:]:
                            await extra_page.close()
                        logger.info("Closed add")
                        
                    # found out button to show more matches 
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
                # found match links and extract hrefs immediately
                match_elements = await page.query_selector_all('.eventRowLink')
                logger.info(f'Founded {len(match_elements)} matches')

                match_urls = []
                
                for match in match_elements:
                    try:  
                        href = await match.get_attribute('href')
                        if href:
                            match_href = href
                            match_urls.append(match_href)
                            
                    except Exception as e:
                        logger.error(f"Error extracting href: {e}")
                
                # now navigate to each match
                for i, match_href in enumerate(match_urls, 1):
                    match_page = None
                    try:
                        logger.info(f"Loading match {i}/{len(match_urls)}")

                        match_page = await browser.new_page()
                        await match_page.goto(match_href, wait_until="domcontentloaded", timeout=30000)
                        await asyncio.sleep(0.5)
                        
                        logger.info(f"Successfully loaded match {i}")
                        # TODO: Extract match data from match_page

                        await match_page.close()
                        logger.info(f"Match {i} complete")
                        
                    except Exception as e:
                        logger.error(f"Error loading match {i}: {str(e)}")
                        if match_page and not match_page.is_closed():
                            try:
                                await match_page.close()
                            except:
                                pass
                        continue
                    
if __name__ == "__main__":
    asyncio.run(Scraper.scraper())