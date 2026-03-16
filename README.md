# 🔀 Hybrid Strangle

A Python-based automated options trading system that executes a **Hybrid Strangle strategy** on Indian indices (NIFTY, BANKNIFTY, etc.) using the [Shoonya (Finvasia) API](https://github.com/Shoonya-Dev/ShoonyaApi-py). The system creates, manages, and monitors option baskets, with full trade logging, notifications, and a distributable GUI.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Strategy](#strategy)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Google Sheets Service Account Setup](#google-sheets-service-account-setup)
- [Usage](#usage)
- [Running the Basket Creator GUI](#running-the-basket-creator-gui)
- [Distribution Build](#distribution-build)
- [Modules Reference](#modules-reference)
- [Disclaimer](#disclaimer)

---

## Overview

**Hybrid Strangle** automates the lifecycle of an options strangle on Indian derivatives markets. It connects to the Shoonya brokerage API, selects appropriate strikes, places call and put option orders as a basket, monitors positions in real time, and logs all activity. Notifications can be sent to keep traders informed of key events without needing to watch a terminal.

---

## Strategy

A **strangle** involves simultaneously selling (or buying) an Out-of-the-Money (OTM) Call and an OTM Put on the same underlying index and expiry. The "Hybrid" variant combines elements of both short and long strangles, potentially adjusting legs based on market conditions, premiums, or predefined rules.

Key characteristics:
- **Underlying:** NIFTY, BANKNIFTY, or other supported NSE/NFO indices
- **Instrument type:** Options (CE and PE legs)
- **Order type:** Basket orders (both legs placed atomically)
- **Strike selection:** Configurable OTM offset from ATM
- **Risk management:** Stop-loss and target logic managed by `strategy.py`

---

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                    basket_creator.py                   │
│              (GUI Entry Point / Orchestrator)          │
└────────────┬──────────────────────────┬───────────────┘
             │                          │
     ┌───────▼──────┐          ┌────────▼────────┐
     │  config.py   │          │  shoonya_api.py  │
     │ config_mgr   │          │  (Broker Layer)  │
     └──────────────┘          └────────┬────────┘
                                        │
          ┌─────────────────────────────┼──────────────────┐
          │                             │                  │
  ┌───────▼──────┐           ┌──────────▼──────┐  ┌───────▼──────┐
  │  strategy.py │           │  basket_mgr.py  │  │   models.py  │
  │ (Trade Logic)│           │ (Basket CRUD)   │  │(Data Schemas)│
  └───────┬──────┘           └──────────┬──────┘  └──────────────┘
          │                             │
  ┌───────▼──────┐           ┌──────────▼──────┐
  │trade_logger  │           │  file_manager   │
  │    .py       │           │      .py        │
  └───────┬──────┘           └─────────────────┘
          │
  ┌───────▼──────────┐
  │  notification.py │
  │  (Alerts/Notifs) │
  └──────────────────┘
```

---

## Project Structure

```
Hybrid_Strangle/
│
├── basket_creator.py          # Main GUI application / entry point
├── basket_manager.py          # Create, read, update, delete baskets
├── basket_schema.xsd          # XML schema for basket validation
├── config.py                  # Static configuration constants
├── config_manager.py          # Dynamic config loading and management
├── file_manager.py            # File I/O for basket persistence
├── models.py                  # Data models / dataclasses for orders/baskets
├── notification.py            # Notification dispatch (email/push/etc.)
├── shoonya_api.py             # Shoonya API wrapper (login, orders, quotes)
├── strategy.py                # Core strategy logic (strike selection, SL/TP)
├── trade_logger.py            # Trade and event logging
│
├── basket_schema.xsd          # XSD schema for XML basket validation
├── BasketCreator.spec         # PyInstaller spec for building executable
├── requirements.txt           # Python dependencies
│
├── service_account.json           # (gitignored) Your GCP service account key
├── service_account_template.json  # Template for service account credentials
├── service_account_setup.md       # Step-by-step GCP setup guide
│
├── baskets/                   # Saved basket XML files
├── build/BasketCreator/       # PyInstaller build artifacts
├── dist/                      # Distributable executable output
└── BasketCreator_Distribution/ # Packaged distribution folder
```

---

## Prerequisites

- **Python 3.9+**
- **Shoonya (Finvasia) trading account** with API access enabled
  - Obtain your API key from [Shoonya API settings](https://prism.shoonya.com/api)
- **Google Cloud Platform account** (for Google Sheets integration, if used)
- **pip** for package management
- **PyInstaller** (only if building the distributable)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/ShreyaThakur05/Hybrid_Strangle.git
cd Hybrid_Strangle
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration

### Shoonya API credentials

Edit `config.py` or `config_manager.py` and supply your Shoonya credentials:

```python
USER_ID    = "your_user_id"
PASSWORD   = "your_password"
VENDOR_CODE = "your_vendor_code_U"   # typically UserID + _U
API_KEY    = "your_api_key"
IMEI       = "your_imei_or_random_string"
TOTP_SECRET = "your_totp_secret"     # from Shoonya app during TOTP setup
```

> ⚠️ **Never commit real credentials to version control.**  
> Consider using environment variables or a separate `creds.yml` file that is listed in `.gitignore`.

### Strategy parameters

Key parameters to tune in `config.py`:

| Parameter | Description | Example |
|---|---|---|
| `INDEX` | Underlying index | `"NIFTY"` / `"BANKNIFTY"` |
| `QUANTITY` | Lot size | `50` |
| `OTM_OFFSET` | Strike offset from ATM | `100` |
| `STOP_LOSS_PCT` | Stop-loss % per leg | `75` |
| `TARGET_PCT` | Target profit % of premium | `35` |
| `EXPIRY` | Options expiry date | `"28NOV24"` |

---

## Google Sheets Service Account Setup

This project optionally logs trades to a Google Sheet. Follow the steps in [`service_account_setup.md`](service_account_setup.md) for a full walkthrough, or use the summary below:

1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create a new project.
2. Enable the **Google Sheets API** and **Google Drive API**.
3. Create a **Service Account** and download the JSON key.
4. Rename the downloaded key to `service_account.json` and place it in the project root.
5. Share your Google Sheet with the service account's email address (with Editor access).
6. Update the Sheet ID in `config.py`.

> Use `service_account_template.json` as a reference for the expected key structure.

---

## Usage

### Run the main application

```bash
python basket_creator.py
```

This launches the Basket Creator GUI where you can:
- Configure and preview option baskets
- Execute strangle orders via the Shoonya API
- Monitor active positions
- View trade logs

### Run strategy directly (headless)

If you prefer headless/script-based execution:

```bash
python strategy.py
```

---

## Running the Basket Creator GUI

The GUI provides a visual interface to:

- **Create Baskets** — select index, expiry, strike, quantity, and product type
- **Manage Baskets** — list, edit, delete saved baskets from the `baskets/` folder
- **Place Orders** — submit the basket as a set of buy/sell orders to Shoonya
- **View Logs** — inspect trade logs generated by `trade_logger.py`

Baskets are persisted as XML files (validated against `basket_schema.xsd`) in the `baskets/` directory.

---

## Distribution Build

A standalone executable is provided in `BasketCreator_Distribution/` (or can be rebuilt using PyInstaller):

```bash
# Install PyInstaller if not already installed
pip install pyinstaller

# Build using the spec file
pyinstaller BasketCreator.spec
```

The output executable will be generated in the `dist/` folder. The `BasketCreator_Distribution/` folder contains the packaged version ready for sharing with users who don't have Python installed.

---

## Modules Reference

| File | Responsibility |
|---|---|
| `basket_creator.py` | GUI entry point; orchestrates all components |
| `basket_manager.py` | CRUD operations on basket objects |
| `basket_schema.xsd` | XSD schema for validating basket XML files |
| `config.py` | Static constants (API creds, strategy params) |
| `config_manager.py` | Dynamic config loading, environment overrides |
| `file_manager.py` | Reading/writing basket XML files to disk |
| `models.py` | Dataclasses/models for Order, Basket, Position |
| `notification.py` | Sends alerts (trade fills, SL hits, targets) |
| `shoonya_api.py` | Shoonya API integration: login, place/cancel orders, fetch quotes |
| `strategy.py` | Strike selection, SL/TP logic, position monitoring |
| `trade_logger.py` | Structured logging of all trade events |

---

## Author

**Shreya Thakur** — [@ShreyaThakur05](https://github.com/ShreyaThakur05)
