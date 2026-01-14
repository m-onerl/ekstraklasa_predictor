
import asyncio
import gc
from playwright.async_api import async_playwright
import logging
from database.src.db_queries import DatabaseOperations
from database.src.db_connect import CONNECTION_INFO
from psycopg import connect

logger = logging.getLogger(__name__)
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
class Scraper:
    
    @staticmethod
    async def extract_detailed_statistics(match_page, max_retries=3):
        detailed_stats = {}
        
        for attempt in range(max_retries):
            try:
                # wait before attempting extraction
                await asyncio.sleep(1 + attempt * 0.5)
                sections_wrapper = await match_page.query_selector('div[class*="sectionsWrapper"]')
                
                if not sections_wrapper:
                    sections = await match_page.query_selector_all('.section')
                    if sections and len(sections) > 0:
                        if detailed_stats:
                            break
                    else:
                        logger.info(f"Attempt {attempt + 1}: sectionsWrapper and sections not found")
                        continue
                else:
                    logger.info(f"Attempt {attempt + 1}: sections_wrapper found")
                    
                    sections = await sections_wrapper.query_selector_all('.section')
                    logger.info(f"Found {len(sections)} statistics sections")
                    
                    if len(sections) == 0:
                        logger.info(f"Attempt {attempt + 1}: No sections found, retrying")
                        continue
                    
                    for section in sections:
                        section_header = await section.query_selector('.section__title')
                        if section_header:
                            section_title = (await section_header.inner_text()).strip()
                            detailed_stats[section_title] = {}
                            
                            stat_rows = await section.query_selector_all('[data-testid="wcl-statistics"]')
                            for stat_row in stat_rows:
                                category_element = await stat_row.query_selector('[data-testid="wcl-statistics-category"]')
                                if category_element:
                                    category = (await category_element.inner_text()).strip()
                                    value_elements = await stat_row.query_selector_all('[data-testid="wcl-statistics-value"]')
                                    if len(value_elements) >= 2:
                                        home_value = (await value_elements[0].inner_text()).strip()
                                        away_value = (await value_elements[1].inner_text()).strip()
                                        detailed_stats[section_title][category] = {
                                            'home': home_value,
                                            'away': away_value
                                        }
                    
                    if detailed_stats:
                        logger.info(f"Successfully extracted {len(detailed_stats)} sections")
                        break
                    
            except Exception as e:
                logger.error(f"Attempt error extracting detailed statistics: {e}")
        
        return detailed_stats
    
    @staticmethod
    async def extract_match_data(match_page):
        match_data = {}
        
        try:
            date_element = await match_page.query_selector('.duelParticipant_startTime')
            if date_element:
                match_data['date_time'] = (await date_element.inner_text()).strip()
                
            home_team_element = await match_page.query_selector('.duelParticipant__home .participant__participantName a')
            
            if home_team_element:
                match_data['home_team'] = (await home_team_element.inner_text()).strip()

            away_team_element = await match_page.query_selector('.duelParticipant__away .participant__participantName a')
            if away_team_element:
                match_data['away_team'] = (await away_team_element.inner_text()).strip()
                score_wrapper = await match_page.query_selector('.detailScore__wrapper')
                        
            if score_wrapper:
                score_spans = await score_wrapper.query_selector_all('span')
                if len(score_spans) >= 3:
                    match_data['home_score'] = (await score_spans[0].inner_text()).strip()
                    match_data['away_score'] = (await score_spans[2].inner_text()).strip()
                    
            # get basic statistics there will be more
            stats = {}
            stat_rows = await match_page.query_selector_all('[data-testid="wcl-statistics"]')
            
            for stat_row in stat_rows:
                # geted category name
                category_element = await stat_row.query_selector('[data-testid="wcl-statistics-category"]')
                if category_element:
                    category = (await category_element.inner_text()).strip()
                    
                    # values of home and away
                    value_elements = await stat_row.query_selector_all('[data-testid="wcl-statistics-value"]')
                    if len(value_elements) >= 2:
                        home_value = (await value_elements[0].inner_text()).strip()
                        away_value = (await value_elements[1].inner_text()).strip()
                        
                        stats[category] = {
                            'home': home_value,
                            'away': away_value
                        }
            
            match_data['statistics'] = stats
            
            await asyncio.sleep(0.5)
            
            # get reffere and stadium
            match_info = await match_page.query_selector('.wcl-content_Vkmj9')

            if match_info:
                logger.info("Found match_info")
                info_values = await match_info.query_selector_all('.wcl-infoValue_grawU')
                info_labels = await match_info.query_selector_all('.wcl-infoLabelWrapper_DXbvw')
                
                for i, label_element in enumerate(info_labels):
                    label = (await label_element.inner_text()).strip()

                    if i < len(info_values):
                        value_element = info_values[i]  # Get the element, not the text
                        
                        if 'sędzia' in label.lower() or 'sedzia' in label.lower():
                            # Get all spans inside this value element
                            spans = await value_element.query_selector_all('span')
                            if len(spans) >= 1:
                                match_data['referee_name'] = (await spans[0].inner_text()).strip()
                            if len(spans) >= 2:
                                nationality = (await spans[1].inner_text()).strip()
                                match_data['referee_nationality'] = nationality.replace('(', '').replace(')', '').strip()
                                
                        elif 'stadion' in label.lower():
                            # Get all spans inside this value element
                            spans = await value_element.query_selector_all('span')
                            if len(spans) >= 1:
                                match_data['stadium_name'] = (await spans[0].inner_text()).strip()
                            if len(spans) >= 2:
                                city = (await spans[1].inner_text()).strip()
                                match_data['stadium_city'] = city.replace('(', '').replace(')', '').strip()
                                
                        elif 'pojemność' in label.lower() or 'pojemnosc' in label.lower():
                            match_data['capacity'] = (await value_element.inner_text()).strip()
                            
                        elif 'frekwencja' in label.lower():
                            match_data['attendance'] = (await value_element.inner_text()).strip()
            else:
                logger.info("referee_wrapper NOT found")
                
            # get match status
            status_element = await match_page.query_selector('.fixedHeaderDuel__detailStatus')
            if status_element:
                match_data['status'] = (await status_element.inner_text()).strip()
            try:
                # Get the statistics tab URL and navigate directly
                stats_tab = await match_page.query_selector('a[href*="szczegoly/statystyki"]')
                if stats_tab:
                    stats_href = await stats_tab.get_attribute('href')
                    if stats_href:
                        # Navigate directly to statistics page instead of clicking
                        stats_url = stats_href if stats_href.startswith('http') else f"https://www.flashscore.pl{stats_href}"
                        logger.info(f"Navigating to statistics: {stats_url}")
                        await match_page.goto(stats_url, wait_until="domcontentloaded", timeout=15000)
                        
                        # Wait for content to load
                        await asyncio.sleep(2)
                        
                        try:
                            await match_page.wait_for_selector('[data-testid="wcl-statistics"]', timeout=8000)
                            logger.info("Statistics elements appeared")
                        except:
                            logger.warning("Statistics elements did not appear in time")
                        
                        # now scrape detailed statistics with retry logic
                        detailed_stats = await Scraper.extract_detailed_statistics(match_page)
                        logger.info(f"Extracted detailed stats: {len(detailed_stats)} sections")
                        
                        match_data['detailed_statistic'] = detailed_stats
                else:
                    logger.warning("Statistics tab link not found on this page")
                    
            except Exception as e:
                logger.error(f"Error navigating to statistics tab: {e}")
                
            logger.info(f"Extracted data for {match_data.get('home_team', 'Unknown')} vs {match_data.get('away_team', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Error extracting match data: {e}")
        
        return match_data
        
    @staticmethod
    def save_season_to_database(season_matches, season_name):
        """Save all matches from one season into database"""
        if not season_matches:
            logger.warning(f"No matches to save for season {season_name}")
            return 0
        
        saved_count = 0
        try:
            with connect(CONNECTION_INFO) as conn: 
                with conn.cursor() as cur:
                    for match_data in season_matches:
                        try:
                            DatabaseOperations.insert_match_data(cur,match_data)
                            saved_count += 1
                        except Exception as e:
                            logger.error(f"Error inserting match: {e}")
                            continue
                    conn.commit()
            logger.info(f"Saved {saved_count}/{len(season_matches)} season for season {season_name}")
        except Exception as e:
            logger.error(f"Dtabase error for season {season_name}")
        return saved_count                    
    
    async def scraper():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless = True)  
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
            
            
            for season_idx, link in enumerate(res):
                season_matches = []
                season_name = seasons_data[season_idx].get('text', f'Season {season_idx}')
                logger.info(f"Starting season: {season_name}")
                
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
                        
                        # get match data
                        match_data = await Scraper.extract_match_data(match_page)
                        match_data['url'] = match_href
                        match_data['match_id'] = match_href.split('/')[-1] if '/' in match_href else match_href
                        
                        # add data to list
                        season_matches.append(match_data)
                        match_data['season'] = season_name

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
                saved = Scraper.save_season_to_database(season_matches, season_name)
                total_saved = saved
                logger.info(f"Season {season_name} complete")
                season_matches.clear()
                gc.collect()
                
            await browser.close()
            logger.info(f"Scraping completed matches collected : {len(season_matches)}")
            
            return total_saved
                    
if __name__ == "__main__":
    asyncio.run(Scraper.scraper())