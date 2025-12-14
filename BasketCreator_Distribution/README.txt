SHOONYA BASKET CREATOR - EXECUTABLE DISTRIBUTION
===============================================

FILES INCLUDED:
- BasketCreator.exe     - Main executable program
- spot_value.txt        - Edit this file to change spot price
- basket_schema.xsd     - XML validation schema
- baskets/              - Output folder for basket files

HOW TO USE:
1. Double-click BasketCreator.exe to run the program
2. The program will wait until 9:20 AM to start trading
3. Edit spot_value.txt to simulate price changes
4. Check baskets/ folder for generated basket files
5. Check your email for basket notifications

FEATURES:
- Automatic 6-leg strangle basket creation
- Email notifications when baskets are created
- 1% loss limit with automatic force exit
- Daily session: 9:20 AM - 2:00 PM
- Maximum 2 adjustments per day
- XML and JSON basket file generation

CONFIGURATION:
All settings are built into the executable:
- Trading hours: 9:20 AM - 2:00 PM
- Max loss: 1%
- Max adjustments: 2
- Email: shreyathakurindia@gmail.com

REQUIREMENTS:
- Windows 10/11
- Internet connection for Shoonya API and email
- No Python installation required

SUPPORT:
This is a standalone executable with all dependencies included.