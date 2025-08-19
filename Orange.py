import re
import json
import config
import os
import poplib
import time

from email.parser import BytesParser
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

class Orange:
    def __init__(self, context_orange=None):
        self.url=config.O_URL
        self.company_id=config.O_COMPANY_ID
        self.username=config.O_USER
        self.password=config.O_PASS        
        self.browser = None
        self.context=context_orange
        self.page=None
        self.timeout=10000
        self.file_name="table_data.json"
        self.error_file="error.json"
        self.MTR_link="https://www.orange-book.com/ja/f/view/OB3110S23001.xhtml?definiteFileType=2"
        self.TRI_link="https://www.orange-book.com/ja/f/view/OB3110S23001.xhtml?definiteFileType=1"
        self.warning_mess=["本商品は、廃番商品のため、注文できません。"]
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

    
    def start_import_single(self, product_code, downloaded_file, description,customer_information):
        """
        Process a single record for import without reading from JSON file
        customer_information is a dict of 
         {
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
        """
        try:
            print(f"[Processing single record for product_code: {product_code}]")
            
            # If no page is available, try to connect or return error
            if not self.page:
                if self.context:
                    self.page = self.context.new_page()
                else:
                    return {"error": "No browser context available"}
            # pull data (ensure keys exist)
            ci = customer_information or {}
            name          =self. _cap20(ci.get("name", ""))
            incharge_name = self._cap20(ci.get("incharge_name", ""))
            postal1       = ci.get("postal1", "") or ""
            postal2       = ci.get("postal2", "") or ""
            phone1        = ci.get("phone1", "") or ""
            phone2        = ci.get("phone2", "") or ""
            phone3        = ci.get("phone3", "") or ""
            address1      = self._cap20(ci.get("address1", ""))
            address2      = self._cap20(ci.get("address2", ""))
            address3      = self._cap20(ci.get("address3", ""))
            
            # ========== Case: 見積り ==========
            if "送料別途見積り" in description:
                try:
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
                        self.log_error(product_code, "missing_file", "Missing downloaded_file")
                        return {"error": "Missing downloaded_file"}
                    
                    # Confirm filename was set in UI
                    filename_field = self.page.query_selector('input#inputFileName')
                    if filename_field:
                        print("UI shows:", filename_field.input_value())         
                           
                    self.page.click('#btn-excelin')
                    # Select radio option
                    self.page.wait_for_selector('label:has(input#deliveryKbn_4)', timeout=self.timeout)
                    self.page.click('label:has(input#deliveryKbn_4)')
                    time.sleep(1)

                    # Check for error field 
                    value_field= 'input#detailData1List\\:0\\:articleNameFixed'
                    warning_field='p.p-warning--type-02.u-font14'
                    value=None
                    if self.page.is_visible(value_field, timeout=self.timeout):
                        value = self.page.get_attribute(value_field, 'value')
                        # Fill product code
                        print("Value: ",value)
                        self.page.wait_for_selector('input#abstr', timeout=self.timeout)
                        self.page.fill('input#abstr', product_code)
                        self.page.wait_for_load_state("load")
                        self.page.click("#btn-estimateConfirm")
                    warning_text = None
                    if self.page.is_visible(warning_field, timeout=500):
                        warning_el = self.page.query_selector(warning_field)
                        print("Warning: ",warning_el)
                        if warning_el:
                            warning_text = warning_el.text_content().strip()
                            error_msg = warning_text or f"Cannot order article: {value}"
                            print(f"[Error] {error_msg}")
                            self.log_error(product_code, "order_error", error_msg)
                            return error_msg
                    # value = self.page.get_attribute('input#detailData1List\\:0\\:articleNameFixed', 'value')
                    # warning = self.page.query_selector('p.p-warning--type-02.u-font14')                                     
                    self.page.wait_for_selector('#directName1', timeout=self.timeout)    

                    

                    # Name / Incharge (全角 20 max per spec)
                    self._fill_if_exists('#directName1', name, "Name (directName1)")
                    self._fill_if_exists('#directName3', incharge_name, "Incharge (directName3)")

                    # Postal (half-width expected; ids commonly directZipNo1/2)
                    self._fill_if_exists('#directZipNo1', postal1, "Postal1 (directZipNo1)")
                    self._fill_if_exists('#directZipNo2', postal2, "Postal2 (directZipNo2)")
                    
                    # Phone blocks (half-width digits)
                    self._fill_if_exists('#directTelNo1', phone1, "Phone1 (directTelNo1)")
                    self._fill_if_exists('#directTelNo2', phone2, "Phone2 (directTelNo2)")
                    self._fill_if_exists('#directTelNo3', phone3, "Phone3 (directTelNo3)")

                    # Address lines (20 max each)
                    self._fill_if_exists('#directAddress1', address1, "Address1 (directAddress1)")
                    self._fill_if_exists('#directAddress2', address2, "Address2 (directAddress2)")
                    self._fill_if_exists('#directAddress3', address3, "Address3 (directAddress3)")

                    

                    print("[Info] Finished filling recipient info.")
                    self.page.click("#btn-save")
                    #Next page
                    self.page.wait_for_selector('#btn-save', timeout=self.timeout)
                    self.page.click('#btn-save')
                    self.page.wait_for_load_state("domcontentloaded")
                    #Next page
                    self.page.wait_for_selector('#btn-estimateFix', timeout=self.timeout)
                    self.page.click('#btn-estimateFix')
                    self.page.wait_for_load_state("domcontentloaded")
                    #Last page confirm
                    self.page.wait_for_selector('#btn-estimateFix', timeout=self.timeout)
                    self.page.once("dialog", lambda dialog: (print(f"[Dialog] {dialog.message}"), dialog.accept()))
                    try:
                        with self.page.expect_event("dialog", timeout=3000) as di:
                            self.page.click('#btn-estimateFix')
                        di.value.accept()
                    except PlaywrightTimeoutError:
                        # No dialog showed up; just ensure the click happened
                        self.page.click('#btn-estimateFix')
                    # Handle the confirm dialog
                    
                    self.page.wait_for_load_state("domcontentloaded")
                    result_sel = "div.p-panel-10__item p.u-font24"
                    self.page.wait_for_selector(result_sel, timeout=self.timeout)
                    result_text = self.page.text_content(result_sel).strip()

                    print(f"[Result] {result_text}")
                    return result_text
                
                
                except PlaywrightTimeoutError as te:
                    print(f"[Timeout] Timeout error for product_code {product_code}: {te}")
                    self.log_error(product_code, "timeout", str(te))
                    return {"error": "timeout", "continue": True}
                except Exception as e:
                    print(f"[Exception] Error in MTR case for product_code {product_code}: {e}")
                    self.log_error(product_code, "exception", str(e))
                    return {"error": str(e), "continue": True}

            # ========== Case: TRI ==========
            elif "法人・事業所限定" in description:
                try:
                    # if name in vars.corp_keywords or     
                    print(f"[TRI case] Product code: {product_code}")
                    return {"status": "success", "type": "TRI"}
                except PlaywrightTimeoutError as te:
                    print(f"[Timeout] Timeout error in TRI case for product_code {product_code}: {te}")
                    self.log_error(product_code, "timeout", str(te))
                    return {"error": "timeout", "continue": True}
                except Exception as e:
                    print(f"[Exception] Error in TRI case for product_code {product_code}: {e}")
                    self.log_error(product_code, "exception", str(e))
                    return {"error": str(e), "continue": True}
            
            else:
                print(f"[Info] No matching case for product_code: {product_code}")
                return {"status": "skipped", "reason": "No matching case"}
                
        except PlaywrightTimeoutError as te:
            print(f"[Timeout] General timeout error for product_code {product_code}: {te}")
            self.log_error(product_code, "timeout", str(te))
            return {"error": "timeout", "continue": True}
        except Exception as e:
            print(f"[Exception] Error processing product_code {product_code}: {e}")
            self.log_error(product_code, "exception", str(e))
            return {"error": str(e), "continue": True}
    def _cap20(self,s: str) -> str:
            s = s or ""
            return s[:20]  # hard cap to 20 chars

    def _fill_if_exists(self, selector: str, value: str, label: str):
        loc = self.page.locator(selector)
        if loc.count() > 0:
            loc.fill(value)
            print(f"[Fill] {label}: '{value}' -> {selector}")
            return True
        else:
            print(f"[Skip] {label} not found: {selector}")
            return False

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

                # This is testing
                input_infor={"name": "竹田 紀男",
                    "incharge_name": "",
                    "postal1": "134",
                    "postal2": "0013",
                    "phone1": "090",
                    "phone2": "8816",
                    "phone3": "9449",
                    "address1": "東京都江戸川区江戸川5-22-70",
                    "address2": "",
                    "address3": ""
                    }
                result = self.start_import_single(product_code, downloaded_file, description,input_infor)
                if result:
                    record["upload_result"] = result
                    
                
                datas[row_id] = [record]
                return
        except Exception as e:
            print(f"[Exception] Json Content Error: {e}")
            return None
        with open(self.file_name, "w", encoding="utf-8") as f:
            json.dump(datas, f, ensure_ascii=False, indent=2)
        print("[Done] Updated data saved.")
            
    def search_order(self)->str:
        return url
if __name__=="__main__":
    orange = Orange()
    orange.connect_existing_browser()
    orange.start_import()