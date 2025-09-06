# Instagram Auto Publisher 📸

Automatic Instagram post publishing system based on Google Sheets schedule.

## 🚀 Features

- ⏰ Automatic post publishing according to schedule
- 📊 Google Sheets integration as data source
- 🖼️ Automatic image processing (Instagram proportions)
- 📱 Telegram notifications about publishing status
- 🔄 Support for various date formats
- 🌐 Image downloading from URLs (including Google Drive)

## 📋 Requirements

- Python 3.8+
- Instagram account
- Google Sheets API Key
- Telegram Bot (optional)

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd pythonProject57
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create .env file with configuration:**
   ```env
   INSTA_USERNAME=your_username
   INSTA_PASSWORD=your_password
   GOOGLE_SHEET_ID=google_sheet_id
   GOOGLE_API_KEY=your_google_api_key
   TELEGRAM_BOT_TOKEN=telegram_bot_token
   TELEGRAM_CHAT_ID=telegram_chat_id
   
   # Optional - logging configuration
   LOG_LEVEL=INFO
   LOG_FORMAT=TEXT
   ```

## 📊 Google Sheets Configuration

The sheet should contain columns:
- **data_publikacji** - publication date (DD.MM.YYYY or other supported formats)
- **tresc_postu** - post content
- **tagi** - hashtags (optional)
- **sciezka_zdjecia** - URL or path to image
- **czy_opublikowano** - publication status (TRUE/FALSE)

## 📝 Logging Configuration

The system supports configurable logging level and structured logging in JSON format:

### Logging Levels
- **DEBUG** - detailed diagnostic information
- **INFO** - general operational information (default)
- **WARNING** - warnings
- **ERROR** - errors
- **CRITICAL** - critical errors

### Logging Formats
- **TEXT** - standard text format (default)
- **JSON** - structured logging in JSON format

### Configuration Examples
```bash
# Standard logging
LOG_LEVEL=INFO
LOG_FORMAT=TEXT

# Structured logging for monitoring systems
LOG_LEVEL=DEBUG
LOG_FORMAT=JSON
```

### Testing Logging
```bash
python test_logging.py
```

## 🔒 Security

The application includes advanced security mechanisms protecting against abuse and errors.

### Input Data Validation
- **Instagram usernames**: Length check (1-30 characters) and allowed characters
- **Post content**: 2200 character limit, forbidden words detection
- **Hashtags**: Maximum 30 hashtags, format validation
- **Image URLs**: HTTPS protocol and file extensions check

### Rate Limiting
- **Instagram API**: 20 calls/min, 500/hour, burst limit 5
- **Google Sheets API**: 60 calls/min, 3000/hour, burst limit 10
- **Automatic cooldown**: After exceeding limits (5-10 minutes)
- **Intelligent waiting**: Automatic delays when approaching limits

### Security Monitoring
- **Suspicious activity detection**: Automatic logging of unusual behavior
- **API call statistics**: Usage and blocking tracking
- **Structured logging**: All security events in JSON format

### Security Testing
To test security features:
```bash
python test_security.py
```

## 📊 Monitoring and Health Check

The application includes an advanced monitoring system:

### Health Check Server
- **Port**: 8080 (configurable via HEALTH_CHECK_PORT)
- **Automatic startup**: server starts in background with application
- **HTTP Endpoints**: available for external monitoring systems

### Available Endpoints

#### /health - Health Status
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "2025-01-17T23:26:34.123456",
  "uptime_seconds": 3600.5,
  "version": "1.0.0"
}
```

#### /metrics - Application Metrics
```json
{
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "memory_used_mb": 512.3,
    "memory_available_mb": 1024.7,
    "disk_usage_percent": 67.4,
    "disk_free_gb": 25.8
  },
  "application": {
    "posts_published_total": 150,
    "posts_failed_total": 3,
    "posts_published_last_24h": 12,
    "posts_failed_last_24h": 0,
    "last_successful_post": "2025-01-17T22:30:15.123456",
    "last_failed_post": null,
    "scheduler_status": "running",
    "api_calls_instagram": 200,
    "api_calls_google_sheets": 50,
    "api_calls_blocked": 5
  },
  "timestamp": "2025-01-17T23:26:34.123456"
}
```

#### /metrics/prometheus - Prometheus Metrics
Format compatible with Prometheus for monitoring system integration:
```
# HELP instagram_scheduler_posts_published_total Total number of published posts
# TYPE instagram_scheduler_posts_published_total counter
instagram_scheduler_posts_published_total 150

# HELP instagram_scheduler_cpu_percent CPU usage percentage
# TYPE instagram_scheduler_cpu_percent gauge
instagram_scheduler_cpu_percent 15.2
```

#### /status - Full Status
Combines information from /health and /metrics in one endpoint.

### Automatic Metrics Collection
- **Post publishing**: automatic registration of successful and failed publications
- **API calls**: tracking all Instagram and Google Sheets API calls
- **Scheduler status**: application state monitoring (running, stopped, error)
- **System metrics**: CPU, memory, disk in real-time

### Health Criteria
The application automatically determines its status based on:
- **CPU > 90%**: degraded/unhealthy
- **Memory > 90%**: degraded/unhealthy
- **Disk > 95%**: degraded/unhealthy
- **Scheduler not running**: degraded/unhealthy
- **Error rate > 50%**: degraded/unhealthy

### Integration with Monitoring Systems
- **Prometheus**: /metrics/prometheus endpoint
- **Grafana**: metrics visualization
- **Alerting**: based on health check status
- **Load balancers**: health check for high availability

### Monitoring Testing
```bash
python test_monitoring.py
```

### Usage Examples
```bash
# Check health status
curl http://localhost:8080/health

# Get metrics
curl http://localhost:8080/metrics

# Metrics for Prometheus
curl http://localhost:8080/metrics/prometheus
```

## 🎯 Usage

### Running the scheduler
```bash
python src/core/main.py
```

### Test publishing
```bash
python src/core/main.py test
```

### Test date parsing
```bash
python src/core/main.py dates
```

### Test data loading
```bash
python src/core/main.py data
```

### One-time publishing
```bash
python src/core/main.py once
```

### Scheduler status
```bash
python src/core/main.py status
```

### Help
```bash
python src/core/main.py --help
```

## 📁 Project Structure

```
├── .gitignore              # Files ignored by Git
├── README.md               # Project documentation
├── requirements.txt        # Project dependencies
├── requirements-test.txt   # Test dependencies
├── src/                    # Application source code
│   ├── __init__.py
│   ├── config/             # Configuration
│   │   ├── __init__.py
│   │   └── config.py       # Environment variables and configuration
│   ├── core/               # Main components
│   │   ├── __init__.py
│   │   └── main.py         # Application entry point
│   ├── models/             # Data models
│   │   ├── __init__.py
│   │   └── models.py       # Post, ColumnMapper
│   ├── services/           # Business logic
│   │   ├── __init__.py
│   │   ├── services.py     # DataService, ImageService, etc.
│   │   ├── scheduler.py    # Scheduler, TestScheduler
│   │   └── monitoring.py   # Health check, metrics
│   ├── integrations/       # External integrations
│   │   ├── __init__.py
│   │   ├── instagram.py    # Instagram API
│   │   ├── google_sheets.py # Google Sheets API
│   │   └── telegram_bot.py # Telegram notifications
│   └── utils/              # Helper utilities
│       ├── __init__.py
│       ├── utils.py        # Retry, rate limiting
│       ├── security.py     # Validation, security
│       └── image_utils.py  # Image processing
└── tests/                  # Unit tests
    ├── test_models.py
    ├── test_services.py
    ├── test_google_sheets.py
    ├── test_security.py
    ├── test_monitoring.py
    ├── test_logging.py
    └── test_graceful_shutdown.py
```

## 🏗️ Architecture

The project has been refactored from a monolithic structure to a modular architecture with separation of responsibilities:

### 📦 Modules
- **src/config/** - Environment and logging configuration management
- **src/models/** - Data models (Post, ColumnMapper)
- **src/services/** - Business logic (DataService, ImageService, NotificationService, PublisherService, Scheduler, Monitoring)
- **src/integrations/** - External integrations (Instagram, Google Sheets, Telegram)
- **src/utils/** - Helper utilities (retry, rate limiting, security, image processing)
- **src/core/** - Main application entry point
- **tests/** - Comprehensive unit tests

### 🎯 Architecture Principles
- **Single Responsibility Principle** - each module has one responsibility
- **Dependency Injection** - loose coupling between components
- **Separation of Concerns** - clear separation of layers
- **Testability** - each component is independently testable

### Refactoring Benefits:
- ✅ Modular structure with clear separation of responsibilities
- ✅ Easier testing and debugging
- ✅ Better scalability and extensibility
- ✅ Cleaner and more maintainable code
- ✅ Compliance with Python best practices
- ✅ Preparation for future application development

## ⚙️ API Configuration

### Google Sheets API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Sheets API
4. Create an API key and add it to .env

### Telegram Bot (optional)
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot with the /newbot command
3. Copy the token and add it to .env
4. Find your Chat ID and add it to .env

## 🕐 Schedule

By default, the system checks for posts to publish daily at **4:00 PM**. This can be changed in the scheduler.py file in the run() method of the Scheduler class:

```python
target_time = dt_time(16, 0)  # Change to your desired time
```

## 🖼️ Supported Image Formats

- JPG, JPEG, PNG, WEBP
- Automatic proportion adjustment for Instagram requirements
- URL support (including Google Drive)
- Local files from images/ folder

## 📝 Supported Date Formats

- DD.MM.YYYY (e.g., 08.08.2025)
- DD/MM/YYYY (e.g., 08/08/2025)
- YYYY-MM-DD (e.g., 2025-08-08)
- DD-MM-YYYY (e.g., 08-08-2025)
- Numbers (serial date number from Excel/Google Sheets)

## 🚨 Security Notes

- **Never commit the .env file** to the repository
- Use strong passwords for Instagram account
- Regularly change API keys
- Monitor Instagram account activity

## 🐛 Troubleshooting

### Instagram Login Errors
- Check login credentials correctness
- Instagram may require two-factor authentication
- Avoid too frequent logins (may lead to blocking)

### Google Sheets API Errors
- Check if the sheet is public or shared
- Verify the Google Sheet ID correctness in .env file
- Make sure the API Key has appropriate permissions
- Check if columns in the sheet have correct names

### Image Issues
- Check if URL is publicly accessible
- Make sure the image format is supported
- Check if images/ folder exists for local files

## 📄 License

This project is released under the MIT License.

## 🤝 Support

In case of issues:
1. Check logs in console
2. Test components separately (python main.py test)
3. Check configuration in .env file

---

**⚠️ Disclaimer:** Use this tool in accordance with Instagram's terms of service. The author is not responsible for any potential account blocks.
