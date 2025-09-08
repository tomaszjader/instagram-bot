# Instagram Auto Publisher

An automated Instagram posting system that publishes content based on a schedule stored in Google Sheets. The application uses Google API (without Service Account) and includes Telegram notifications for monitoring.

## Features

- 📅 **Automated Scheduling**: Posts are scheduled via Google Sheets
- 📸 **Instagram Integration**: Automatic posting to Instagram using instagrapi
- 📊 **Google Sheets Integration**: Schedule management through Google Sheets API
- 📱 **Telegram Notifications**: Real-time notifications about posting status
- 🖼️ **Image Processing**: Built-in image utilities for post preparation
- 🧪 **Testing Suite**: Comprehensive testing for all components
- 📝 **Logging**: Detailed logging with colored output

## Prerequisites

- Python 3.7+
- Instagram account
- Google Sheets API access
- Telegram Bot (optional, for notifications)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd pythonProject57
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root with the following variables:
   ```env
   INSTA_USERNAME=your_instagram_username
   INSTA_PASSWORD=your_instagram_password
   GOOGLE_SHEET_ID=your_google_sheet_id
   GOOGLE_API_KEY=your_google_api_key
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_telegram_chat_id
   ```

## Configuration

### Google Sheets Setup

1. Create a Google Sheet with your posting schedule
2. Get your Google Sheets API key from Google Cloud Console
3. Share your sheet with the API or make it publicly readable
4. Copy the Sheet ID from the URL

### Telegram Setup (Optional)

1. Create a Telegram bot via @BotFather
2. Get your bot token
3. Get your chat ID (you can use @userinfobot)

## Usage

### Run the Scheduler
```bash
python main.py
```

### Test Publication
```bash
python main.py test
```

### Test Date Parsing
```bash
python main.py dates
```

## Project Structure

```
├── main.py              # Main entry point
├── scheduler.py         # Scheduling logic
├── instagram.py         # Instagram API integration
├── google_sheets.py     # Google Sheets API integration
├── telegram_bot.py      # Telegram notifications
├── image_utils.py       # Image processing utilities
├── config.py           # Configuration and environment variables
├── test_functions.py   # Testing utilities
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Dependencies

### Core Dependencies
- `instagrapi==2.0.0` - Instagram API client
- `requests==2.31.0` - HTTP requests
- `python-dotenv==1.0.0` - Environment variable management
- `Pillow==10.0.0` - Image processing

### Google Sheets Integration
- `google-api-python-client==2.108.0`
- `google-auth==2.23.4`
- `google-auth-oauthlib==1.1.0`
- `google-auth-httplib2==0.1.1`

### Development Tools
- `pytest==7.4.3` - Testing framework
- `black==23.9.1` - Code formatting
- `flake8==6.1.0` - Code linting
- `coloredlogs==15.0.1` - Enhanced logging

## Error Handling

The application includes comprehensive error handling and logging:
- All critical errors are logged with detailed information
- Telegram notifications for posting status
- Graceful handling of API rate limits
- Configuration validation on startup

## Security Notes

- Never commit your `.env` file to version control
- Use strong passwords for your Instagram account
- Consider using Instagram's official API when available
- Regularly rotate your API keys and tokens

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Format code: `black .`
6. Check linting: `flake8`
7. Submit a pull request

## License

This project is for educational purposes. Please ensure compliance with Instagram's Terms of Service and API usage policies.

## Troubleshooting

### Common Issues

1. **Instagram Login Issues**:
   - Check username/password
   - Instagram may require 2FA or manual verification
   - Consider using app-specific passwords

2. **Google Sheets Access**:
   - Verify API key permissions
   - Check sheet sharing settings
   - Ensure correct Sheet ID

3. **Telegram Notifications**:
   - Verify bot token
   - Check chat ID format
   - Ensure bot has permission to send messages

## Support

For issues and questions, please check the logs first. The application provides detailed logging to help diagnose problems.