import re
import json
import config
import os
import poplib
import time

from email.parser import BytesParser
from playwright.sync_api import sync_playwright

class Orange:
    def __init__(self,context_orange):
        self.url=config.O_URL
        self.company_id=config.O_COMPANY_ID
        self.username=config.O_USER
        self.password=config.O_PASS        
        self.browser = None
        self.context=context_orange
        self.page=None
        self.timeout=10000
        self.file_name="table_data.json"
        self.MTR_link="https://www.orange-book.com/ja/f/view/OB3110S23001.xhtml?definiteFileType=2"
        self.TRI_link="https://www.orange-book.com/ja/f/view/OB3110S23001.xhtml?definiteFileType=1"
        return
    def log_in(self):
        self.page = self.context.new_page()
        self.page.goto(self.url)
        self.page.fill('#companyId',self.company_id)
        self.page.fill('#loginId', self.username)
        self.page.fill('#password', self.password)
        self.page.click('#btn-login')
        
        # Wait for the page to load after login
        self.page.wait_for_load_state('networkidle')
        #Input otp
        #wait for the email to be sent
        timeout = 5
        time.sleep(timeout)
        otp=self.fetch_auth_code_from_email()
        print(otp)
        self.page.wait_for_selector('input#authcCd', timeout=self.timeout)
        self.page.fill('input#authcCd', otp)
        self.page.click('#btn-signIn')
        # After login there will be an extra step to confirm login
        self.page.wait_for_selector('#btn-login', timeout=self.timeout)
        self.page.click('#btn-login')
        self.page.wait_for_load_state('networkidle')
        print("Logged into Orange successfully.")
        if not self.page:
            raise Exception("You must login first.")
        
        return
    
    def fetch_auth_code_from_email(self):
        email_user=config.O_MAIL_USER
        email_pass=config.O_MAIL_PASS
        pop_server=config.O_MAIL_HOST
        
        max_check=5  # check the newest 5 emails
       
        try:
            mailbox = poplib.POP3_SSL(pop_server)
            mailbox.user(email_user)
            mailbox.pass_(email_pass)
            print("Logined")
             # Get message count
            num_messages = len(mailbox.list()[1])
            if num_messages == 0:
                print(" メールが見つかりません。")
                return

            # Check last N messages (to avoid spam)
            for i in range(num_messages, max(0, num_messages - 10), -1):
                resp, lines, octets = mailbox.retr(i)
                raw_email = b'\r\n'.join(lines)
                msg = BytesParser().parsebytes(raw_email)
                

                # Filter by sender
                sender = msg.get("Resent-From") or msg.get("From") or msg.get("Return-Path") or ""
                if "info-f@first23.com" not in sender:
                    continue
                # print(msg)

                # Get body content
                # print(msg)
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()

                # Extract OTP (e.g. 認証コード 123456)
                otp_match = re.search(r"認証コード\s*([0-9]{6})", body)
                if otp_match:
                    otp = otp_match.group(1)
                    print(f" 認証コード取得: {otp}")
                    return otp

            print(" 認証コードが見つかりませんでした。")
            return None

        except Exception as e:
            print(f"POP3 Error: {e}")
            return None
    def connect_existing_browser(self):
        import asyncio
        import nest_asyncio
        
        # Always apply nest_asyncio to handle potential event loop conflicts
        nest_asyncio.apply()
        
        from playwright.sync_api import sync_playwright

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.connect_over_cdp("http://localhost:9222")
        context = self.browser.contexts[0]
        self.page = context.pages[0] if context.pages else context.new_page()
        print(" Connected to Chrome")

    
    def start_import_single(self, product_code, downloaded_file, description):
        """
        Process a single record for import without reading from JSON file
        """
        try:
            print(f"[Processing single record for product_code: {product_code}]")
            
            # ========== Case: 見積り ==========
            if "送料別途見積り" in description:
                self.page.goto(self.MTR_link)

                # Unhide file input
                self.page.wait_for_selector('button.js-attachmentfile__btn', timeout=self.timeout)
                self.page.eval_on_selector('input#fileInput', 'el => el.removeAttribute("hidden")')

                # Upload file
                if downloaded_file:
                    print(f"Uploading file: {downloaded_file}")
                    self.page.set_input_files('input#fileInput', downloaded_file)
                else:
                    print(f"[Error] Missing 'downloaded_file' for product_code {product_code}")
                    return {"error": "Missing downloaded_file"}

                # Confirm filename was set in UI
                filename_field = self.page.query_selector('input#inputFileName')
                if filename_field:
                    print("UI shows:", filename_field.input_value())

                
                self.page.click('#btn-excelin')
                # Select radio option
                self.page.wait_for_selector('label:has(input#deliveryKbn_4)')
                self.page.click('label:has(input#deliveryKbn_4)')

                # Fill product code
                self.page.wait_for_selector('input#abstr', timeout=self.timeout)
                # self.page.fill('input#abstr', product_code)

                # Check for error field after filling
                value = self.page.get_attribute('input#detailData1List\\:0\\:articleNameFixed', 'value')

                if value:
                    # Check if clickable <a> element exists
                    warning = self.page.query_selector('p.p-warning--type-02.u-font14')
                    if warning:
                        warning_text = warning.text_content().strip()
                        error_msg = warning_text or f"Cannot order article: {value}"
                        print(f"[Error] {error_msg}")
                        return {"error": error_msg}
                    else:
                        # All good → click confirm
                        self.page.click("#btn-estimateConfirm")

                
                time.sleep(5)
                return {"status": "success", "type": "見積り"}

            # ========== Case: TRI ==========
            elif "法人・事業所限定" in description:
                print(f"[TRI case] Product code: {product_code}")
                return {"status": "success", "type": "TRI"}
            
            else:
                print(f"[Info] No matching case for product_code: {product_code}")
                return {"status": "skipped", "reason": "No matching case"}
                
        except Exception as e:
            print(f"[Exception] Error processing product_code {product_code}: {e}")
            return {"error": str(e)}

    def start_import(self):       
        with open(self.file_name, "r", encoding="utf-8") as f:
            datas = json.load(f)
        try:
            for row_id, records in datas.items():
                print(f"[Processing row: {row_id}]")

                #  Flatten the list of dicts into one single dict
                record = {}
                for item in records:
                    if isinstance(item, dict):
                        record.update(item)

                description = record.get("description", "")
                downloaded_file = record.get("downloaded_file")
                product_code = record.get("product_code")

                # Use the new single import function
                result = self.start_import_single(product_code, downloaded_file, description)
                if result.get("error"):
                    record["error"] = result["error"]
                
                datas[row_id] = [record]
        except Exception as e:
            print(f"[Exception] Json Content Error: {e}")
            return None
        with open(self.file_name, "w", encoding="utf-8") as f:
            json.dump(datas, f, ensure_ascii=False, indent=2)
        print("[Done] Updated data saved.")
            
    def search_order(self)->str:
        return url
    