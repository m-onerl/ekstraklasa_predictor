
import asyncio
from playwright.async_api import async_playwright
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
class Scraper:
    
    @staticmethod
    async def extract_detailed_statistics(match_page):
        """Extract detailed statistics from the statistics tab"""
        detailed_stats = {}
        try:
            # find the sectionsWrapper that contains all statistics sections
            sections_wrapper = await match_page.query_selector('.//*[@id="detail"]/div[4]/div[2]/div[2]')
            
            if sections_wrapper:
                # get all sections within the wrapper
                sections = await sections_wrapper.query_selector_all('.section')
                logger.info(f"Found {len(sections)} statistics sections")
                
                for section in sections:
                    # get section header/title
                    section_header = await section.query_selector('.section__title')
                    if section_header:
                        section_title = (await section_header.inner_text()).strip()
                        
                        # initialize dict for this section
                        detailed_stats[section_title] = {}
                        
                        # get all stat rows within this section
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
        except Exception as e:
            logger.error(f"Error extracting detailed statistics: {e}")
        
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
            
            # get match status
            status_element = await match_page.query_selector('.fixedHeaderDuel__detailStatus')
            if status_element:
                match_data['status'] = (await status_element.inner_text()).strip()
            try:
                # look for the statistics tab link
                stats_tab = await match_page.query_selector('a[href*="szczegoly/statystyki"]')
                if stats_tab:
                    await stats_tab.click()
                    await asyncio.sleep(1)
                    
                    # now scrape detailed statistics
                    detailed_stats = await Scraper.extract_detailed_statistics(match_page)

            except Exception as e:
                logger.error(f"Error navigating to statistics tab: {e}")
                
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
            
            # get reffere name 
            referee_wrapper = await match_page.query_selector('.wcl-summaryMatchInformation_U4gpU')
            if referee_wrapper:
                info_values = await referee_wrapper.query_selector_all('.wcl-infoValue_grawU')
                info_labels = await referee_wrapper.query_selector_all('.wcl-infoLabel_xPJVi')
                
                for i, label_element in enumerate(info_labels):
                    label = (await label_element.inner_text()).strip()
                    
                    if i < len(info_values):
                        value = (await info_values[i].inner_text()).strip()
                        
                        if 'Sędzia' in label or 'Sedzia' in label:
                            match_data['referee'] = value
                        elif 'Stadion' in label:
                            match_data['stadium'] = value
                        elif 'Pojemność' in label or 'Pojemnosc' in label:
                            match_data['capacity'] = value
                        elif 'Frekwencja' in label:
                            match_data['attendance'] = value
            
            logger.info(f"Extracted data for {match_data.get('home_team', 'Unknown')} vs {match_data.get('away_team', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Error extracting match data: {e}")
        
        return match_data
        
    async def scraper():
        
        all_matches_data = []

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
                        
                        # get match data
                        match_data = await Scraper.extract_match_data(match_page)
                        match_data['url'] = match_href
                        match_data['match_id'] = match_href.split('/')[-1] if '/' in match_href else match_href
                        
                        # add data to list
                        all_matches_data.append(match_data)
                        logger.info(f"Added match data to list. Total matches: {len(all_matches_data)}")

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
            
            await browser.close()
            logger.info(f"Scraping completed matches collected : {len(all_matches_data)}")

            if all_matches_data:
                logger.info("Sample of match data:")
                logger.info(all_matches_data[0])
            
            return all_matches_data
                    
if __name__ == "__main__":
    asyncio.run(Scraper.scraper())