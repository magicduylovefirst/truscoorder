import re
import json
import config
import os
import poplib
import time
from var import corp_keywords

from email.parser import BytesParser
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError #Handle POp up window check



class GoQ:
    def __init__(self,context, orange_instance=None):
        self.url=config.GOQ_URL
        self.url_login=config.GOQ_LOGIN_URL
        self.username=config.GOQ_USER
        self.password=config.GOQ_PASS
        self.browser = None
        self.context=context
        self.page=None
        self.timeout=10000       
        self.main_frame=None
        self.file_name="table_data.json"
        self.orange = orange_instance
        return
    
    def log_in(self):
        #temporarialy comment out for testing
        self.page = self.context.new_page()
        self.page.goto(self.url_login)
        self.page.fill('form#js-loginForm >> input[name="code"]', self.username)
        self.page.fill('form#js-loginForm >> input[name="password"]', self.password)
        self.page.click('form#js-loginForm >> button[type="submit"]')
        #This step will confirm the auth
        self.page.wait_for_load_state("load")
        try:
            # Step 1: Check if GoQ login screen appears first
            goq_auth_btn = self.page.locator("button#js-loginGoqAuth")
            if goq_auth_btn.is_visible(timeout=5000):
                print("[Info] Found GoQアカウントでログイン button. Clicking it now...")
                goq_auth_btn.click()
                self.page.wait_for_load_state("networkidle")  # wait for page to finish loading
            else:
                print("[Info] GoQ login button not visible — skipping.")
                
        except TimeoutError:
            print("[Info] Timed out waiting for GoQ login button.")
        except Exception as e:
            print(f"[Info] GoQ login screen did not appear: {e}")

        # Step 2: Proceed with login3 button
        try:
            self.page.wait_for_selector("button#login3", timeout=self.timeout)
            self.page.click("button#login3")
        except TimeoutError:
            print("[Info] No terms of use appeared — continuing normally.")

        # Step 3: Handle pop-up window
        self.close_all_popups()
        return
    def close_all_popups(self, timeout=5000, max_popups=5):
        popup_selector = "#manage_pop_up_window"
        checkbox_selector = f"{popup_selector} input[type='checkbox']"
        close_button_selector = "#manage_puw_close"

        for i in range(max_popups):
            try:
                popup = self.page.locator(popup_selector)
                if not popup.is_visible(timeout=timeout):
                    print("[Info] No more popups detected.")
                    break

                print(f"[Info] Pop-up #{i + 1} detected. Checking checkboxes...")

                # Check all unchecked checkboxes
                checkboxes = self.page.locator(checkbox_selector)
                for j in range(checkboxes.count()):
                    cb = checkboxes.nth(j)
                    if not cb.is_checked():
                        cb.click()
                        print(f"[Auto] Checked checkbox {j}")
                    else:
                        print(f"[Auto] Checkbox {j} already checked")

                # Wait for close button to be enabled (i.e., not have class 'disabled')
                print("[Wait] Waiting for close button to be enabled...")
                self.page.wait_for_function("""
                    () => {
                        const btn = document.querySelector("#manage_puw_close");
                        return btn && !btn.classList.contains("disabled");
                    }
                """, timeout=timeout)

                # Click close button
                close_btn = self.page.locator(close_button_selector)
                close_btn.click()
                print(f"[Info] Closed popup #{i + 1}")

                # Wait for popup to disappear
                self.page.wait_for_selector(popup_selector, state="hidden", timeout=timeout)

                # Small delay between popups
                self.page.wait_for_timeout(500)

            except Exception as e:
                print(f"[Error] Failed while handling popup #{i + 1}: {e}")
                break


    def _wait_until_all_checkboxes_checked(self, popup_selector="#manage_pop_up_window"):
        """
        Optional: Use this only if you want an extra polling mechanism.
        Not required in new version.
        """
        print("[Wait] Verifying all checkboxes are checked...")
        checkbox_selector = f"{popup_selector} input[type='checkbox']"
        while True:
            all_checked = True
            checkboxes = self.page.locator(checkbox_selector)
            for j in range(checkboxes.count()):
                cb = checkboxes.nth(j)
                if not cb.is_checked():
                    all_checked = False
                    break
            if all_checked:
                print("[Success] All checkboxes are confirmed checked.")
                break
            else:
                self.page.wait_for_timeout(500)


    def connect_existing_browser(self):
        from playwright.sync_api import sync_playwright

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.connect_over_cdp("http://localhost:9222")
        context = self.browser.contexts[0]
        self.page = context.pages[0] if context.pages else context.new_page()
        print(" Connected to Chrome")
    def searching(self):
        self.page.goto(self.url)
        context = self.page.context  # Save the current browser context

        with open(self.file_name, "r", encoding="utf-8") as f:
            datas = json.load(f)

        for row_id, items in datas.items():
            # Flatten list of dicts into one flat dict
            record = {}
            for item in items:
                if isinstance(item, dict):
                    record.update(item)

            product_code = record.get("product_code")
            if not product_code:
                print(f"[Warning] Missing product_code for row {row_id}")
                continue

            print(f"[Action] Searching for product_code: {product_code}")

            # Save current tab
            original_tab = self.page

            # Watch for new tab opening after action
            with context.expect_page() as page_info:
                self.search_and_open_order_detail(product_code)  # This should trigger new tab
            new_tab = page_info.value

            # Work with the new tab
            self.page.screenshot(path="screenshot_after_login.png")
            new_tab.wait_for_load_state()
            print("[Info] Opened tab URL:", new_tab.url)

            self.process_detail_tab(new_tab,product_code)

            # Close new tab after processing (optional)
            new_tab.close()

            # Switch back to original tab
            original_tab.bring_to_front()
            self.page = original_tab  # Reset internal pointer to original tab

            # Run Orange import for this product
            if self.orange:
                # Get the record data for Orange import
                record = {}
                for item in items:
                    if isinstance(item, dict):
                        record.update(item)
                
                description = record.get("description", "")
                downloaded_file = record.get("downloaded_file")
                
                print(f"[Action] Running Orange import for product_code: {product_code}")
                result = self.orange.start_import_single(product_code, downloaded_file, description)
                print(f"[Orange Result] {result}")

            time.sleep(1)

           
            
    def search_and_open_order_detail(self, product_code):
        try:
            # 1. Fill search field
            self.page.fill('input#srh_onum', product_code)

            # 2. Click search
            self.page.click('input#search')
            self.page.wait_for_selector('#orderlisttable', timeout=5000)
            print(f"[Success] Search result loaded for {product_code}")

            # 3. Click the first order detail link (open in new tab)
            link = self.page.query_selector('#orderlisttable tr[id^="orderListRow_"] a[href*="order_details"]')
            if link:
                with self.page.expect_popup() as popup_info:
                    link.click()
                new_page = popup_info.value
                print("[Success] Order detail tab opened.")
                return new_page
            else:
                print(f"[Warning] No order link found for {product_code}")
                return None

        except Exception as e:
            print(f"[Error] Failed to search or open detail for {product_code}: {e}")
            return None

    def process_detail_tab(self, tab,product_code,output_file="details.json"):        
        tab.wait_for_load_state("domcontentloaded")
        print(f"[DEBUG] Processing detail tab for product_code: {product_code}")
        print("[Process] Extracting customer data...")
        html_content = tab.content()
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("[DEBUG] HTML content saved to debug_page.html")
        
        target_td = tab.locator('td:has(span.fontsz12)', has_text="送付先").first
        table_element = target_td.locator("xpath=ancestor::table").first        
        receiver_td = table_element.locator("tr").nth(1).locator("td").first        
        receiver_text = receiver_td.inner_text().strip().split("\n")
        receiver_text = [line.strip() for line in receiver_text if line.strip()] 
        print(f"[DEBUG] Raw receiver_text: {receiver_text}")
       
        full_name_kana = receiver_text[0]
        name = full_name_kana.split('[')[0].strip()
        print(f"[DEBUG] Full name with kana: {full_name_kana}")
        print(f"[DEBUG] Extracted name: {name}")
                              
        postal_raw = receiver_text[1].replace("〒", "").strip().replace("-", "")
        postal1 = postal_raw[:3]
        postal2 = postal_raw[3:]
        print(f"[DEBUG] Raw postal: {receiver_text[1]} -> processed: {postal_raw} -> postal1: {postal1}, postal2: {postal2}")
        
        address = receiver_text[2]
        print(f"[DEBUG] Original address: {address}")
        
        phone_raw = receiver_text[3].replace("TEL：", "").replace("-", "").strip()
        phone1 = phone_raw[:3]
        phone3 = phone_raw[-4:]
        phone2 = phone_raw[3:-4] 
        print(f"[DEBUG] Raw phone: {receiver_text[3]} -> processed: {phone_raw} -> phone1: {phone1}, phone2: {phone2}, phone3: {phone3}")

        incharge_name = ""
        print(f"[DEBUG] Incharge name: {incharge_name}")
        
        # Filter address using corporate keywords
        filtered_address = address
        for keyword in corp_keywords:
            if keyword in address:
                parts = address.split(keyword)
                if len(parts) > 1:
                    # Remove the corporate part and keep the address part
                    filtered_address = parts[-1].strip()
                    print(f"[DEBUG] Found keyword '{keyword}' in address, filtered to: {filtered_address}")
                    break
        
        # Split filtered address into components
        address_parts = filtered_address.split()
        address1 = address_parts[0] if len(address_parts) > 0 else ""
        address2 = address_parts[1] if len(address_parts) > 1 else ""
        address3 = " ".join(address_parts[2:]) if len(address_parts) > 2 else ""
        print(f"[DEBUG] Address parts: address1='{address1}', address2='{address2}', address3='{address3}'")
        
        result = {
        "name": name,
        "incharge_name": incharge_name,
        "postal1": postal1,
        "postal2": postal2,
        "phone1": phone1,
        "phone2": phone2,
        "phone3": phone3,
        "address1": address1,
        "address2": address2,
        "address3": address3
        }
        print(f"[DEBUG] Final result: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[Saved] to {output_file}")
        return result




if __name__ == "__main__":
    html_block="""
        山三鋳造(株) 中洋一[ヤマサンチュウゾウカブ ナカヨウイチ]
〒 722-0037
広島県尾道市西御所町14-22
TEL： 0848-23-2001
"""
    goq=GoQ()
    # goq.log_in()
    
    goq.connect_existing_browser()
    goq.searching()
    # agent = CustomerInfoExtractor(api_key=config.GEMINI_API)
    # result = agent.extract(html_block)
    # print(result)