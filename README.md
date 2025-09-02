# AI Agents - Automated Order Processing System

A Python-based automation system that integrates with three platforms (Rakuraku, GoQ, and Orange) to streamline order processing and management workflows.

## Overview

This system automates the order processing pipeline by:

1. **Rakuraku** - Fetching order data and generating quotes/orders from Rakuraku
2. **GoQ** - Processing order details and customer information from GoQ
3. **Orange** - Importing orders and handling product catalog operations from Orange

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
