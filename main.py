import re
import json
import config
import os
import poplib
import time

from email.parser import BytesParser
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError #Handle POp up window check

from browser_manager import BrowserManager

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
    
if __name__ == "__main__":
    
    

    manager = BrowserManager()
    manager.start()

    context_goq = manager.new_context()
    context_orange = manager.new_context()
    context_raku = manager.new_context()

    orange = Orange(context_orange)
    goq = GoQ(context_goq, orange)
    rakuraku = Rakuraku(context_raku)
    rakuraku.log_in()
    rakuraku.get_page_info()
    rakuraku. refactor_json()
    rakuraku.get_download_link()
    rakuraku.start_download()
    rakuraku.refactor_json()
    rakuraku.close()   
    
    # goq.connect_existing_browser()
    goq.log_in()
    orange.log_in()  
    goq.searching()

    

    manager.stop()
   
    
    
    # orange=Orange()    
    # # orange.log_in()    
    # # orange.fetch_auth_code_from_email()
    # # orange.connect_existing_browser()
    # # orange.start_import()
    
    # goq=GoQ()
    # goq.log_in()
    # # goq.connect_existing_browser()
    # goq.searching()