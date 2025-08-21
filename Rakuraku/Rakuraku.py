import re
import json
import config
import os
import time

from playwright.sync_api import sync_playwright

class Rakuraku:
    def __init__(self, context):
        self.url=config.RKRK_URL
        self.username=config.RKRK_USER
        self.password=config.RKRK_PASS
        self.browser = None
        self.context=context
        self.page=None
        self.timeout=10000
        self.valuable_headers = ['record_td_0_0_99-137222','record_td_0_0_99-137224','record_td_0_0_99-137226']
        self.main_frame=None
        self.file_name="table_data.json"
        # <a href="javascript:actionExecuteSubmit('/bntz5xa/actionexe/unit/buttonId/106853/recordId/240381/dbgId/100117/dbSchemaId/101273/menuId/102243/actionId/5/start/0')" class="fw-btn-mini fw-btn" style="width:80.5px;" id="actionButton_106853">見積書作成</a>
        self.create_mitsukomi= '#actionButton_106853'
        #<a href="javascript:actionExecuteSubmit('/bntz5xa/actionexe/unit/buttonId/106851/recordId/240381/dbgId/100117/dbSchemaId/101273/menuId/102243/actionId/5/start/0')" class="fw-btn-mini fw-btn" style="margin-bottom:5px;width:80.5px;" id="actionButton_106851">発注書作成</a>
        self.create_order = '#actionButton_106851'
        return
    def log_in(self):
        self.page = self.context.new_page()
        self.page.goto(self.url)
        self.page.fill('#loginId', self.username)
        self.page.fill('#loginPassword', self.password)
        self.page.click('#jq-loginSubmit')
        
        # Wait for the page to load after login
        self.page.wait_for_load_state('networkidle')
        print("Logged into Rakuraku successfully.")
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
        self.main_frame=self.page.frame(name="main")
        self.main_frame.wait_for_load_state('domcontentloaded', timeout=self.timeout)
        
    #test purpose
    def get_page_info(self):
        
        # # Now get HTML and text
        # main_html = self.main_frame.content()
        # with open("html_output/main_frame_after_click.html", "w", encoding="utf-8") as f:
        #     f.write(main_html)
        # print("Saved html_output/main_frame_after_click.html")

        self.main_frame.wait_for_selector('table#tableRecordFix',timeout=self.timeout)
        table=self.main_frame.query_selector('table#tableRecordFix')
        #Get data rows
        all_rows={}
        BREAK_POINT='発注済'
        found_break_point=False
        
        trs=table.query_selector_all('tr')
        for row in trs:
            tds=row.query_selector_all('td')
            row_data=[]
            row_id=row.get_attribute('id')
            if not row_id:
                continue
            for idx, td in enumerate(tds):
                td_id = td.get_attribute('id')
                td_text = td.text_content().strip()
                if idx in [1, 6, 7, 8, 11, 12, 13]:
                    row_data.append({td_id: td_text})
                # elif td_id in self.valuable_headers:
                #     row_data.append({'id': td_id, 'text': td_text})
                if td_text==BREAK_POINT:
                    found_break_point=True
                    break
            if row_data:
                if found_break_point:
                    break
                else:
                    all_rows[row_id] = row_data
        with open(self.file_name, "w", encoding="utf-8") as f:
            json.dump(all_rows, f, ensure_ascii=False, indent=4)
            
        self.page.screenshot(path="screenshot_after_login.png")
        print("Screenshot saved as 'screenshot_after_login.png'")     
        
    
    def refactor_json(self):
        try:
            with open(self.file_name, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Get the outer dynamic key (assuming there's only one top-level key)
            for outer_key, records in data.items():
            

                updated_list = []
            

                for i, item in enumerate(records):
                    if not isinstance(item, dict):
                        updated_list.append(item)
                        continue
                    value = list(item.values())[0]  # get the value of the only key
                    if i == 1:
                        
                        updated_list.append({"order_number": value})
                    elif i == 4:                        
                        updated_list.append({"product_code": value})
                        parts = value.split('-')
                        if len(parts) >= 3:
                            short_code = "-".join(parts[-2:])
                            updated_list[-1]["product_code"] = short_code
                        
                    elif i == 5:
                        updated_list.append({"download_code": value})
                    elif i == 6:
                        updated_list.append({"description": value})
                    else:
                        updated_list.append(item)  # keep as-is

           
            # Replace the list with the updated one
                data[outer_key] = updated_list

            # Save back to file
            with open(self.file_name, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

        except Exception as e:
            print(f"Error: {e}")

    def get_download_link(self):
        """
        While the 発注済 status is not found,
        we will check the description of each row and click the appropriate button
        to create the download link for the order or estimate,
        and save the file to the specified directory.
        """    
        
        #Start to create the download links by clicking the buttons in the 2nd column
        print("Starting to process rows for download...")                   
            # When there are 2 lines, we will have some trouble
        while True:
            
            self.main_frame.wait_for_selector('table#tableRecordFix', timeout=self.timeout)
            table = self.main_frame.query_selector('table#tableRecordFix')
            try:
                status_cell = self.main_frame.query_selector('#record_td_0_0_99-137216')
                if not status_cell:
                    print("Status cell not found. Breaking.")
                    break

                status_text = status_cell.text_content().strip()
                print(f"Status: {status_text}")

                if status_text == '発注済':
                    print("Order already completed. Breaking.")
                    break
                description_cell = self.main_frame.query_selector('#record_td_0_0_99-137226')
                if not description_cell:
                    print("Description cell not found. Breaking.")
                    break
                description = description_cell.text_content().strip()
                # Temporaraly we will not handle the case when there are more than 2 lines
                #As well as update the download file_name                
                if self.main_frame.query_selector('#record_td_0_1_99-137222'):
                    continue
                if "送料別途見積り" in description:
                    download_button = self.create_mitsukomi                
                    
                elif "法人・事業所限定" in description:
                    download_button = self.create_order                    
                else:
                    download_button=None
                    print("Can not download")
                
                
                #click the button to trigger
                print(f"Processing row with description: {description}")
            
                self.main_frame.click(download_button)
                print(f"Clicked download button for row .")
                self.page.wait_for_selector('iframe#main', timeout=self.timeout)
                self.main_frame = self.page.frame(name="main")
                self.main_frame.wait_for_load_state('domcontentloaded', timeout=self.timeout)                
                self.main_frame.wait_for_selector('table#tableRecordFix', timeout=self.timeout)
                time.sleep(1)

            except Exception as e:
                print(f"Error clicking download button for row : {e}")               
            


    
    def start_download(self,download_dir="Downloads"):
        self.main_frame.wait_for_selector('table#tableRecordFix',timeout=self.timeout)
        
        #Create the download directory if it doesn't exist
        try:
            os.makedirs(download_dir, exist_ok=True)
        except Exception as e:
            print(f"Error creating download directory {download_dir}: {e}")
            return
        # Open the json file to get what to download
        try:
            with open(self.file_name, "r", encoding="utf-8") as f:
                data = json.load(f)
            for row_id, cells in data.items():
                #Find the line that has the row_id
                self.main_frame.wait_for_selector(f'tr#{row_id}', timeout=self.timeout)
                row=self.main_frame.query_selector(f'tr#{row_id}')
                tds=row.query_selector_all('td')
                try:
                    td=tds[8]
                    link=td.query_selector('a')
                    if not link:
                        print(f"No link found in row {row_id}. Skipping.")
                        continue
                    #start download
                    with self.page.expect_download() as download_info:
                        link.click()
                    download=download_info.value
                    #Save the file to the download directory
                    save_path = os.path.join(download_dir, download.suggested_filename)
                    download.save_as(save_path)
                    print(f"Downloaded file for row {row_id} to {save_path}")
                    data[row_id].append({ "downloaded_file": save_path})
                except Exception as e:
                    print(f"Error processing row {row_id}: {e}")
                    continue
            #Save the updated data back to the json file
            try:
                with open(self.file_name, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                print("Updated table_data.json with download paths.")
            except Exception as e:
                print(f"Error saving table_data.json: {e}")
                        
                
        except Exception as e:
            print(f"Error reading table_data.json: {e}")
            return
        
    def close(self):
        if self.browser:
            self.browser.close()   