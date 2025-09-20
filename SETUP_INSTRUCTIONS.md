# 🎯 Bwin Bet Monitor - Complete Setup & Usage Guide

## 📋 Overview

This enhanced betting monitor provides automated tracking of bets on bwin.com with proxy protection, Telegram notifications, and multiple security features.

## ✨ Key Improvements in This Version

### 🔒 Security Enhancements
- **Enhanced Proxy Authentication**: Improved Chrome extension for reliable proxy authentication
- **Multiple Kill Switches**: Automatic termination on proxy/login/navigation failures
- **IP Verification**: Validates proxy connection before and after browser launch
- **Anti-Detection Measures**: Advanced browser fingerprinting protection

### 🛠️ Technical Improvements
- **Automatic ChromeDriver Management**: Uses `webdriver-manager` for automatic driver updates
- **Better Error Handling**: Comprehensive try-catch blocks with detailed logging
- **Async Telegram Support**: Improved async handling for Telegram notifications
- **Enhanced Bet Detection**: Multiple strategies for finding and extracting bet information
- **Persistent Storage**: Saves bet history to JSON file
- **Log Rotation**: Prevents log files from growing too large

### 📊 Monitoring Features
- **Real-time Bet Tracking**: Monitors active bets continuously
- **Smart Page Refresh**: Periodic page refresh to prevent session timeout
- **Status Updates**: Hourly status reports via Telegram
- **Error Recovery**: Automatic recovery from temporary failures
- **Detailed Logging**: Comprehensive logging with function names and line numbers

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Google Chrome browser
- Proxy server with authentication
- Telegram bot token
- Bwin.com account

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

If you encounter any issues, install packages individually:

```bash
pip install requests
pip install python-dotenv
pip install selenium
pip install webdriver-manager
pip install python-telegram-bot
```

### Step 2: Configure Settings

1. Copy the configuration template:
```bash
cp config.env.template config.env
```

2. Edit `config.env` with your actual credentials:
```env
# Proxy settings
PROXY_HOST=your-proxy.com
PROXY_PORT=8080
PROXY_USERNAME=proxyuser
PROXY_PASSWORD=proxypass
EXPECTED_PROXY_IP=123.456.789.000

# Bwin credentials
BWIN_USERNAME=your_email@example.com
BWIN_PASSWORD=your_password

# Telegram settings
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Monitoring settings
CHECK_INTERVAL=30
HEADLESS_MODE=false
```

### Step 3: Verify Proxy IP

Before running the monitor, verify your proxy's IP address:

```bash
# Using curl (Linux/Mac)
curl -x http://username:password@proxy:port https://api.ipify.org

# Using Python
python -c "import requests; print(requests.get('https://api.ipify.org', proxies={'http': 'http://user:pass@proxy:port', 'https': 'http://user:pass@proxy:port'}).text)"
```

Use this IP address as your `EXPECTED_PROXY_IP` in the configuration.

### Step 4: Set Up Telegram Bot

1. **Create a bot**:
   - Message @BotFather on Telegram
   - Send `/newbot`
   - Choose a name and username
   - Save the bot token

2. **Get your chat ID**:
   - Start a chat with your bot
   - Send any message
   - Visit: `https://api.telegram.org/bot<YourBotToken>/getUpdates`
   - Find the `"chat":{"id":xxxxx}` value

3. **For group notifications**:
   - Add the bot to your group
   - Make it an admin (for sending messages)
   - Use the negative group ID (e.g., -1001234567890)

### Step 5: Run the Monitor

```bash
python bwin_bet_monitor_final.py
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. Import Errors
```bash
# Error: ModuleNotFoundError: No module named 'requests'
# Solution:
pip install --upgrade requests

# If using virtual environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. ChromeDriver Issues
```bash
# The script now uses webdriver-manager for automatic driver management
# If issues persist, manually download ChromeDriver:
# 1. Check Chrome version: chrome://version
# 2. Download matching driver: https://chromedriver.chromium.org/
# 3. Place in project directory or PATH
```

#### 3. Proxy Connection Failed
- Verify proxy credentials are correct
- Test proxy with curl or browser
- Check if proxy allows HTTPS connections
- Ensure `EXPECTED_PROXY_IP` matches actual proxy IP

#### 4. Login Failed
- Verify Bwin credentials
- Check if account requires 2FA
- Try logging in manually first
- Clear Chrome user data folder

#### 5. Telegram Not Working
- Verify bot token is correct
- Ensure bot is in the chat/group
- Check chat ID (negative for groups)
- Test with: `https://api.telegram.org/bot<token>/sendMessage?chat_id=<id>&text=test`

### Debug Mode

Enable detailed debugging by setting in config.env:
```env
DEBUG_MODE=true
```

Or modify the logging level in the script:
```python
root_logger.setLevel(logging.DEBUG)
```

## 📁 File Structure

```
bwin-monitor/
├── bwin_bet_monitor_final.py    # Main script (improved version)
├── requirements.txt              # Python dependencies
├── config.env                    # Your configuration (create from template)
├── config.env.template           # Configuration template
├── chrome-user-data/            # Chrome profile directory (auto-created)
├── bwin_monitor.log             # Main log file (auto-created)
├── bet_history.json             # Bet history storage (auto-created)
└── README.md                    # Documentation
```

## 🔐 Security Best Practices

1. **Never commit config.env to version control**
   ```bash
   echo "config.env" >> .gitignore
   ```

2. **Use environment variables in production**:
   ```bash
   export PROXY_HOST=your-proxy.com
   export BWIN_USERNAME=your-email
   # ... set all variables
   python bwin_bet_monitor_final.py
   ```

3. **Restrict file permissions**:
   ```bash
   chmod 600 config.env  # Only owner can read/write
   ```

4. **Use a dedicated proxy** for betting activities

5. **Enable 2FA on Telegram** for added security

## 📊 Understanding the Output

### Log Messages

```
2024-01-15 10:30:00 - INFO - Verifying proxy connection...
✅ Proxy verification successful!
2024-01-15 10:30:05 - INFO - Launching Chrome browser...
2024-01-15 10:30:15 - INFO - Login successful!
2024-01-15 10:30:20 - INFO - Check #1 - Looking for new bets...
🎯 New bet detected: bet_1234567890
```

### Telegram Notifications

You'll receive notifications for:
- Monitor startup status
- New bets detected
- Hourly status updates
- Error alerts
- Monitor shutdown

### Bet History JSON

```json
{
  "last_updated": "2024-01-15T10:30:00",
  "total_bets": 5,
  "bets": [
    {
      "betslip_id": "bet_1234567890",
      "teams": "Team A vs Team B",
      "market": "1X2",
      "stake": "€10.00",
      "odds": "2.50",
      "possible_winnings": "€25.00",
      "bet_time": "2024-01-15 10:30:00",
      "status": "Active"
    }
  ]
}
```

## 🚨 Kill Switch Behavior

The monitor will automatically terminate if:

1. **Proxy verification fails** - Wrong IP or connection error
2. **Browser launch fails** - ChromeDriver issues
3. **Login fails** - Wrong credentials or site changes
4. **Bet history inaccessible** - Navigation errors
5. **Too many consecutive errors** - Default: 5 errors

## 🔄 Recovery Mechanisms

The monitor includes automatic recovery for:
- Temporary network issues
- Page load timeouts
- Session timeouts (via periodic refresh)
- Minor navigation errors

## 📈 Performance Tips

1. **Optimal check interval**: 30-60 seconds
2. **Use headless mode** for servers: `HEADLESS_MODE=true`
3. **Monitor resource usage** with system tools
4. **Clean Chrome profile** periodically:
   ```bash
   rm -rf chrome-user-data/
   ```

## 🆘 Support & Updates

### Getting Help

1. Check the log file for detailed error messages
2. Enable debug mode for more information
3. Test components individually (proxy, login, etc.)
4. Verify all configurations are correct

### Updating the Script

```bash
# Backup your configuration
cp config.env config.env.backup

# Update dependencies
pip install --upgrade -r requirements.txt

# Test with new version
python bwin_bet_monitor_final.py
```

## ⚖️ Legal Disclaimer

- This tool is for educational and personal use only
- Users must comply with bwin.com terms of service
- Follow local laws regarding automated betting tools
- Use responsibly and within legal boundaries
- The developers are not responsible for misuse

## 🎉 Success Checklist

- [ ] Python 3.8+ installed
- [ ] All dependencies installed
- [ ] config.env created with valid credentials
- [ ] Proxy IP verified
- [ ] Telegram bot created and configured
- [ ] Chrome browser installed
- [ ] Test run successful
- [ ] First bet notification received

## 📝 Version History

- **v2.0.0** (Current) - Complete rewrite with enhanced features
  - Automatic ChromeDriver management
  - Improved proxy authentication
  - Better error handling
  - Enhanced bet detection
  - Async Telegram support
  - JSON bet history storage

## 🔮 Future Enhancements

Planned features for future versions:
- Web dashboard for monitoring
- Multiple account support
- Advanced bet filtering
- Statistical analysis
- Email notifications
- Database storage (SQLite/PostgreSQL)
- REST API for external integration

---

**Remember**: Always gamble responsibly and within your means. This tool is for monitoring purposes only.