# Google Sheets Service Account Setup

## Steps to Enable Google Sheets Integration:

1. **Create Google Cloud Project**:
   - Go to https://console.cloud.google.com/
   - Create new project or select existing one

2. **Enable APIs**:
   - Enable Google Sheets API
   - Enable Google Drive API

3. **Create Service Account**:
   - Go to IAM & Admin > Service Accounts
   - Create new service account
   - Download JSON key file
   - Rename to `service_account.json` and place in project root

4. **Share Spreadsheet**:
   - Create Google Sheet named "Trading_Log"
   - Share with service account email (from JSON file)
   - Give Editor permissions

5. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## File Structure:
```
strategy2/
├── service_account.json  # Google service account credentials
├── trade_logger.py       # Google Sheets integration
├── requirements.txt      # Dependencies
└── ...
```