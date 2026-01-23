import asyncio
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Statistic:
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
                
            # Extract home team with multiple selector attempts
            home_team_element = await match_page.query_selector('.duelParticipant__home .participant__participantName a')
            if not home_team_element:
                home_team_element = await match_page.query_selector('.duelParticipant__home .participant__participantName')
            if not home_team_element:
                home_team_element = await match_page.query_selector('[class*="participant__home"] [class*="participantName"]')
            
            if home_team_element:
                match_data['home_team'] = (await home_team_element.inner_text()).strip()
                logger.debug(f"Extracted home team: {match_data['home_team']}")
            else:
                logger.warning("Could not find home team element")
                match_data['home_team'] = None

            # Extract away team with multiple selector attempts
            away_team_element = await match_page.query_selector('.duelParticipant__away .participant__participantName a')
            if not away_team_element:
                away_team_element = await match_page.query_selector('.duelParticipant__away .participant__participantName')
            if not away_team_element:
                away_team_element = await match_page.query_selector('[class*="participant__away"] [class*="participantName"]')
            
            if away_team_element:
                match_data['away_team'] = (await away_team_element.inner_text()).strip()
                logger.debug(f"Extracted away team: {match_data['away_team']}")
            else:
                logger.warning("Could not find away team element")
                match_data['away_team'] = None

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
                current_url = match_page.url
                logger.info(f"Current URL: {current_url}")

                if '/mecz/' in current_url:
                    # remove query parameters temporarily
                    base_url = current_url.split('?')[0]
                    query_params = current_url.split('?')[1] if '?' in current_url else ''
                    
                    # remove trailing slash if exists
                    base_url = base_url.rstrip('/')
                    
                    # construct statistics URL
                    stats_url = f"{base_url}/szczegoly/statystyki/0/"
                    if query_params:
                        stats_url += f"?{query_params}"
                    
                    logger.info(f"Navigating to statistics: {stats_url}")
                    
                    try:
                        await match_page.goto(stats_url, wait_until="domcontentloaded", timeout=15000)
                        
                        # wait for content to load
                        await asyncio.sleep(2)
                        
                        try:
                            await match_page.wait_for_selector('[data-testid="wcl-statistics"]', timeout=8000)
                            logger.info("Statistics elements appeared")
                        except:
                            logger.warning("Statistics elements did not appear in time")
                        
                        # now scrape detailed statistics with retry logic
                        detailed_stats = await Statistic.extract_detailed_statistics(match_page)
                        logger.info(f"Extracted detailed stats: {len(detailed_stats)} sections")
                        
                        match_data['detailed_statistic'] = detailed_stats
                        
                    except Exception as nav_error:
                        logger.error(f"Error navigating to statistics URL: {nav_error}")
                        match_data['detailed_statistic'] = {}
                else:
                    logger.warning(f"Unexpected URL format: {current_url}")
                    match_data['detailed_statistic'] = {}
                    
            except Exception as e:
                logger.error(f"Error processing statistics: {e}")
                match_data['detailed_statistic'] = {}
                
            logger.info(f"Extracted data for {match_data.get('home_team', 'Unknown')} vs {match_data.get('away_team', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Error extracting match data: {e}")
        
        return match_data