import re
import json
import config

from playwright.sync_api import sync_playwright



class Rakuraku:
    def __init__(self):
        self.url=config.RKRK_URL
        self.username=config.RKRK_USER
        self.password=config.RKRK_PASS
        self.browser = None
        self.context=None
        self.page=None
        self.timeout=10000
        self.valuable_headers = ['record_td_0_0_99-137222','record_td_0_0_99-137224','record_td_0_0_99-137226']
        return
    def log_in(self):
        playwright=sync_playwright().start()
        self.browser = playwright.chromium.launch(headless=False)
        self.page = self.browser.new_page()
        self.page.goto(self.url)
        self.page.fill('#loginId', self.username)
        self.page.fill('#loginPassword', self.password)
        self.page.click('#jq-loginSubmit')
        
        # Wait for the page to load after login
        self.page.wait_for_load_state('networkidle')
        print("Logged into Rakuraku successfully.")
        
    #test purpose
    def get_page_info(self):
        if not self.page:
            raise Exception("You must login first.")
        # Wait for the 'side' iframe to appear after login
        self.page.wait_for_selector('iframe#side', timeout=self.timeout)
        side_frame = self.page.frame(name="side")     
        # Wait for the トラスコ発注 span in the iframe
        side_frame.wait_for_selector('#treeViewData_12_span', timeout=self.timeout)
        # Click it
        side_frame.click('#treeViewData_12_span')
        print("Clicked トラスコ発注 (treeViewData_12_span) in menu iframe.")

        self.page.wait_for_selector('iframe#main',timeout=self.timeout)
        main_frame=self.page.frame(name="main")
        
        main_frame.wait_for_load_state('domcontentloaded', timeout=self.timeout)
        # Now get HTML and text
        main_html = main_frame.content()
        with open("main_frame_after_click.html", "w", encoding="utf-8") as f:
            f.write(main_html)
        print("Saved main_frame_after_click.html")
        
        main_frame.wait_for_selector('table#tableRecordFix',timeout=self.timeout)
        table=main_frame.query_selector('table#tableRecordFix')
        
        #Get the headers
        # headers=[]
        # headers_row=table.query_selector_all('tr')
        # for row in headers_row:
        #     ths=row.query_selector_all('th')
        #     for th in ths:
        #         th_id=th.get_attribute('id')
        #         th_text=th.text_content().strip()
        #         if th_id and th_text:
        #             headers.append({'id': th_id, 'text': th_text})
        #Get data rows
        all_rows=[]
        BREAK_POINT='発注済'
        found_break_point=False
        
        trs=table.query_selector_all('tr')
        for row in trs:
            tds=row.query_selector_all('td')
            row_data=[]
            row_id=row.get_attribute('id')
            if row_id=='null':
                continue
            for td in tds:
                td_id=td.get_attribute('id')
                td_text=td.text_content().strip()
                #I need to get the 2nd td too
                if td_id in self.valuable_headers:
                    row_data.append({'id': td_id, 'text': td_text})
                if td_text==BREAK_POINT:
                    found_break_point=True
                    break
            if row_data:
                if found_break_point:
                    break
                else:
                    all_rows[row_id] = row_data
        with open("table_data.json", "w", encoding="utf-8") as f:
            json.dump({'rows': all_rows}, f, ensure_ascii=False, indent=4)
        self.page.screenshot(path="screenshot_after_login.png")
        print("Screenshot saved as 'screenshot_after_login.png'")     
        
    def search_order(self):
        return 
    def handle_information(self,filename="table_data.json"):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            all_rows = data.keys()
            pattern= r'^(\d{6})-([^-]+-.+)'
            if not all_rows:
                print("No rows found in the table.")
                return
            for row in all_rows:
                for parts in row:
                #handle the VA発注番号
                    if parts.get('id') == 'record_td_0_0_99-137224':
                        try:
                            order_number = parts['text']
                            print(f"Order Number: {order_number}")
                            match = re.match(pattern, order_number)
                            if match:
                                order_number = match.group(2)
                            parts['text'] = order_number
                        except Exception as e:
                            print(f"Error processing row {parts['id']}: {e}") 
                    
                    json.dump(row, f, ensure_ascii=False, indent=4)
        return
    def download_order(self, folder_path="Downloads"):
        return 
    def close(self):
        if self.browser:
            self.browser.close()
    
class Order:
    def __init__(self):
        return    
    def log_in(self):
        return
    def upload_file(self):
        return
    
    
class GoQ:
    def __init__(self):
        return
    def log_in(self):
        return
    def search_order(self):
        return url
    def get_info(self,url):
        return
    
if __name__ == "__main__":
    agent=Rakuraku()
    agent.log_in()
    agent.get_page_info()
    input("Press enter to close")
    agent.close()