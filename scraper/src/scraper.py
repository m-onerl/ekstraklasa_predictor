import asyncio
import gc
import logging

from playwright.async_api import async_playwright
from psycopg import connect

from database.src.db_queries import DatabaseOperations
from database.src.db_connect import CONNECTION_INFO
from .get_statistics import Statistic


logger = logging.getLogger(__name__)
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Scraper:
    
    @staticmethod
    async def scrape_single_match(browser, match_href, match_num, total_matches):
        match_page = None
        try:
            logger.info(f"Loading match {match_num}/{total_matches}")

            match_page = await browser.new_page()
            await match_page.goto(match_href, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(0.5)
            
            logger.info(f"Successfully loaded match {match_num}")
            
            # get match data
            match_data = await Statistic.extract_match_data(match_page)
            match_data['url'] = match_href
            match_data['match_id'] = match_href.split('/')[-1] if '/' in match_href else match_href
            
            await match_page.close()
            logger.info(f"Match {match_num} complete")
            
            return match_data
            
        except Exception as e:
            logger.error(f"Error loading match {match_num}: {str(e)}")
            if match_page and not match_page.is_closed():
                try:
                    await match_page.close()
                except:
                    pass
            return None
        
    @staticmethod
    def save_season_to_database(season_matches, season_name):
        """Save all matches from one season into database"""
        saved_count = 0
        try:
            with connect(CONNECTION_INFO) as conn: 
                with conn.cursor() as cur:
                    for match_data in season_matches:
                        try:
                            DatabaseOperations.insert_match_data(cur, match_data)
                            saved_count += 1
                        except Exception as e:
                            logger.error(f"Error inserting match: {e}")
                            continue
                    conn.commit()
            logger.info(f"Saved {saved_count}/{len(season_matches)} matches for season {season_name}")
        except Exception as e:
            logger.error(f"Database error for season {season_name}: {e}")
        return saved_count                    
    
async def scraper(batch_size=5, start_season_year=2012):

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  
        page = await browser.new_page()
      
        url = "https://www.flashscore.pl/pilka-nozna/polska/pko-bp-ekstraklasa/archiwum/"

        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(2)
        
        # get for every one season links
        season_links = await page.query_selector_all(".archiveLatte__season")
        logger.info(f"Found out {len(season_links)} seasons")

        #keep into list season informamtion and links
        seasons_data = []
        for i, season_element in enumerate(season_links):
            
            link = await season_element.query_selector("a.archiveLatte__text.archiveLatte__text--clickable")
            #name of atributes to keep
            if link:
                text = await link.inner_text()
                href = await link.get_attribute("href")
                
                # get format of season years
                year_text = text.strip().split()[-1] 
                if '/' in year_text:
                    start_year = year_text.split('/')[0] 
                else:
                    start_year = year_text
                
                url = f"https://www.flashscore.pl{href}wyniki/"
                # append into list
                seasons_data.append({
                    'index': i,
                    'text': text.strip(),
                    'href': url,
                    'year': start_year
                })
                
                logger.info(f"{i+1}. {text.strip()}  year: {start_year}")
                
        logger.info(f"Total found seasons: {len(seasons_data)}")

        # seasons by year
        filtered_seasons = [
            s for s in seasons_data 
            if s['year'].isdigit() and int(s['year']) >= start_season_year
        ]


        res = [d.get('href') for d in filtered_seasons if 'href' in d]
        
        total_saved_all_seasons = 0  # total across all seasons
        
        for season_idx, link in enumerate(res):
            season_matches = []
            season_name = filtered_seasons[season_idx].get('text', f'Season {season_idx}')
            logger.info(f"Starting season: {season_name}")
            
            await page.goto(link, wait_until="networkidle")
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
                    logger.error(f"Error with clicking into button: {e}")
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
            
            # process matches in batches asynchronously
            total_matches = len(match_urls)
            for batch_start in range(0, total_matches, batch_size):
                batch_end = min(batch_start + batch_size, total_matches)
                batch_urls = match_urls[batch_start:batch_end]
                
                logger.info(f"Processing batch {batch_start//batch_size + 1}: matches {batch_start+1}-{batch_end}/{total_matches}")
                
                # tasks for concurrent scraping
                tasks = [
                    Scraper.scrape_single_match(browser, url, batch_start + i + 1, total_matches)
                    for i, url in enumerate(batch_urls)
                ]
                
                # for all tasks in batch to complete
                batch_results = await asyncio.gather(*tasks)
                
                # successful results to season matches
                for match_data in batch_results:
                    if match_data:
                        match_data['season'] = season_name
                        season_matches.append(match_data)
                
                logger.info(f"Batch complete: {len([r for r in batch_results if r])} successful")
                
            # season to database
            saved = Scraper.save_season_to_database(season_matches, season_name)
            total_saved_all_seasons += saved
            logger.info(f"Season {season_name} complete: {saved}/{len(season_matches)} saved")
            
            season_matches.clear()
            gc.collect()
            
        await browser.close()
        logger.info(f"Scraping complete {total_saved_all_seasons}")
        
        return total_saved_all_seasons
                
if __name__ == "__main__":
    asyncio.run(scraper(batch_size=5, start_season_year=2012))