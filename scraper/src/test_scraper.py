
import asyncio
from playwright.async_api import async_playwright

async def test_basic_scraper():
    """Test basic Playwright functionality"""
    print("Starting Playwright test...")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  
        page = await browser.new_page()

        url = "https://www.flashscore.pl/mecz/pilka-nozna/jagiellonia-bialystok-lIDaZJTc/lech-poznan-OpNH7Ouf/?mid=ILxxk2t1"
        print(f"Navigating to: {url}")
        
        await page.goto(url, wait_until="networkidle")

        title = await page.title()
        print(f"Page title: {title}")

        await asyncio.sleep(3)
        
        await browser.close()
        print("Test complete!")

if __name__ == "__main__":
    asyncio.run(test_basic_scraper())