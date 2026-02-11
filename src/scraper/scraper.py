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
            
            # wait for teams elements to be present before extracting data
            try:
                await match_page.wait_for_selector('.duelParticipant__home', timeout=5000)
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.warning(f"Team elements not found quickly for match {match_num}: {e}")
                await asyncio.sleep(1)
            
            logger.info(f"Successfully loaded match {match_num}")
            
            # get match data
            match_data = await Statistic.extract_match_data(match_page)
            match_data['url'] = match_href

            if '?mid=' in match_href:
                match_data['match_id'] = match_href.split('?mid=')[-1]
            elif 'mid=' in match_href:
                match_data['match_id'] = match_href.split('mid=')[-1]

            
            await match_page.close() 
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
                    for idx, match_data in enumerate(season_matches):
                        try:
                            home_team = match_data.get('home_team', 'Unknown')
                            away_team = match_data.get('away_team', 'Unknown')
                            logger.info(f"Inserting match {idx+1}/{len(season_matches)}: {home_team} vs {away_team}")
                            DatabaseOperations.insert_match_data(cur, match_data)
                            saved_count += 1
                        except Exception as e:
                            logger.error(f"Error inserting match {home_team} vs {away_team}: {e}")
                            logger.error(f"Match data keys: {match_data.keys()}")
                            continue
                    conn.commit()
            logger.info(f"Saved {saved_count}/{len(season_matches)} matches for season {season_name}")
        except Exception as e:
            logger.error(f"Database error for season {season_name}: {e}")
        return saved_count                    
    
async def scraper(start_season_year=2012):

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
                
                season_url = f"https://www.flashscore.pl{href}wyniki/"
                # append into list
                seasons_data.append({
                    'index': i,
                    'text': text.strip(),
                    'href': season_url,
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
        season_names = [d.get('text', f'Season {i}') for i, d in enumerate(filtered_seasons)]
        
        await browser.close()
        
        total_saved_all_seasons = 0  # total across all seasons
        
        for season_idx, (link, season_name) in enumerate(zip(res, season_names)):
            logger.info(f"Starting season {season_idx+1}/{len(res)}: {season_name}")
            
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            season_matches = []
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
            
            # process matches sequentially (one by one) for reliability
            total_matches = len(match_urls)
            for match_idx, url in enumerate(match_urls):
                logger.info(f"Processing match {match_idx+1}/{total_matches}")
                
                match_data = await Scraper.scrape_single_match(browser, url, match_idx + 1, total_matches)
                
                if match_data:
                    if not match_data.get('home_team') or not match_data.get('away_team'):
                        logger.warning(f"Skipping match with missing team data: Home={match_data.get('home_team')}, Away={match_data.get('away_team')}, URL={match_data.get('url')}")
                        continue
                    
                    # validate detailed statistics were extracted
                    ds = match_data.get('detailed_statistic', {})
                    if len(ds) == 0:
                        logger.warning(f"Match {match_idx+1} has empty detailed_statistic!")
                    
                    match_data['season'] = season_name
                    season_matches.append(match_data)
                    logger.info(f"Match {match_idx+1} scraped successfully (detailed sections: {len(ds)})")
                else:
                    logger.error(f"Match {match_idx+1} failed to scrape")
                
                # delay between matches to avoid rate limiting
                await asyncio.sleep(2)
                
            # season to database
            saved = Scraper.save_season_to_database(season_matches, season_name)
            total_saved_all_seasons += saved
            logger.info(f"Season {season_name} complete: {saved}/{len(season_matches)} saved")
            
            await browser.close()
            logger.info(f"Closed browser for season {season_name} (fresh start for next season)")
            
            season_matches.clear()
            gc.collect()
        logger.info(f"Scraping complete {total_saved_all_seasons}")
        
        return total_saved_all_seasons
                
if __name__ == "__main__":
    asyncio.run(scraper(start_season_year=2012))