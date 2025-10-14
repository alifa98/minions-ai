import asyncio

import httpx
import structlog
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

logger = structlog.get_logger()


async def fetch_page_content(url: str) -> str:
    """Fetch and clean page content, trying httpx first, then Playwright for JS-heavy sites."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        # Stage 1: Fast static fetch
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')

            # Basic check for meaningful content
            if len(soup.get_text(strip=True)) > 300:
                # Remove boilerplate
                for element in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
                    element.decompose()
                return soup.get_text(separator='\n', strip=True)

        # Stage 2: If static content is sparse, use Playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, wait_until='domcontentloaded', timeout=20000)
            await asyncio.sleep(2)  # Allow JS to render
            content = await page.content()
            await browser.close()
            soup = BeautifulSoup(content, 'lxml')
            for element in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
                element.decompose()
            return soup.get_text(separator='\n', strip=True)

    except Exception as e:
        logger.error("fetch_page_content_failed", url=url, error=str(e))
        return ""
