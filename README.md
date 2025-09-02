# AI Agents - Automated Order Processing System

A Python-based automation system that integrates with three platforms (Rakuraku, GoQ, and Orange) to streamline order processing and management workflows.

## Overview

This system automates the order processing pipeline by:
1. **Rakuraku** - Fetching order data and generating quotes/orders
2. **GoQ** - Processing order details and customer information  
3. **Orange** - Importing orders and handling product catalog operations

## Features

- **Multi-platform Integration**: Seamlessly connects Rakuraku, GoQ, and Orange systems
- **Automated Data Processing**: Extracts and processes customer information, addresses, and product codes
- **Error Handling**: Comprehensive logging and error tracking system
- **Browser Automation**: Uses Playwright for reliable web automation
- **Email Integration**: Automatic OTP retrieval for authentication
- **Corporate vs Individual Detection**: Smart filtering based on business rules

## System Architecture

```
main.py → BrowserManager → [GoQ, Orange, Rakuraku] → Data Processing → Order Import
```

### Core Components

- **BrowserManager**: Manages browser instances and contexts
- **GoQ**: Handles order searching, customer data extraction, and status updates
- **Orange**: Manages product imports and catalog operations
- **Rakuraku**: Processes order data and generates documentation

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install playwright
   playwright install chromium
   ```
3. Configure credentials in `config.py`
4. Set up email access for OTP authentication

## Configuration

Update `config.py` with your platform credentials:

```python
# Platform URLs and login credentials
RKRK_URL = "your_rakuraku_url"
GOQ_URL = "your_goq_url"  
ORANGE_URL = "your_orange_url"

# Login credentials for each platform
RKRK_USER = "your_username"
RKRK_PASS = "your_password"
# ... (additional credentials)
```

## Usage

### Basic Operation

```python
python main.py
```

This will:
1. Initialize browser contexts for each platform
2. Log into all three systems
3. Process orders from Rakuraku
4. Search and update orders in GoQ
5. Import relevant data to Orange

### Individual Platform Usage

Each platform can be used independently:

```python
# GoQ operations
goq = GoQ(context, orange_instance)
goq.log_in()
goq.searching()

# Orange operations  
orange = Orange(context)
orange.log_in()
orange.start_import_single(product_code, file, description, customer_info)

# Rakuraku operations
rakuraku = Rakuraku(context)
rakuraku.log_in()
rakuraku.get_page_info()
```

## Data Flow

1. **Rakuraku**: Extracts order data → `table_data.json`
2. **GoQ**: Processes each product code:
   - Searches for order details
   - Extracts customer information
   - Updates order status and history
3. **Orange**: Imports processed data based on business rules

## Business Logic

### Corporate vs Individual Detection
- Uses keyword matching to identify corporate customers
- Applies different processing rules based on customer type
- Handles special cases for "法人・事業所限定" products

### Address Processing
- Smart address parsing for Japanese addresses
- Postal code formatting and validation
- Phone number standardization

## Error Handling

- Comprehensive error logging to `error/error_YYYYMMDD_HHMMSS.json`
- Timeout handling for web operations
- Automatic retry mechanisms
- Detailed error tracking per product code

## File Structure

```
AI Agents/
├── main.py                 # Main orchestration script
├── config.py              # Configuration and credentials
├── GoQ/
│   └── GoQ.py             # GoQ platform integration
├── Orange/
│   └── Orange.py          # Orange platform integration  
├── Rakuraku/
│   └── Rakuraku.py        # Rakuraku platform integration
├── utils.py               # Utility functions
├── var.py                 # Variable definitions
├── Downloads/             # Downloaded files storage
├── error/                 # Error logs
└── html_output/           # Debug HTML outputs
```

## Dependencies

- **playwright**: Web automation framework
- **poplib**: Email retrieval for OTP
- **json**: Data processing
- **re**: Text processing and validation

## Logging

The system maintains detailed logs for:
- Order processing status
- Error conditions and timeouts  
- Customer information extraction
- Platform-specific operations

## Security Notes

- Credentials are stored in `config.py` (keep secure)
- Email passwords for OTP retrieval
- Browser sessions are properly managed and closed

## Development

To extend functionality:
1. Add new platform integrations following existing patterns
2. Extend error handling in base classes
3. Add new business rules in respective platform modules
4. Update configuration as needed

## Troubleshooting

- Check `error/` directory for detailed error logs
- Verify credentials in `config.py`
- Ensure browser automation elements haven't changed
- Check network connectivity to all platforms

---

# Developer Documentation

## Code Flow and Architecture

### Execution Flow

```
1. main.py starts execution
2. BrowserManager initializes Chromium browser
3. Three separate browser contexts created (isolation)
4. Platform logins execute in parallel
5. Rakuraku data extraction → table_data.json
6. GoQ processes each product sequentially
7. Orange imports are triggered conditionally
8. Browser cleanup and shutdown
```

### Detailed Code Flow

#### 1. Main Entry Point (`main.py:44-78`)

```python
# Browser initialization
manager = BrowserManager()
manager.start()

# Create isolated contexts for each platform
context_goq = manager.new_context()
context_orange = manager.new_context() 
context_raku = manager.new_context()

# Platform instantiation with dependency injection
orange = Orange(context_orange)
goq = GoQ(context_goq, orange)  # GoQ gets Orange instance
rakuraku = Rakuraku(context_raku)
```

#### 2. Authentication Phase

**Rakuraku Login** (`Rakuraku.py:26-50`):
- Basic form authentication
- Iframe navigation to menu system
- Clicks トラスコ発注 menu item

**GoQ Login** (`GoQ.py:54-88`):
- Multi-step OAuth flow
- Handles GoQ account authentication popup
- Terms of service acceptance
- Popup window management with checkbox automation

**Orange Login** (`Orange.py:49-76`):
- Form authentication with company ID
- Email-based OTP retrieval
- Two-step confirmation process

#### 3. Data Extraction Phase (`Rakuraku.py:52-95`)

```python
def get_page_info(self):
    # Extract table data until "発注済" status found
    all_rows = {}
    BREAK_POINT = '発注済'
    
    for row in table_rows:
        if row.text == BREAK_POINT:
            break
        # Extract columns: 1,6,7,8,11,12,13
        row_data = extract_valuable_columns(row)
        all_rows[row_id] = row_data
    
    # Save to table_data.json
    save_json(all_rows)
```

#### 4. Order Processing Loop (`GoQ.py:168-276`)

```python
def searching(self):
    with open("table_data.json") as f:
        orders = json.load(f)
    
    for order_id, items in orders.items():
        product_code = extract_product_code(items)
        
        try:
            # Open new tab for order details
            with context.expect_page() as page_info:
                self.search_and_open_order_detail(product_code)
            new_tab = page_info.value
            
            # Extract customer information
            customer_info = self.process_detail_tab(new_tab, product_code)
            
            # Conditional Orange import
            if customer_info and should_import_to_orange():
                result = orange.start_import_single(...)
                self.import_result(new_tab, result)
            
        except Exception as e:
            self.log_error(product_code, "exception", str(e))
```

### Key Classes and Methods

#### BrowserManager (`main.py:20-42`)
- **Purpose**: Centralized browser lifecycle management
- **Methods**:
  - `start()`: Initializes Playwright and Chromium browser
  - `new_context()`: Creates isolated browser context
  - `stop()`: Cleanup browser resources

#### GoQ Class (`GoQ/GoQ.py`)

**Core Methods**:

1. **`log_in()`** (lines 54-88):
   - Handles complex OAuth flow
   - Manages popup windows with checkbox automation
   - Error handling for authentication edge cases

2. **`searching()`** (lines 168-276):
   - Main processing loop
   - Tab management for concurrent operations
   - Error logging per product code

3. **`process_detail_tab()`** (lines 310-425):
   - Customer data extraction using CSS selectors
   - Japanese address parsing logic
   - Corporate vs individual customer detection

4. **`import_result()`** (lines 426-558):
   - Updates order history in GoQ system
   - Status changes to "発注" (175)
   - Form submission with validation

#### Orange Class (`Orange/Orange.py`)

**Authentication Flow**:
1. Form login with company ID
2. Email OTP retrieval via POP3
3. Two-step confirmation process

**Key Features**:
- Email integration for OTP (`fetch_auth_code_from_email()`)
- Product import with business rule validation
- Error handling for discontinued products

#### Rakuraku Class (`Rakuraku/Rakuraku.py`)

**Data Extraction Process**:
1. Navigate to iframe-based interface
2. Extract table data with selective column filtering
3. Stop processing at "発注済" status
4. Generate structured JSON output

### Business Logic Implementation

#### Corporate Customer Detection (`GoQ.py:390-393`)

```python
# Logic: If name lacks corporate keywords but address has them
if not any(corp_key in name for corp_key in corp_keywords) and \
   any(corp_key in processed_address for corp_key in corp_keywords):
    name, incharge_name = processed_address, name  # Swap values
```

#### Address Processing (`GoQ.py:352-381`)

```python
for keyword in corp_keywords:
    if keyword in address:
        parts = address.split(keyword, 1)
        
        if keyword in after_keywords:
            # Get text AFTER keyword
            processed_address = (keyword + parts[-1]).strip()
        else:
            # Get text BEFORE keyword, after last number
            before_text = parts[0]
            last_number_pos = find_last_number_position(before_text)
            processed_address = before_text[last_number_pos:] + keyword
```

### Error Handling Strategy

#### Hierarchical Error Management

1. **Method-level**: Try-catch with specific error types
2. **Product-level**: Continue processing other products on error  
3. **System-level**: Comprehensive logging with timestamps
4. **Debugging**: HTML dumps saved on critical failures

```python
def log_error(self, product_code, error_status, error_message=""):
    error_data[product_code] = {
        "status": error_status,
        "message": error_message,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    # Save to timestamped error file
```

### Data Flow Patterns

#### JSON Data Structure

**table_data.json** format:
```json
{
  "row_id": [
    {"td_id": "value"},
    {"td_id": "value"}
  ]
}
```

**Customer Information** structure:
```json
{
  "name": "customer_name",
  "incharge_name": "contact_person", 
  "postal1": "123", "postal2": "4567",
  "phone1": "03", "phone2": "1234", "phone3": "5678",
  "address1": "first_20_chars",
  "address2": "next_20_chars", 
  "address3": "remaining_chars"
}
```

### Concurrency and Tab Management

#### Multi-tab Strategy (`GoQ.py:193-255`)

```python
# Save original tab reference
original_tab = self.page

# Watch for new tab creation
with context.expect_page() as page_info:
    self.search_and_open_order_detail(product_code)
new_tab = page_info.value

# Process in new tab
customer_info = self.process_detail_tab(new_tab, product_code)

# Cleanup and return to original
new_tab.close()
original_tab.bring_to_front()
self.page = original_tab
```

### Platform Integration Patterns

#### Dependency Injection
- GoQ receives Orange instance for cross-platform operations
- Enables conditional Orange imports based on GoQ data
- Maintains loose coupling between platform modules

#### Context Isolation
- Each platform operates in separate browser context
- Prevents cookie/session interference
- Enables parallel authentication

### Development Patterns

#### Configuration Management
- Centralized credential storage in `config.py`
- Environment-specific URLs and timeouts
- Email configuration for OTP automation

#### Debugging Support
- HTML output capture in `html_output/` directory
- Screenshot generation for visual debugging
- Detailed console logging with status indicators

#### Extensibility Points
1. **New Platform Integration**: Follow existing class patterns
2. **Business Rule Changes**: Modify keyword arrays in `var.py`
3. **Data Processing**: Extend JSON transformation methods
4. **Error Handling**: Add new error types to logging system

## Detailed Technical Implementation

### Email OTP System (`Orange.py:78-132`)

The Orange platform requires email-based two-factor authentication:

```python
def fetch_auth_code_from_email(self):
    # Connect to POP3 server
    mailbox = poplib.POP3_SSL(pop_server)
    mailbox.user(email_user)
    mailbox.pass_(email_pass)
    
    # Check last 10 messages for OTP
    for i in range(num_messages, max(0, num_messages - 10), -1):
        resp, lines, octets = mailbox.retr(i)
        raw_email = b'\r\n'.join(lines)
        msg = BytesParser().parsebytes(raw_email)
        
        # Filter by sender
        sender = msg.get("Resent-From") or msg.get("From") or ""
        if "info-f@first23.com" not in sender:
            continue
            
        # Extract OTP using regex
        otp_match = re.search(r"認証コード\s*([0-9]{6})", body)
        if otp_match:
            return otp_match.group(1)
```

### Data Processing Pipeline

#### JSON Data Transformation (`Rakuraku.py:96-138`)

Raw table data is transformed into structured format:

```python
def refactor_json(self):
    for outer_key, records in data.items():
        updated_list = []
        for i, item in enumerate(records):
            value = list(item.values())[0]
            if i == 1:  # Order number
                updated_list.append({"order_number": value})
            elif i == 4:  # Product code processing
                updated_list.append({"product_code": value})
                # Extract meaningful part from "20250901-0218519373"
                parts = [p.strip() for p in value.split('-') if p.strip()]
                if len(parts) >= 3:  
                    updated_list[-1]["product_code"] = "-".join(parts[1:])
            elif i == 5:  # Download code
                updated_list.append({"download_code": value})
            elif i == 6:  # Description
                updated_list.append({"description": value})
```

**Example Data Structure Evolution**:

Raw extraction:
```json
{
  "recordTr_242968_0": [
    {"recordAct_242968": ""},
    {"record_td_0_0_99-137224": "1177794"},
    {"record_td_0_0_99-137226": "20250901-0218519373"}
  ]
}
```

After refactoring:
```json
{
  "recordTr_242968_0": [
    {"order_number": "1177794"},
    {"product_code": "0218519373"},
    {"description": "■アストロプロダクツ AP 4連バキュームゲージ..."}
  ]
}
```

### Advanced Address Processing Algorithm

#### Corporate Keyword Detection (`var.py:1-28`)

The system uses comprehensive Japanese corporate entity detection:

```python
corp_keywords = [
    # Traditional companies
    "株式会社", "有限会社", "合同会社", "合名会社", "合資会社",
    "(株)", "(有)", "(同)",
    # Foundations & associations  
    "一般社団法人", "一般財団法人", "公益社団法人", "公益財団法人",
    # Medical & educational
    "医療法人", "宗教法人", "社会福祉法人", "学校法人",
    # Government & special entities
    "独立行政法人", "地方独立行政法人", "国立大学法人"
]

# Keywords requiring text AFTER them (e.g., "株式会社 ABC商事")
after_keywords = ["(株)", "(有)", "(同)", "(医)", ...]
```

#### Address Parsing Logic (`GoQ.py:352-381`)

Complex Japanese address processing with corporate entity handling:

```python
for keyword in corp_keywords:
    if keyword in address:
        parts = address.split(keyword, 1)
        
        if keyword in after_keywords:
            # Get company name AFTER abbreviation
            # "(株)ABC商事" → "ABC商事"
            processed_address = (keyword + parts[-1]).strip()
        else:
            # Get company name BEFORE full form, after last address number
            # "東京都港区1-2-3 ABC株式会社" → "ABC株式会社"
            before_text = parts[0]
            number_matches = list(re.finditer(r'[\d０-９]', before_text))
            if number_matches:
                last_number_end = number_matches[-1].end()
                processed_address = (before_text[last_number_end:] + keyword).strip()
```

### File Download Management (`Rakuraku.py:202-252`)

Automated file download with error handling:

```python
def start_download(self, download_dir="Downloads"):
    # Create download directory
    os.makedirs(download_dir, exist_ok=True)
    
    # Process each row
    for row_id, cells in data.items():
        row = self.main_frame.query_selector(f'tr#{row_id}')
        tds = row.query_selector_all('td')
        
        # Column 8 contains download link
        td = tds[8]
        link = td.query_selector('a')
        
        # Handle download with Playwright
        with self.page.expect_download() as download_info:
            link.click()
        download = download_info.value
        
        # Save with original filename
        save_path = os.path.join(download_dir, download.suggested_filename)
        download.save_as(save_path)
        
        # Update JSON with file path
        data[row_id].append({"downloaded_file": save_path})
```

### Orange Import Process (`Orange.py:150-299`)

Complex multi-step import workflow:

#### 1. File Upload & Product Validation
```python
# Unhide file input for automation
self.page.eval_on_selector('input#fileInput', 'el => el.removeAttribute("hidden")')

# Upload Excel file
self.page.set_input_files('input#fileInput', downloaded_file)

# Validate product code
value_field = f'input#detailData1List\\:{row_idx}\\:articleNameFixed'
warning_field = 'p.p-warning--type-02.u-font14'

# Check for discontinuation warnings
if self.page.is_visible(warning_field, timeout=self.timeout):
    warning_text = warning_el.text_content().strip()
    if warning_text in self.warning_mess:
        return {"error": "Product discontinued"}
```

#### 2. Customer Information Input
```python
# Name validation (20 character limit)
def _cap20(self, text):
    return text[:20] if text else ""

# Fill customer fields with validation
self._fill_if_exists('#directName1', self._cap20(name), "Name")
self._fill_if_exists('#directName3', self._cap20(incharge_name), "Incharge")

# Address processing (split into 20-char segments)
address1 = full_addr[:20]
address2 = full_addr[20:40] if len(full_addr) > 20 else ""
address3 = full_addr[40:60] if len(full_addr) > 40 else ""
```

### Error Handling Architecture

#### Multi-Level Error Logging (`GoQ.py:34-53`)

```python
def log_error(self, product_code, error_status, error_message=""):
    # Load existing errors or create new file
    if os.path.exists(self.error_file):
        with open(self.error_file, "r", encoding="utf-8") as f:
            error_data = json.load(f)
    else:
        error_data = {}
    
    # Add timestamped error entry
    error_data[product_code] = {
        "status": error_status,           # timeout, exception, skip
        "message": error_message,         # detailed error description
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Save to timestamped file: error/error_YYYYMMDD_HHMMSS.json
    with open(self.error_file, "w", encoding="utf-8") as f:
        json.dump(error_data, f, ensure_ascii=False, indent=2)
```

#### Business Rule Validation (`GoQ.py:221-240`)

Special handling for restricted products:

```python
# Skip corporate-only products for individual customers
if "法人・事業所限定" in description and "送料別途見積り" not in description:
    # Check if customer name/address contains corporate keywords
    target_text = f"{customer_info.get('name', '')} {customer_info.get('address', '')}"
    is_corporate = any(kw in target_text for kw in corp_keywords)
    
    if not is_corporate:
        msg = "法人・事業所限定ですが宛先に法人名が見つかりません。自動skip"
        self.log_error(product_code, "skip", msg)
        skip_import = True
```

### Popup Management System (`GoQ.py:89-158`)

Automated handling of dynamic popups:

```python
def close_all_popups(self, timeout=5000, max_popups=5):
    popup_selector = "#manage_pop_up_window"
    checkbox_selector = f"{popup_selector} input[type='checkbox']"
    
    for i in range(max_popups):  # Handle up to 5 popups
        try:
            # Wait for popup visibility
            popup = self.page.locator(popup_selector)
            if not popup.is_visible(timeout=timeout):
                break
                
            # Auto-check all unchecked checkboxes
            checkboxes = self.page.locator(checkbox_selector)
            for j in range(checkboxes.count()):
                cb = checkboxes.nth(j)
                if not cb.is_checked():
                    cb.click()
            
            # Wait for close button to be enabled
            self.page.wait_for_function("""
                () => {
                    const btn = document.querySelector("#manage_puw_close");
                    return btn && !btn.classList.contains("disabled");
                }
            """, timeout=timeout)
            
            # Click close and wait for disappearance
            close_btn = self.page.locator("#manage_puw_close")
            close_btn.click()
            self.page.wait_for_selector(popup_selector, state="hidden")
            
        except Exception as e:
            print(f"[Error] Failed popup #{i + 1}: {e}")
            break
```

### Data Validation & Processing

#### Customer Information Structure
```json
{
  "name": "臼井工務店臼井誠",          // Company + person name
  "incharge_name": "",               // Contact person (if separated)
  "postal1": "571",                  // First 3 digits of postal code
  "postal2": "0012",                 // Last 4 digits of postal code  
  "phone1": "090",                   // Area code
  "phone2": "3165",                  // Middle digits
  "phone3": "0045",                  // Last 4 digits
  "address1": "大阪府門真市江端町16ー14", // First 20 chars of address
  "address2": "",                    // Next 20 chars (if needed)
  "address3": ""                     // Remaining chars (if needed)
}
```

#### Phone Number Processing (`GoQ.py:340-344`)
```python
phone_raw = receiver_text[3].replace("TEL：", "").replace("-", "").strip()
phone1 = phone_raw[:3]      # "090"
phone3 = phone_raw[-4:]     # "0045" 
phone2 = phone_raw[3:-4]    # "3165"
```

### Browser Context Management

#### Isolation Strategy (`main.py:48-56`)
```python
# Create separate contexts to prevent cross-contamination
context_goq = manager.new_context()      # GoQ operations
context_orange = manager.new_context()   # Orange operations  
context_raku = manager.new_context()     # Rakuraku operations

# Dependency injection for cross-platform operations
orange = Orange(context_orange)
goq = GoQ(context_goq, orange)  # GoQ can trigger Orange imports
```

#### Tab Management Pattern (`GoQ.py:193-255`)
```python
# Save current tab state
original_tab = self.page

try:
    # Watch for new tab creation
    with context.expect_page() as page_info:
        self.search_and_open_order_detail(product_code)
    new_tab = page_info.value
    
    # Work in isolated tab
    customer_info = self.process_detail_tab(new_tab, product_code)
    
    # Conditional cross-platform operation
    if customer_info and self.orange:
        result = self.orange.start_import_single(...)
        self.import_result(new_tab, result)
    
finally:
    # Always cleanup and restore state
    new_tab.close()
    original_tab.bring_to_front()
    self.page = original_tab
```

### Performance & Reliability Features

#### Timeout Management
- **Login operations**: 10 seconds
- **Page loads**: Network idle detection
- **Element searches**: 10 seconds with fallbacks
- **File operations**: No timeout (system dependent)

#### Error Recovery Strategies
1. **Connection failures**: Retry with exponential backoff
2. **Element not found**: CSS selector fallbacks
3. **Authentication issues**: Session state preservation
4. **File download failures**: Path validation and retry

#### Debug & Monitoring
- **HTML dumps**: Saved to `html_output/` for troubleshooting
- **Screenshots**: Captured at key workflow points
- **Console logging**: Timestamped with operation context
- **JSON persistence**: All intermediate states saved