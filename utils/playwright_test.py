import asyncio
import os

async def main():
    print('Python version:', os.sys.version.replace('\n', ' '))
    print('DISPLAY:', os.environ.get('DISPLAY'))
    try:
        from playwright.async_api import async_playwright
    except Exception as e:
        print('Playwright import error:', repr(e))
        return

    try:
        async with async_playwright() as p:
            print('Launching chromium (headless=True)...')
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            print('Going to Naver finance market sum...')
            await page.goto('https://finance.naver.com/sise/sise_market_sum.naver', timeout=30000)
            title = await page.title()
            print('Page title:', title)
            await browser.close()
            print('Browser closed — success')
    except Exception as e:
        print('Runtime error during browser test:', repr(e))

if __name__ == '__main__':
    asyncio.run(main())
