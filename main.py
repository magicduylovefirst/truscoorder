import re
import json
import config
import os
import poplib
import time

from email.parser import BytesParser
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError #Handle POp up window check


from GoQ import GoQ
from Rakuraku import Rakuraku
from Orange import Orange



class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.started = False

    def start(self):
        if not self.started:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=False)
            self.started = True

    def new_context(self):
        if not self.started:
            raise Exception("BrowserManager not started yet")
        return self.browser.new_context()

    def stop(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.started = False
    def ensure_playwright_browsers():
    # Try to find a chromium browser; if missing, install it
        try:
            from playwright.__main__ import main as playwright_main
            # Optional: skip if already present
            # Default cache dir on Windows: %USERPROFILE%\AppData\Local\ms-playwright
            cache_dir = Path(os.environ.get("USERPROFILE", "")) / "AppData" / "Local" / "ms-playwright"
            if not cache_dir.exists() or not any(cache_dir.glob("**/chrome.exe")):
                print("Installing Playwright browsers (chromium)...")
                playwright_main(["install", "chromium"])
        except Exception as e:
            print("Playwright auto-install failed:", e)
            # Try to install anyway
            try:
                from playwright.__main__ import main as playwright_main
                print("Attempting to install browsers...")
                playwright_main(["install", "chromium"])
            except Exception as e2:
                print("Second attempt failed:", e2)
   
    
if __name__ == "__main__":
    
    # Ensure Playwright browsers are installed
    manager = BrowserManager()
    manager.ensure_playwright_browsers()
    manager.start()

    context_goq = manager.new_context()
    context_orange = manager.new_context()
    context_raku = manager.new_context()

    orange = Orange(context_orange)
    goq = GoQ(context_goq, orange)
    goq.log_in()
    orange.log_in()  
    rakuraku = Rakuraku(context_raku)
    rakuraku.log_in()
    rakuraku.get_page_info()
    rakuraku. refactor_json()
    rakuraku.get_download_link()
    rakuraku.start_download()


    
    # goq.connect_existing_browser()
    
    goq.searching()

    

    manager.stop()
   
    
    
  