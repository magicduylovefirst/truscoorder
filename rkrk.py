from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import csv
import os
from selenium.webdriver.support.ui import Select
import shutil
from datetime import datetime
from datetime import timedelta
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
import sys
from selenium.common.exceptions import NoAlertPresentException
import platform
from selenium.webdriver.chrome.options import Options
import tempfile
from selenium.webdriver.common.action_chains import ActionChains
import re
from selenium.webdriver.common.keys import Keys

HOJIN_KEYWORDS = [
    "会社", "法人", "協同組合", "信用金庫", "信用組合", "労働金庫", "社団", "財団",
    "病院", "医院", "クリニック", "歯科", "診療所", "薬局", "調剤薬局", "整骨院", "整体院", "接骨院", "動物病院", "訪問看護", "デイサービス",
    "大学", "短期大学", "専門学校", "高校", "高等学校", "中学", "中学校", "小学", "小学校", "保育園", "幼稚園", "こども園", "塾", "教室", "スクール",
    "商店", "○○店", "○○屋", "屋", "商会", "事務所", "支店", "出張所", "営業所", "センター", "工場", "倉庫", "研究所",
    "製作所", "製造所", "スタジオ", "開発", "建設", "建築", "不動産", "企画", "制作", "運送", "配送", "物流", "整備", "代行",
    "サービス", "デザイン", "プロダクション", "カンパニー", "グループ", "ホールディングス", "サロン", "美容室", "理容室", "エステ", "ペットショップ"
]


def parse_soufusaki(text: str) -> list:
    """
    送付先の文字列から [氏名, カナ, 郵便番号, 住所, 電話番号] を抽出してリストで返す。
    """
    lines = text.strip().splitlines()

    name = ''
    kana = ''
    postal_code = ''
    address = ''
    tel = ''

    for line in lines:
        line = line.strip()
        if re.match(r'^〒\s*\d{3}-\d{4}', line):
            postal_code = line.replace('〒', '').strip()
        elif line.startswith('TEL') or 'TEL' in line:
            tel = line.replace('TEL：', '').replace('TEL:', '').strip()
        elif re.search(r'\[.*\]', line):  # 氏名とカナを含む行
            match = re.match(r'(.+?)\[(.+?)\]', line)
            if match:
                name = match.group(1).strip()
                kana = match.group(2).strip()
        elif re.search(r'(県|府|都|道)', line):  # 住所とみなす行
            address = line.strip()

    return [name, kana, postal_code, address, tel]

def get_table_data(driver):
    from selenium.webdriver.common.by import By
    import time

    def scroll_to_bottom():
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    data_list = []
    row_index = 0
    max_empty_count = 10
    empty_count = 0

    while True:
        try:
            id_name = f"record_td_{row_index}_0_99-137219"
            id_price = f"record_td_{row_index}_0_99-137224"

            name_element = driver.find_element(By.ID, id_name)
            price_element = driver.find_element(By.ID, id_price)

            name = name_element.text.strip()
            price = price_element.text.strip()
            data_list.append([name, price])

            row_index += 1
            empty_count = 0
        except:
            scroll_to_bottom()
            time.sleep(0.5)
            empty_count += 1
            if empty_count >= max_empty_count:
                break

    return data_list


def show_and_click_hidden_button(driver, field_id):
    # 非表示要素の <span> のIDを生成
    span_id = f"filterButtn_{field_id}"

    # 1. JavaScriptで style.display を変更して表示状態に
    driver.execute_script(f"document.getElementById('{span_id}').style.display = 'inline';")

    # 2. JavaScriptでリンクを取得してクリック
    js_click = f"""
        var el = document.querySelector("#{span_id} a");
        if (el) el.click();
    """
    driver.execute_script(js_click)


def login_to_goq(driver):
    driver.get("https://order.goqsystem.com/goq21/form/goqsystem_new/systemlogin.php?q=172.31.25.245")
    driver.execute_script("document.body.style.zoom='75%'")
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.NAME, "login_id")))
    driver.find_element(By.NAME, "login_id").send_keys("iKQVh8s7")
    driver.find_element(By.NAME, "login_pw").send_keys("xnV6Ephv")
    driver.find_element(By.ID, "loginbtn1").click()
    wait.until(EC.presence_of_element_located((By.NAME, "seq_id")))
    driver.find_element(By.NAME, "seq_id").send_keys("agjSqOqg")
    driver.find_element(By.NAME, "seq_pw").send_keys("D30EhP5P")
    driver.find_element(By.XPATH, "//button[contains(text(),'ログイン')]").click()
    wait.until(EC.presence_of_element_located((By.NAME, "login3")))
    driver.find_element(By.ID, "login3").click()
    menu = wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "受注管理")))
    ActionChains(driver).move_to_element(menu).perform()
    # サブメニュー「受注管理」をクリック
    submenu = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[text()="受注管理" and contains(@href, "index.php")]')))
    submenu.click()
    popup = wait.until(EC.presence_of_element_located((By.ID, "manage_pop_up_window")))
    checkboxes = popup.find_elements(By.CSS_SELECTOR, '.info-check-box input[type="checkbox"]')
    for checkbox in checkboxes:
        if not checkbox.is_selected():
            driver.execute_script("arguments[0].click();", checkbox)
    close_button = driver.find_element(By.ID, "manage_puw_close")
    driver.execute_script("arguments[0].click();", close_button)
    
    # 対象の文字列
    target_text = "第三"    
    # XPath（部分一致に変更しておく）
    xpath = '//li[contains(@class, "order-tabs__item")]//a[contains(text(), "第三")]'
    # 要素の存在を確認して取得
    element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    # 要素を画面内にスクロール
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", element)
    # JavaScriptで強制クリック
    driver.execute_script("arguments[0].click();", element)
    
    return driver

def input_soufusaki(driver, soufusaki):
    name = soufusaki[0]
    zip_code = soufusaki[2]
    address = soufusaki[3]
    tel = soufusaki[4]

    # 郵便番号分割
    zip1, zip2 = zip_code.split('-') if '-' in zip_code else (zip_code[:3], zip_code[3:])

    # 住所分割（最初の数字で分ける）
    m = re.search(r'\d', address)
    if m:
        addr1 = address[:m.start()]
        addr2 = address[m.start():]
    else:
        addr1 = address
        addr2 = ''

    # 電話番号分割
    tel_parts = tel.split('-') if '-' in tel else (tel[:3], tel[3:7], tel[7:])

    # 入力
    driver.find_element(By.ID, 'directName1').send_keys(name)
    driver.find_element(By.ID, 'directZipNo1').send_keys(zip1)
    driver.find_element(By.ID, 'directZipNo2').send_keys(zip2)
    driver.find_element(By.ID, 'directTelNo1').send_keys(tel_parts[0])
    driver.find_element(By.ID, 'directTelNo2').send_keys(tel_parts[1])
    driver.find_element(By.ID, 'directTelNo3').send_keys(tel_parts[2])
    driver.find_element(By.ID, 'directAddress1').clear()
    driver.find_element(By.ID, 'directAddress1').send_keys(addr1)
    driver.find_element(By.ID, 'directAddress2').send_keys(addr2)
    
def login_to_rkrk(driver, login_url, username, password):
    """
    ログイン処理を行う関数
    """
    driver.get(login_url)
    
    wait = WebDriverWait(driver, 10)
    # ユーザーIDとパスワードを入力してログイン
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "loginId"))
    ).send_keys(username)
    driver.find_element(By.ID, "loginPassword").send_keys(password)
    driver.find_element(By.ID, "jq-loginSubmit").click()

def login_to_orange(driver, login_url, tenpo, username, password):
    """
    ログイン処理を行う関数
    """
    driver.get(login_url)
    
    # ユーザーIDとパスワードを入力してログイン
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "companyId"))
    ).send_keys(tenpo)
    driver.find_element(By.ID, "loginId").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.ID, "btn-login").click()
    wait = WebDriverWait(driver, 1000)
    # DOM上にある「Excelファイルから見積依頼」リンクを取得
    excel_link = wait.until(EC.presence_of_element_located(
        (By.XPATH, '//a[contains(text(), "Excelファイルから見積依頼")]')
    ))

    # JavaScriptでクリック（display:noneでも強制的に動かせる場合あり）
    driver.execute_script("arguments[0].click();", excel_link)    

def rkrk_data(driver, choice, file_name):
    """
    商品情報をアップロードする関数（安定化版）
    """
    wait = WebDriverWait(driver, 20)

    try:
        # 初期化
        driver.switch_to.default_content()
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "side")))

        # メニュー展開
        menu = wait.until(EC.element_to_be_clickable((By.ID, "viewMenu")))
        driver.execute_script("arguments[0].click();", menu)

        # 各リンククリック（順に実行）
        for link_text in ["受発注管理", "VA発注管理", "バロートラスコ発注"]:
            item = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, link_text)))
            driver.execute_script("arguments[0].click();", item)

        # メインフレームに切り替え
        driver.switch_to.default_content()
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "main")))

        # 非表示ボタンのクリック
        show_and_click_hidden_button(driver, "99-137226")

        # 検索欄に入力
        input_element = wait.until(EC.visibility_of_element_located((By.ID, "textCurrentValue")))
        input_element.clear()
        input_element.send_keys(choice)

        # 確定クリック
        confirm_button = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "確定")))
        driver.execute_script("arguments[0].click();", confirm_button)

        # アップロードボタン操作
        show_and_click_hidden_button(driver, "99-137216")
        time.sleep(1)

        # チェックボックスを順にクリック
        for checkbox_id in ["allSelectFlag", "selectionIdList_10"]:
            cb = wait.until(EC.element_to_be_clickable((By.ID, checkbox_id)))
            driver.execute_script("arguments[0].click();", cb)

        # 確定クリック（再）
        confirm_button2 = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "確定")))
        driver.execute_script("arguments[0].click();", confirm_button2)

        # セレクトボックスの操作
        select_element = wait.until(EC.presence_of_element_located((By.ID, "displayCount")))
        Select(select_element).select_by_value("500")

    except Exception as e:
        print(f"[エラー] rkrk_data関数の処理中に問題が発生しました: {e}")
        # # aタグを直接取得してクリック（JS経由）
        # link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#method_switch a")))
        # driver.execute_script("arguments[0].click();", link)
        # menu_button = wait.until(EC.element_to_be_clickable((By.ID, "link_menu_box")))
        # menu_button.click()
        # 商品マスタ = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "CSV出力")))
        # driver.execute_script("arguments[0].click();", 商品マスタ)
        # download_button = wait.until(EC.element_to_be_clickable((By.ID, "csv_confirm_start")))
        # download_button.click()

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        input("エラー発生のため、終了するにはEnterを押してください...")  # エラー発生時に終了を促す        

def search_with_driver(driver, keyword):
    # 検索ボックスに文字を入力
    search_box = driver.find_element(By.ID, "fullText_searchString")
    search_box.clear()
    search_box.send_keys(keyword)

    # 検索ボタンをクリック
    search_button = driver.find_element(By.ID, "fullTextSearch")
    search_button.click()            

def upload_rkrk_data(driver, radio, file_name):
    """
    商品情報をアップロードする関数
    """
    wait = WebDriverWait(driver, 10)
    file_path = os.path.join(os.getcwd(), file_name)
    try:        
        # iframe に切り替える（IDが 'side' のもの）
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "side")))

        # iframe 内の商品管理（親メニュー）をクリック
        商品管理 = wait.until(EC.element_to_be_clickable((By.LINK_TEXT,"商品管理")))
        driver.execute_script("arguments[0].click();", 商品管理)

        # 子メニュー「商品マスタ」をクリック（展開されている前提）
        商品マスタ = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "商品マスタ")))
        driver.execute_script("arguments[0].click();", 商品マスタ)
        
        # 子メニュー「商品マスタ」をクリック（展開されている前提）
        アップ画面 = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "登録・上書き(JAN無)(新)")))
        driver.execute_script("arguments[0].click();", アップ画面)
        
        # iframe に切り替える（IDが 'main' のもの）
        driver.switch_to.default_content()
        # main iframe に入る
        driver.switch_to.default_content()
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "main")))
        # input[name="filePath"] にファイル送信
        upload_input = wait.until(EC.presence_of_element_located((By.NAME, "filePath")))
        driver.execute_script("arguments[0].style.display = 'block';", upload_input)  # 必要なら可視化
        upload_input.send_keys(file_path)
        # # aタグを直接取得してクリック（JS経由）
        # link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#method_switch a")))
        # driver.execute_script("arguments[0].click();", link)

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        input("エラー発生のため、終了するにはEnterを押してください...")  # エラー発生時に終了を促す        
                        
def prepend_to_textareas(driver, my_var):
    """
    textarea #a52 と #a9 に指定のフォーマットでテキストを先頭追加する。

    - a52: ■[日付 時刻]\nmy_var\n（既存の先頭に追加）
    - a9:  my_var（改行なしで既存の先頭に追加）

    Parameters:
        driver : selenium.webdriver.Chrome などの WebDriver
        my_var : str - 追加したい文字列
    """

    # a52 用：日時 + my_var + 改行
    try:
        textarea_52 = driver.find_element(By.ID, "a52")
        existing_52 = textarea_52.get_attribute("value")
        now = datetime.now().strftime("■[%Y-%m-%d %H:%M:%S]")
        new_text_52 = f"{now}\n{my_var}\n{existing_52}"
        textarea_52.clear()
        textarea_52.send_keys(new_text_52)
    except Exception as e:
        print("a52の処理エラー:", e)

    # a9 用：my_var（改行なし）
    try:
        textarea_9 = driver.find_element(By.ID, "a9")
        existing_9 = textarea_9.get_attribute("value")
        new_text_9 = f"{my_var}{existing_9}"
        textarea_9.clear()
        textarea_9.send_keys(new_text_9)
    except Exception as e:
        print("a9の処理エラー:", e)
    
# ✅ 誰のパソコンでも共通の「ダウンロードフォルダ」取得
DOWNLOAD_ROOT = os.path.join(os.path.expanduser("~"), "Downloads")
DOWNLOAD_DIR = os.path.join(DOWNLOAD_ROOT, "my_downloader")  # サブフォルダを作成

# 📁 ダウンロードフォルダを初期化（削除→再作成）
def prepare_download_folder():
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR)

# 📥 ダウンロード用ドライバ作成
def setup_download_driver():
    options = Options()
    options.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "safebrowsing.enabled": True
    })
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def get_downloaded_file_path():
    files = [f for f in os.listdir(DOWNLOAD_DIR) if not f.endswith(".crdownload")]
    if len(files) != 1:
        raise Exception("ダウンロードフォルダ内にファイルが1つではありません")
    return os.path.join(DOWNLOAD_DIR, files[0])
    
        
def main():
    rklogin_url = 'https://hdtitan.htdb.jp/bntz5xa/top/index'
    rkusername = 'ryuji-tanaka'
    rkpassword = 'first-123'    
    
    
    driver = setup_download_driver()
    driver.set_window_size(1200, 900)

    # ブラウザを閉じない設定を追加
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    # オプションを driver に渡す
    driver2 = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait2 = WebDriverWait(driver2, 10)


    item="//input[@name='zr_item_upload.type' and @value='0']"
    
    driver3 = webdriver.Chrome(options=options)
    driver3.get("https://www.orange-book.com/ja/f/view/OB1110S01001.xhtml")
    wait3 = WebDriverWait(driver3, 10)
    
    try:
        login_to_goq(driver2)
        login_to_orange(driver3, "https://www.orange-book.com/ja/f/view/OB1110S01001.xhtml", "85514432", "firstorder", "first160DWS5")
        login_to_rkrk(driver, rklogin_url, rkusername, rkpassword)
    
        rkrk_data(driver, "[送料別途見積り]", 'db_m.csv')
        table_data = get_table_data(driver)
        filtered_data = [(d, v) for d, v in table_data if d.strip() and v.strip()]
        print(filtered_data)
    
        for den, vajutyu in filtered_data:
            if vajutyu.count("-") >= 2:
                pos = vajutyu.find("-")
                vajutyu = vajutyu[pos + 1:]
    
            search_with_driver(driver, vajutyu)
    
            # srh_onum に入力
            input_element = wait2.until(EC.presence_of_element_located((By.ID, "srh_onum")))
            input_element.clear()
            input_element.send_keys(vajutyu)
    
            # スクロールしてボタンをクリック
            search_button = wait2.until(EC.element_to_be_clickable((By.ID, "search")))
            driver2.execute_script("arguments[0].scrollIntoView(true);", search_button)
            driver2.execute_script("arguments[0].click();", search_button)
    
            # 元のタブを保存
            original_tab = driver2.current_window_handle
    
            # 該当リンクが表示されてクリックできるようになるのを待つ
            link = wait2.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, vajutyu)))
            link.click()
    
            # 新しいタブを取得して切り替え
            wait2.until(lambda d: len(d.window_handles) > 1)
            new_tab = [handle for handle in driver2.window_handles if handle != original_tab][0]
            driver2.switch_to.window(new_tab)
    
            # table内の"〒"を含む td 要素を取得
            table = wait2.until(EC.presence_of_element_located((By.XPATH, "//table[contains(@style, 'background-color:rgba(213,203,203,1.00)')]")))
            soufusaki_td = table.find_element(By.XPATH, ".//td[contains(., '〒')]")
            soufusaki_text = soufusaki_td.text
            soufusaki = parse_soufusaki(soufusaki_text)
            print(soufusaki)

            excel_link = wait3.until(EC.presence_of_element_located(
                (By.XPATH, '//a[contains(text(), "Excelファイルから見積依頼")]')
            ))

            # JavaScriptでクリック（display:noneでも強制的に動かせる場合あり）
            driver3.execute_script("arguments[0].click();", excel_link)
            # ファイルアップロード処理
            file_path = get_downloaded_file_path()
            file_input = wait3.until(EC.presence_of_element_located((By.ID, "fileInput")))
            file_input.send_keys(file_path)
    
            submit_btn = wait3.until(EC.element_to_be_clickable((By.ID, "btn-excelin")))
            submit_btn.click()
    
            # 「ユーザー様 直送」ボタンをクリック
            direct_btn = wait3.until(EC.element_to_be_clickable(
                (By.XPATH, "//span[@class='a-toggle__text' and normalize-space()='ユーザー様　直送']")
            ))
            direct_btn.click()
    
            # 抽出欄に入力
            abstr_input = wait3.until(EC.presence_of_element_located((By.ID, "abstr")))
            abstr_input.send_keys(vajutyu)
    
            # 見積確認ボタン
            estimate_btn = wait3.until(EC.element_to_be_clickable((By.ID, "btn-estimateConfirm")))
            driver3.execute_script("arguments[0].click();", estimate_btn)
            # 送付先情報を入力
            time.sleep(1)  # 少し待つ
            input_soufusaki(driver3, soufusaki)
            prepend_to_textareas(driver2, "これは追加する内容です")
    
            input("ここで一時停止しています。Enterキーで再開します >>> ")
    
            # 新しいタブを閉じて元のタブに戻る
            prepare_download_folder()
            driver2.close()
            driver2.switch_to.window(original_tab)
    
            print(den, vajutyu)
    
        print(f"取得件数: {len(filtered_data)} 件")
        rkrk_data(driver, "", 'db_m.csv')
        table_data = get_table_data(driver)
        filtered_data = [(d, v) for d, v in table_data if d.strip() and v.strip()]
        print(filtered_data)
        for den, vajutyu in filtered_data:
            if vajutyu.count("-") >= 2:
                pos = vajutyu.find("-")
                vajutyu = vajutyu[pos + 1:]
            print(den, vajutyu)
        print(f"取得件数: {len(filtered_data)} 件")        

    finally:
        # ウィンドウを閉じない
        input("ウィンドウを閉じるにはEnterを押してください...")  # 最後に閉じるためのプロンプト
        driver.quit()
        driver2.quit()
        driver3.quit()
# 使用例
main()
