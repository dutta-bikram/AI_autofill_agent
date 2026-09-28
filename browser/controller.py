import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext, Page
from browser.extractor import FormFieldExtractor, FormField
from browser.actions import BrowserActionHandler
from config import settings

class BrowserController:
    """Controls Playwright browser instances for form analysis and autonomous filling."""

    def __init__(self, headless: Optional[bool] = None, slow_mo: Optional[int] = None):
        self.headless = headless if headless is not None else settings.HEADLESS_BROWSER
        self.slow_mo = slow_mo if slow_mo is not None else settings.BROWSER_SLOW_MO
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.action_handler: Optional[BrowserActionHandler] = None

    async def start(self) -> Page:
        """Launches the browser and initializes a new page."""
        if self.page and not self.page.is_closed():
            return self.page

        self.playwright = await async_playwright().start()
        # Launch Chromium with anti-bot detection evasions & clean UI
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        self.page = await self.context.new_page()
        self.action_handler = BrowserActionHandler(self.page, slow_mo_ms=self.slow_mo, highlight=settings.HIGHLIGHT_ELEMENTS)
        return self.page

    async def navigate(self, url: str) -> bool:
        """Navigates to the specified URL and waits for DOM to load."""
        if not self.page:
            await self.start()
        try:
            print(f"[BrowserController] Navigating to: {url}")
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(1.0)
            return True
        except Exception as e:
            print(f"[BrowserController] Navigation error ({url}): {e}")
            return False

    async def extract_form_fields(self) -> List[FormField]:
        """Extracts all interactable form fields from the current page."""
        if not self.page:
            raise RuntimeError("Browser is not open. Call navigate() first.")
        fields = await FormFieldExtractor.extract_fields(self.page)
        print(f"[BrowserController] Detected {len(fields)} form field(s).")
        return fields

    async def fill_field(self, field: FormField, value: str) -> bool:
        """Fills a single field using the action handler."""
        if not self.action_handler:
            return False
        return await self.action_handler.fill_field(field, value)

    async def take_screenshot(self, output_path: str) -> str:
        """Captures a screenshot of the current page state."""
        if not self.page:
            return ""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        await self.page.screenshot(path=output_path, full_page=False)
        return output_path

    async def submit_form(self) -> bool:
        """Attempts to click a submit button or submit the form."""
        if not self.page:
            return False
        try:
            # Look for standard submit button or button with text 'Submit', 'Apply', 'Next', 'Send'
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Submit")',
                'button:has-text("Apply")',
                'button:has-text("Send")',
                'button:has-text("Save")'
            ]
            for sel in submit_selectors:
                btn = self.page.locator(sel).first
                if await btn.count() > 0 and await btn.is_visible():
                    print(f"[BrowserController] Clicking submit element: {sel}")
                    await self.action_handler.highlight_element(sel, color="#ef4444")
                    await asyncio.sleep(0.5)
                    await btn.click()
                    await asyncio.sleep(1.5)
                    return True
            return False
        except Exception as e:
            print(f"[BrowserController] Submit error: {e}")
            return False

    async def close(self):
        """Cleanly closes page, browser, and playwright instance."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"[BrowserController] Close error: {e}")
        finally:
            self.page = None
            self.browser = None
            self.playwright = None
