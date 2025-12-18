
import asyncio
from playwright.async_api import async_playwright


seasons = ["PKO BP Ekstraklasa 2025/2026", "PKO BP Ekstraklasa 2024/2025"]
async def test_basic_scraper():
    print("Starting Playwright test...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  
        page = await browser.new_page()

        url = "https://www.flashscore.pl/pilka-nozna/polska/pko-bp-ekstraklasa/archiwum/"
        print(f"Navigating to: {url}")
        
        await page.goto(url, wait_until="networkidle")
        for season in seasons:
            await page.click(season)
            title = await page.title()
            print(f"Page title: {title}")

        await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(test_basic_scraper())