# AIエージェント - 自動受注処理システム

3つのプラットフォーム（楽々、GoQ、Orange）を統合し、受注処理と管理ワークフローを合理化するPythonベースの自動化システム。

## 概要

本システムは以下により受注処理パイプラインを自動化します：
1. **楽々** - 注文データの取得と見積書/発注書の生成
2. **GoQ** - 注文詳細と顧客情報の処理
3. **Orange** - 注文のインポートと製品カタログ操作の処理

## 機能

- **マルチプラットフォーム統合**: 楽々、GoQ、Orangeシステムをシームレスに接続
- **自動データ処理**: 顧客情報、住所、製品コードの抽出と処理
- **エラーハンドリング**: 包括的なログ記録とエラー追跡システム
- **ブラウザ自動化**: Playwrightを使用した信頼性の高いWeb自動化
- **メール統合**: 認証用の自動OTP取得
- **法人・個人判定**: ビジネスルールに基づくスマートフィルタリング

## システム構成

```
main.py → BrowserManager → [GoQ, Orange, 楽々] → データ処理 → 注文インポート
```

### 主要コンポーネント

- **BrowserManager**: ブラウザインスタンスとコンテキストの管理
- **GoQ**: 注文検索、顧客データ抽出、ステータス更新を処理
- **Orange**: 製品インポートとカタログ操作を管理
- **楽々**: 注文データの処理と文書生成

## インストール

1. リポジトリをクローン
2. 依存関係をインストール:
   ```bash
   pip install playwright
   playwright install chromium
   ```
3. `config.py`で認証情報を設定
4. OTP認証用にメールアクセスを設定

## 設定

`config.py`でプラットフォームの認証情報を更新:

```python
# プラットフォームURLとログイン認証情報
RKRK_URL = "your_rakuraku_url"
GOQ_URL = "your_goq_url"  
ORANGE_URL = "your_orange_url"

# 各プラットフォームのログイン認証情報
RKRK_USER = "your_username"
RKRK_PASS = "your_password"
# ... （追加の認証情報）
```

## 使用方法

### 基本操作

```python
python main.py
```

これにより以下が実行されます：
1. 各プラットフォーム用のブラウザコンテキストを初期化
2. 3つのシステム全てにログイン
3. 楽々から注文を処理
4. GoQで注文を検索・更新
5. 関連データをOrangeにインポート

### 個別プラットフォーム使用

各プラットフォームは独立して使用可能:

```python
# GoQ操作
goq = GoQ(context, orange_instance)
goq.log_in()
goq.searching()

# Orange操作
orange = Orange(context)
orange.log_in()
orange.start_import_single(product_code, file, description, customer_info)

# 楽々操作
rakuraku = Rakuraku(context)
rakuraku.log_in()
rakuraku.get_page_info()
```

## データフロー

1. **楽々**: 注文データを抽出 → `table_data.json`
2. **GoQ**: 各製品コードを処理:
   - 注文詳細を検索
   - 顧客情報を抽出
   - 注文ステータスと履歴を更新
3. **Orange**: ビジネスルールに基づいて処理されたデータをインポート

## ビジネスロジック

### 法人・個人判定
- キーワードマッチングを使用して法人顧客を識別
- 顧客タイプに基づいて異なる処理ルールを適用
- "法人・事業所限定"製品の特殊ケースを処理

### 住所処理
- 日本の住所のスマート解析
- 郵便番号のフォーマットと検証
- 電話番号の標準化

## エラーハンドリング

- `error/error_YYYYMMDD_HHMMSS.json`への包括的エラーログ
- Web操作のタイムアウト処理
- 自動再試行メカニズム
- 製品コード毎の詳細エラー追跡

## ファイル構造

```
AI Agents/
├── main.py                 # メイン統制スクリプト
├── config.py              # 設定と認証情報
├── GoQ/
│   └── GoQ.py             # GoQプラットフォーム統合
├── Orange/
│   └── Orange.py          # Orangeプラットフォーム統合
├── Rakuraku/
│   └── Rakuraku.py        # 楽々プラットフォーム統合
├── utils.py               # ユーティリティ関数
├── var.py                 # 変数定義
├── Downloads/             # ダウンロードファイル保存
├── error/                 # エラーログ
└── html_output/           # デバッグHTML出力
```

## 依存関係

- **playwright**: Web自動化フレームワーク
- **poplib**: OTP用メール取得
- **json**: データ処理
- **re**: テキスト処理と検証

## ログ記録

システムは以下の詳細ログを保持:
- 注文処理ステータス
- エラー条件とタイムアウト
- 顧客情報抽出
- プラットフォーム固有操作

## セキュリティ注意事項

- 認証情報は`config.py`に保存（安全に保管）
- OTP取得用のメールパスワード
- ブラウザセッションは適切に管理・終了

## 開発

機能を拡張するには:
1. 既存パターンに従って新しいプラットフォーム統合を追加
2. 基本クラスでエラーハンドリングを拡張
3. 各プラットフォームモジュールで新しいビジネスルールを追加
4. 必要に応じて設定を更新

## トラブルシューティング

- 詳細エラーログは`error/`ディレクトリを確認
- `config.py`の認証情報を確認
- ブラウザ自動化要素が変更されていないことを確認
- 全プラットフォームへのネットワーク接続を確認

---

# 開発者向けドキュメント

## コードフローとアーキテクチャ

### 実行フロー

```
1. main.pyが実行開始
2. BrowserManagerがChromiumブラウザを初期化
3. 3つの独立したブラウザコンテキストを作成（分離）
4. プラットフォームログインを並行実行
5. 楽々データ抽出 → table_data.json
6. GoQが各製品を順次処理
7. Orange インポートが条件付きで実行
8. ブラウザクリーンアップとシャットダウン
```

### 詳細コードフロー

#### 1. メインエントリーポイント（`main.py:44-78`）

```python
# ブラウザ初期化
manager = BrowserManager()
manager.start()

# 各プラットフォーム用の分離されたコンテキストを作成
context_goq = manager.new_context()
context_orange = manager.new_context() 
context_raku = manager.new_context()

# 依存性注入によるプラットフォーム実例化
orange = Orange(context_orange)
goq = GoQ(context_goq, orange)  # GoQはOrangeインスタンスを取得
rakuraku = Rakuraku(context_raku)
```

#### 2. 認証フェーズ

**楽々ログイン**（`Rakuraku.py:26-50`）:
- 基本フォーム認証
- メニューシステムへのiframeナビゲーション
- トラスコ発注メニューアイテムをクリック

**GoQログイン**（`GoQ.py:54-88`）:
- マルチステップOAuthフロー
- GoQアカウント認証ポップアップを処理
- 利用規約承認
- チェックボックス自動化によるポップアップウィンドウ管理

**Orangeログイン**（`Orange.py:49-76`）:
- 会社IDによるフォーム認証
- メールベースOTP取得
- 2段階確認プロセス

#### 3. データ抽出フェーズ（`Rakuraku.py:52-95`）

```python
def get_page_info(self):
    # "発注済"ステータスが見つかるまでテーブルデータを抽出
    all_rows = {}
    BREAK_POINT = '発注済'
    
    for row in table_rows:
        if row.text == BREAK_POINT:
            break
        # カラム抽出: 1,6,7,8,11,12,13
        row_data = extract_valuable_columns(row)
        all_rows[row_id] = row_data
    
    # table_data.jsonに保存
    save_json(all_rows)
```

#### 4. 注文処理ループ（`GoQ.py:168-276`）

```python
def searching(self):
    with open("table_data.json") as f:
        orders = json.load(f)
    
    for order_id, items in orders.items():
        product_code = extract_product_code(items)
        
        try:
            # 注文詳細用新タブを開く
            with context.expect_page() as page_info:
                self.search_and_open_order_detail(product_code)
            new_tab = page_info.value
            
            # 顧客情報を抽出
            customer_info = self.process_detail_tab(new_tab, product_code)
            
            # 条件付きOrangeインポート
            if customer_info and should_import_to_orange():
                result = orange.start_import_single(...)
                self.import_result(new_tab, result)
            
        except Exception as e:
            self.log_error(product_code, "exception", str(e))
```

### 主要クラスとメソッド

#### BrowserManager（`main.py:20-42`）
- **目的**: 一元化されたブラウザライフサイクル管理
- **メソッド**:
  - `start()`: PlaywrightとChromiumブラウザを初期化
  - `new_context()`: 分離されたブラウザコンテキストを作成
  - `stop()`: ブラウザリソースをクリーンアップ

#### GoQクラス（`GoQ/GoQ.py`）

**主要メソッド**:

1. **`log_in()`**（54-88行）:
   - 複雑なOAuthフローを処理
   - チェックボックス自動化によるポップアップウィンドウ管理
   - 認証エッジケースのエラーハンドリング

2. **`searching()`**（168-276行）:
   - メイン処理ループ
   - 並行操作のタブ管理
   - 製品コード毎のエラーログ

3. **`process_detail_tab()`**（310-425行）:
   - CSSセレクタを使用した顧客データ抽出
   - 日本語住所解析ロジック
   - 法人対個人顧客判定

4. **`import_result()`**（426-558行）:
   - GoQシステムの注文履歴を更新
   - ステータスを"発注"（175）に変更
   - バリデーション付きフォーム送信

#### Orangeクラス（`Orange/Orange.py`）

**認証フロー**:
1. 会社IDによるフォームログイン
2. POP3経由でメールOTP取得
3. 2段階確認プロセス

**主要機能**:
- OTP用メール統合（`fetch_auth_code_from_email()`）
- ビジネスルール検証付き製品インポート
- 廃番製品のエラーハンドリング

#### 楽々クラス（`Rakuraku/Rakuraku.py`）

**データ抽出プロセス**:
1. iframeベースインターフェースへのナビゲート
2. 選択的カラムフィルタリングによるテーブルデータ抽出
3. "発注済"ステータスで処理停止
4. 構造化JSON出力の生成

## 詳細技術実装

### メールOTPシステム（`Orange.py:78-132`）

Orangeプラットフォームはメールベース2要素認証が必要:

```python
def fetch_auth_code_from_email(self):
    # POP3サーバーに接続
    mailbox = poplib.POP3_SSL(pop_server)
    mailbox.user(email_user)
    mailbox.pass_(email_pass)
    
    # OTP用に最新10件のメッセージを確認
    for i in range(num_messages, max(0, num_messages - 10), -1):
        resp, lines, octets = mailbox.retr(i)
        raw_email = b'\r\n'.join(lines)
        msg = BytesParser().parsebytes(raw_email)
        
        # 送信者でフィルター
        sender = msg.get("Resent-From") or msg.get("From") or ""
        if "info-f@first23.com" not in sender:
            continue
            
        # 正規表現でOTPを抽出
        otp_match = re.search(r"認証コード\s*([0-9]{6})", body)
        if otp_match:
            return otp_match.group(1)
```

### データ処理パイプライン

#### JSONデータ変換（`Rakuraku.py:96-138`）

生のテーブルデータを構造化フォーマットに変換:

```python
def refactor_json(self):
    for outer_key, records in data.items():
        updated_list = []
        for i, item in enumerate(records):
            value = list(item.values())[0]
            if i == 1:  # 注文番号
                updated_list.append({"order_number": value})
            elif i == 4:  # 製品コード処理
                updated_list.append({"product_code": value})
                # "20250901-0218519373"から意味のある部分を抽出
                parts = [p.strip() for p in value.split('-') if p.strip()]
                if len(parts) >= 3:  
                    updated_list[-1]["product_code"] = "-".join(parts[1:])
            elif i == 5:  # ダウンロードコード
                updated_list.append({"download_code": value})
            elif i == 6:  # 説明
                updated_list.append({"description": value})
```

**データ構造の進化例**:

生データ抽出:
```json
{
  "recordTr_242968_0": [
    {"recordAct_242968": ""},
    {"record_td_0_0_99-137224": "1177794"},
    {"record_td_0_0_99-137226": "20250901-0218519373"}
  ]
}
```

リファクタリング後:
```json
{
  "recordTr_242968_0": [
    {"order_number": "1177794"},
    {"product_code": "0218519373"},
    {"description": "■アストロプロダクツ AP 4連バキュームゲージ..."}
  ]
}
```

### 高度住所処理アルゴリズム

#### 法人キーワード検出（`var.py:1-28`）

システムは包括的な日本の法人実体検出を使用:

```python
corp_keywords = [
    # 伝統的企業
    "株式会社", "有限会社", "合同会社", "合名会社", "合資会社",
    "(株)", "(有)", "(同)",
    # 財団・社団
    "一般社団法人", "一般財団法人", "公益社団法人", "公益財団法人",
    # 医療・教育
    "医療法人", "宗教法人", "社会福祉法人", "学校法人",
    # 政府・特殊実体
    "独立行政法人", "地方独立行政法人", "国立大学法人"
]

# 後続テキストが必要なキーワード（例："株式会社 ABC商事"）
after_keywords = ["(株)", "(有)", "(同)", "(医)", ...]
```

#### 住所解析ロジック（`GoQ.py:352-381`）

法人実体処理を含む複雑な日本語住所処理:

```python
for keyword in corp_keywords:
    if keyword in address:
        parts = address.split(keyword, 1)
        
        if keyword in after_keywords:
            # 略称の後の会社名を取得
            # "(株)ABC商事" → "ABC商事"
            processed_address = (keyword + parts[-1]).strip()
        else:
            # 完全形式の前、最後の住所番号の後の会社名を取得
            # "東京都港区1-2-3 ABC株式会社" → "ABC株式会社"
            before_text = parts[0]
            number_matches = list(re.finditer(r'[\d０-９]', before_text))
            if number_matches:
                last_number_end = number_matches[-1].end()
                processed_address = (before_text[last_number_end:] + keyword).strip()
```

### ファイルダウンロード管理（`Rakuraku.py:202-252`）

エラーハンドリング付き自動ファイルダウンロード:

```python
def start_download(self, download_dir="Downloads"):
    # ダウンロードディレクトリを作成
    os.makedirs(download_dir, exist_ok=True)
    
    # 各行を処理
    for row_id, cells in data.items():
        row = self.main_frame.query_selector(f'tr#{row_id}')
        tds = row.query_selector_all('td')
        
        # 8列目にダウンロードリンクが含まれる
        td = tds[8]
        link = td.query_selector('a')
        
        # Playwrightでダウンロードを処理
        with self.page.expect_download() as download_info:
            link.click()
        download = download_info.value
        
        # 元のファイル名で保存
        save_path = os.path.join(download_dir, download.suggested_filename)
        download.save_as(save_path)
        
        # ファイルパスでJSONを更新
        data[row_id].append({"downloaded_file": save_path})
```

### Orangeインポートプロセス（`Orange.py:150-299`）

複雑なマルチステップインポートワークフロー:

#### 1. ファイルアップロードと製品検証
```python
# 自動化用ファイル入力を表示
self.page.eval_on_selector('input#fileInput', 'el => el.removeAttribute("hidden")')

# Excelファイルをアップロード
self.page.set_input_files('input#fileInput', downloaded_file)

# 製品コードを検証
value_field = f'input#detailData1List\\:{row_idx}\\:articleNameFixed'
warning_field = 'p.p-warning--type-02.u-font14'

# 廃番警告をチェック
if self.page.is_visible(warning_field, timeout=self.timeout):
    warning_text = warning_el.text_content().strip()
    if warning_text in self.warning_mess:
        return {"error": "Product discontinued"}
```

#### 2. 顧客情報入力
```python
# 名前検証（20文字制限）
def _cap20(self, text):
    return text[:20] if text else ""

# 検証付き顧客フィールドを入力
self._fill_if_exists('#directName1', self._cap20(name), "Name")
self._fill_if_exists('#directName3', self._cap20(incharge_name), "Incharge")

# 住所処理（20文字セグメントに分割）
address1 = full_addr[:20]
address2 = full_addr[20:40] if len(full_addr) > 20 else ""
address3 = full_addr[40:60] if len(full_addr) > 40 else ""
```

### エラーハンドリングアーキテクチャ

#### マルチレベルエラーログ（`GoQ.py:34-53`）

```python
def log_error(self, product_code, error_status, error_message=""):
    # 既存エラーを読み込むか新しいファイルを作成
    if os.path.exists(self.error_file):
        with open(self.error_file, "r", encoding="utf-8") as f:
            error_data = json.load(f)
    else:
        error_data = {}
    
    # タイムスタンプ付きエラーエントリを追加
    error_data[product_code] = {
        "status": error_status,           # timeout, exception, skip
        "message": error_message,         # 詳細エラー説明
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # タイムスタンプファイルに保存: error/error_YYYYMMDD_HHMMSS.json
    with open(self.error_file, "w", encoding="utf-8") as f:
        json.dump(error_data, f, ensure_ascii=False, indent=2)
```

#### ビジネスルール検証（`GoQ.py:221-240`）

制限製品の特別処理:

```python
# 個人顧客に対する法人限定製品をスキップ
if "法人・事業所限定" in description and "送料別途見積り" not in description:
    # 顧客名/住所に法人キーワードが含まれているかチェック
    target_text = f"{customer_info.get('name', '')} {customer_info.get('address', '')}"
    is_corporate = any(kw in target_text for kw in corp_keywords)
    
    if not is_corporate:
        msg = "法人・事業所限定ですが宛先に法人名が見つかりません。自動skip"
        self.log_error(product_code, "skip", msg)
        skip_import = True
```

### ポップアップ管理システム（`GoQ.py:89-158`）

動的ポップアップの自動処理:

```python
def close_all_popups(self, timeout=5000, max_popups=5):
    popup_selector = "#manage_pop_up_window"
    checkbox_selector = f"{popup_selector} input[type='checkbox']"
    
    for i in range(max_popups):  # 最大5つのポップアップを処理
        try:
            # ポップアップの可視性を待機
            popup = self.page.locator(popup_selector)
            if not popup.is_visible(timeout=timeout):
                break
                
            # 未チェックのチェックボックスを自動チェック
            checkboxes = self.page.locator(checkbox_selector)
            for j in range(checkboxes.count()):
                cb = checkboxes.nth(j)
                if not cb.is_checked():
                    cb.click()
            
            # 閉じるボタンが有効になるまで待機
            self.page.wait_for_function("""
                () => {
                    const btn = document.querySelector("#manage_puw_close");
                    return btn && !btn.classList.contains("disabled");
                }
            """, timeout=timeout)
            
            # 閉じるボタンをクリックし、消失を待機
            close_btn = self.page.locator("#manage_puw_close")
            close_btn.click()
            self.page.wait_for_selector(popup_selector, state="hidden")
            
        except Exception as e:
            print(f"[Error] ポップアップ#{i + 1}の処理に失敗: {e}")
            break
```

### データ検証と処理

#### 顧客情報構造
```json
{
  "name": "臼井工務店臼井誠",          // 会社名+個人名
  "incharge_name": "",               // 担当者名（分離されている場合）
  "postal1": "571",                  // 郵便番号の最初3桁
  "postal2": "0012",                 // 郵便番号の最後4桁
  "phone1": "090",                   // 市外局番
  "phone2": "3165",                  // 中間桁
  "phone3": "0045",                  // 最後4桁
  "address1": "大阪府門真市江端町16ー14", // 住所の最初20文字
  "address2": "",                    // 次の20文字（必要な場合）
  "address3": ""                     // 残りの文字（必要な場合）
}
```

#### 電話番号処理（`GoQ.py:340-344`）
```python
phone_raw = receiver_text[3].replace("TEL：", "").replace("-", "").strip()
phone1 = phone_raw[:3]      # "090"
phone3 = phone_raw[-4:]     # "0045" 
phone2 = phone_raw[3:-4]    # "3165"
```

### ブラウザコンテキスト管理

#### 分離戦略（`main.py:48-56`）
```python
# クロスコンタミネーションを防ぐため個別コンテキストを作成
context_goq = manager.new_context()      # GoQ操作
context_orange = manager.new_context()   # Orange操作
context_raku = manager.new_context()     # 楽々操作

# クロスプラットフォーム操作用の依存性注入
orange = Orange(context_orange)
goq = GoQ(context_goq, orange)  # GoQはOrangeインポートをトリガー可能
```

#### タブ管理パターン（`GoQ.py:193-255`）
```python
# 現在のタブ状態を保存
original_tab = self.page

try:
    # 新しいタブ作成を監視
    with context.expect_page() as page_info:
        self.search_and_open_order_detail(product_code)
    new_tab = page_info.value
    
    # 分離されたタブで作業
    customer_info = self.process_detail_tab(new_tab, product_code)
    
    # 条件付きクロスプラットフォーム操作
    if customer_info and self.orange:
        result = self.orange.start_import_single(...)
        self.import_result(new_tab, result)
    
finally:
    # 常にクリーンアップして状態を復元
    new_tab.close()
    original_tab.bring_to_front()
    self.page = original_tab
```

### パフォーマンスと信頼性機能

#### タイムアウト管理
- **ログイン操作**: 10秒
- **ページ読み込み**: ネットワークアイドル検出
- **要素検索**: フォールバック付き10秒
- **ファイル操作**: タイムアウトなし（システム依存）

#### エラー回復戦略
1. **接続失敗**: 指数バックオフでリトライ
2. **要素が見つからない**: CSSセレクタフォールバック
3. **認証問題**: セッション状態保持
4. **ファイルダウンロード失敗**: パス検証とリトライ

#### デバッグとモニタリング
- **HTML ダンプ**: トラブルシューティング用`html_output/`に保存
- **スクリーンショット**: 重要ワークフローポイントで取得
- **コンソールログ**: 操作コンテキスト付きタイムスタンプ
- **JSON 永続化**: すべての中間状態を保存