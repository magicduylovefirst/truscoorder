import re
import json
import config
import os
import poplib
import time
from var import corp_keywords, after_keywords, address_keywords
from datetime import datetime

from email.parser import BytesParser
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError #Handle POp up window check

from Orange.Orange import Orange


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
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.error_file = f"error_{now}.json"
        self.orange = orange_instance
        return
    
    def log_error(self, product_code, error_status, error_message=""):
        try:
            if os.path.exists(self.error_file):
                with open(self.error_file, "r", encoding="utf-8") as f:
                    error_data = json.load(f)
            else:
                error_data = {}
            
            error_data[product_code] = {
                "status": error_status,
                "message": error_message,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(self.error_file, "w", encoding="utf-8") as f:
                json.dump(error_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"[Error] Failed to log error for {product_code}: {e}")
    
    def log_in(self):
        #temporarialy comment out for testing
        self.page = self.context.new_page()
        self.page.goto(self.url_login)
        self.page.fill('form#js-loginForm >> input[name="code"]', self.username)
        self.page.fill('form#js-loginForm >> input[name="password"]', self.password)
        self.page.click('form#js-loginForm >> button[type="submit"]')
        #This step will confirm the auth
        # self.page.wait_for_load_state("load")
        time.sleep(1)
        try:
            # Step 1: Check if GoQ login screen appears first
            goq_auth_btn = self.page.locator("button#js-loginGoqAuth")
            if goq_auth_btn.is_visible(timeout=self.timeout):
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

            try:
                print(f"[Action] Searching for product_code: {product_code}")

                # Save current tab
                original_tab = self.page

                # Watch for new tab opening after action
                try:
                    with context.expect_page() as page_info:
                        self.search_and_open_order_detail(product_code)  # This should trigger new tab
                    new_tab = page_info.value

                    # Work with the new tab
                    # self.page.screenshot(path="screenshot_after_login.png")
                    new_tab.wait_for_load_state()
                    print("[Info] Opened tab URL:", new_tab.url)

                    customer_information=self.process_detail_tab(new_tab,product_code)
                    
                    # Run Orange import for this product only if customer_information was successfully extracted
                    if customer_information and self.orange:
                        # Get the record data for Orange import
                        record = {}
                        for item in items:
                            if isinstance(item, dict):
                                record.update(item)
                        
                        description = record.get("description", "")
                        downloaded_file = record.get("downloaded_file")
                        
                        print(f"[Action] Running Orange import for product_code: {product_code}")
                        result = self.orange.start_import_single(product_code, downloaded_file, description,customer_information)
                        print(f"[Orange Result] {result}")
                        #Orange Input, temporary set as test
                        self.import_result(new_tab, result);
                    else:
                        print(f"[Skip] Skipping Orange import for {product_code} due to failed customer information extraction")

                    # Close new tab after processing (optional)
                    new_tab.close()

                    # Switch back to original tab
                    original_tab.bring_to_front()
                    self.page = original_tab  # Reset internal pointer to original tab

                except TimeoutError as te:
                    print(f"[Timeout] Timeout error for product_code {product_code}: {te}")
                    self.log_error(product_code, "timeout", str(te))
                    # Continue to next product instead of breaking
                    continue
                except Exception as e:
                    print(f"[Exception] Error processing product_code {product_code}: {e}")
                    self.log_error(product_code, "exception", str(e))
                    # Continue to next product instead of breaking
                    continue
                
            except Exception as e:
                print(f"[Exception] General error for product_code {product_code}: {e}")
                self.log_error(product_code, "general_exception", str(e))
                # Continue to next product instead of breaking
                continue
            
            time.sleep(1)

           
            
    def search_and_open_order_detail(self, product_code):
        try:
            # 1. Fill search field
            self.page.fill('input#srh_onum', product_code)

            # 2. Click search
            self.page.click('input#search')
            self.page.wait_for_selector('#orderlisttable', timeout=self.timeout)
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

        except TimeoutError as te:
            print(f"[Timeout] Timeout error in search_and_open_order_detail for {product_code}: {te}")
            self.log_error(product_code, "timeout", str(te))
            return None
        except Exception as e:
            print(f"[Error] Failed to search or open detail for {product_code}: {e}")
            self.log_error(product_code, "exception", str(e))
            return None

    

    def process_detail_tab(self, tab,product_code,output_file="details.json"):
        try:        
            tab.wait_for_load_state("domcontentloaded", timeout=self.timeout)
            print(f"[DEBUG] Processing detail tab for product_code: {product_code}")
            print("[Process] Extracting customer data...")
            html_content = tab.content()
            # with open("html_output/debug_page.html", "w", encoding="utf-8") as f:
            #     f.write(html_content)
            # print("[DEBUG] HTML content saved to html_output/debug_page.html")
            
            target_td = tab.locator('td:has(span.fontsz12)', has_text="送付先").first
            table_element = target_td.locator("xpath=ancestor::table").first        
            receiver_td = table_element.locator("tr").nth(1).locator("td").first        
            receiver_text = receiver_td.inner_text().strip().split("\n")
            receiver_text = [line.strip() for line in receiver_text if line.strip()] 
            print(f"[DEBUG] Raw receiver_text: {receiver_text}")
           
            full_name_kana = receiver_text[0]
            name = full_name_kana.split('[')[0].strip().replace(" ","")
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
                    # Split on the first occurrence of the keyword
                    parts = address.split(keyword, 1)
                    
                    if keyword in after_keywords:
                        # Get text AFTER the keyword (current behavior)
                        filtered_address = (keyword + parts[-1]).strip()
                        print(f"[DEBUG] Found keyword '{keyword}' in address, getting text AFTER: {filtered_address}")
                    else:
                        # Get text BEFORE the keyword, but after the last number, INCLUDING the keyword
                        before_text = parts[0]
                        # Find the last number in the before text
                        import re
                        # Match any digit (including full-width digits like ６３)
                        number_matches = list(re.finditer(r'[\d０-９]', before_text))
                        if number_matches:
                            # Get position after the last number
                            last_number_end = number_matches[-1].end()
                            filtered_address = (before_text[last_number_end:] + keyword).strip()
                            print(f"[DEBUG] Found keyword '{keyword}' in address, getting text AFTER last number INCLUDING keyword: {filtered_address}")
                        else:
                            # No numbers found, take all text before keyword plus the keyword
                            filtered_address = (before_text + keyword).strip()
                            print(f"[DEBUG] Found keyword '{keyword}' in address, no numbers found, getting text BEFORE INCLUDING keyword: {filtered_address}")
                    break
            
            # Remove address keywords from the beginning of filtered address
            for addr_keyword in address_keywords:
                if filtered_address.startswith(addr_keyword):
                    filtered_address = filtered_address[len(addr_keyword):].strip()
                    print(f"[DEBUG] Removed address keyword '{addr_keyword}' from beginning of filtered address: {filtered_address}")
                    break
            
            # Split filtered address into components
            # Simple split by 20 characters each
            addr = filtered_address.strip()

            address1 = addr[:20]
            address2 = addr[20:40] if len(addr) > 20 else ""
            address3 = addr[40:60] if len(addr) > 40 else ""
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
            #call Orange to get the input result
           
            # Import result to history table (using the correct tab parameter)
            
            print(f"[DEBUG] Final result: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"[Saved] to {output_file}")
            return result
            
        except TimeoutError as te:
            print(f"[Timeout] Timeout error in process_detail_tab for product_code {product_code}: {te}")
            self.log_error(product_code, "timeout", str(te))
            return None
        except Exception as e:
            print(f"[Exception] Error in process_detail_tab for product_code {product_code}: {e}")
            self.log_error(product_code, "exception", str(e))
            return None

    def import_result(self, tab, result):
        try:
            print("[Action] Looking for 対応履歴 table...")

            # 1) Find ALL tables that have a TD containing '対応履歴'
            candidates = tab.locator('table').filter(has=tab.locator('td:has-text("対応履歴")'))
            n = candidates.count()
            if n == 0:
                print("[Warning] No tables containing '対応履歴'. Dumping page...")
                with open("html_output/page_dump.html", "w", encoding="utf-8") as f:
                    f.write(tab.content())
                return False

            print(f"[Info] Found {n} candidate table(s). Saving each for debugging...")
            chosen_idx = None

            # 2) Save each candidate and pick the best one
            for i in range(n):
                t = candidates.nth(i)
                html = t.evaluate("el => el.outerHTML")
                # with open(f"html_output/history_table_candidate_{i}.html", "w", encoding="utf-8") as f:
                #     f.write(html)
                has_datetime_link = t.locator('a:has-text("日時を追加")').count() > 0
                has_textarea = t.locator("textarea#a52").count() > 0

                print(f"[Info] Candidate {i}: has_datetime_link={has_datetime_link}, has_textarea={has_textarea}")

                # Prefer a table that has the link; fallback to one with the textarea
                if chosen_idx is None and (has_datetime_link or has_textarea):
                    chosen_idx = i

            # If still not chosen, default to the last one (often the detailed block)
            if chosen_idx is None:
                chosen_idx = n - 1
                print(f"[Info] No strong match; falling back to candidate {chosen_idx}")

            history_table = candidates.nth(chosen_idx)
            table_html = history_table.evaluate("el => el.outerHTML")

            # 3) Try to get and save the '日時を追加' link HTML (if present)
            datetime_link = history_table.locator('a:has-text("日時を追加")').first
            
            # 4) Interact with textarea if present
            textarea = history_table.locator("textarea#a52")
            if textarea.count() == 0:
                print("[Warning] Textarea #a52 not found")
                return False                      

            current_content = textarea.input_value()
            print(f"[Info] Current textarea content: {current_content}")

            if result:
                new_content =  result + " デュイ\n自動実行します" + current_content 
                textarea.fill(new_content)
                print(f"[Success] Import result added to textarea: {result}")
                
            else:
                print("[Success] Datetime added to textarea (no extra text)")
            print("[Action] Looking for ひとことメモ table...")
            
            # 5) Click the link if it exists and is (likely) actionable
            if datetime_link.count() > 0:
                print("[Action] Clicking 日時を追加 link...")
                datetime_link.click()
                tab.wait_for_timeout(self.timeout)  

            # 1) Narrow to the first table that has the 'ひとことメモ' label
            memo_table = tab.locator("table").filter(
                has=tab.locator('td:has(span.fontsz12:has-text("ひとことメモ"))')
            ).first

            # # Optional: save that table's HTML
            # table_html = memo_table.evaluate("el => el.outerHTML")
            # with open("html_output/memo_table.html", "w", encoding="utf-8") as f:
            #     f.write(table_html)
            # print("[Saved] html_output/memo_table.html")

            # 2) Find its textarea#a9 inside that table
            textarea = memo_table.locator("textarea#a9").first
            if textarea.count() == 0:
                print("[Warning] textarea#a9 not found inside the ひとことメモ table")
                # Fallback: try global search (in case DOM differs)
                textarea_global = tab.locator("#a9")
                if textarea_global.count() == 0:
                    print("[Warning] Global textarea#a9 not found either")
                    raise RuntimeError("textarea#a9 not found")
                textarea = textarea_global.first
                print("[Info] Using global #a9 fallback")

            # 3) Read current value and re-input 
            current_value = textarea.input_value()
            textarea.fill(result+"\n"+current_value)
            print("[Success] Re-input into #a9")   
            #3.5 Change the status
            select_element = tab.locator('select#a6')
            if select_element.count() == 0:
                print("[Warning] 受注ステータス select#a6 not found.")
                raise RuntimeError("受注ステータス select#a6 not found")

            select_element.select_option("175")
            
            
            # 3) Click the '入力内容を反映する' submit button
            submit_btn = tab.locator('input[type="submit"][value="入力内容を反映する"]').first
            if submit_btn.count() == 0:
                raise RuntimeError("'入力内容を反映する' button not found")

            print("[Action] Clicking '入力内容を反映する' button...")
            submit_btn.click()

            # # Optional: wait for any processing/navigation after click
            # tab.wait_for_load_state("domcontentloaded")
            # Click 「入力内容を反映する」
            self.page.click('input[name="B016"]')

            # Wait for the page to update
            self.page.wait_for_load_state("load")
        except TimeoutError as te:
            print(f"[Timeout] Timeout error in import_result: {te}")
            return False
        except Exception as e:
            print(f"[Error] Failed to import result: {e}")
            time.sleep(10)
            # Optional: dump page on error
            try:
                with open("html_output/page_dump_on_error.html", "w", encoding="utf-8") as f:
                    f.write(tab.content())
                print("[Saved] html_output/page_dump_on_error.html")
            except Exception:
                pass
            return False


if __name__ == "__main__":
    
    # Simple test - create GoQ with None context for testing
    goq = GoQ(None)
    
    # Test the connect_existing_browser method
    try:
        goq.connect_existing_browser()
        print("[Success] Connected to existing Chrome browser")
        print(f"[Info] Current page URL: {goq.page.url}")
        
        # Test searching if we have data file
        if os.path.exists(goq.file_name):
            print(f"[Info] Found data file {goq.file_name}, starting search process")
            goq.searching()
        else:
            print(f"[Info] No data file {goq.file_name} found for searching")
            
    except Exception as e:
        print(f"[Error] Failed during browser operations: {e}")
        print(f"[Info] This is normal if browser/page was closed or if you need to login first")
   
    # Note: import_result requires a tab parameter and would be called within process_detail_tab