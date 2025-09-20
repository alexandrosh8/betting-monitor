# 🚀 Quick Start Guide

Get your Bwin Betting Monitor running in 5 minutes!

## Step 1: Install Dependencies
```bash
python setup.py
```

## Step 2: Configure Your Settings
```bash
# Copy the template
cp config.env.template config.env

# Edit with your details
nano config.env  # or use any text editor
```

**Required Settings:**
```env
PROXY_HOST=your-proxy-server.com
PROXY_PORT=8080
PROXY_USERNAME=your-username
PROXY_PASSWORD=your-password

BWIN_USERNAME=your-bwin-username
BWIN_PASSWORD=your-bwin-password

TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=-1001234567890
```

## Step 3: Test Your Setup
```bash
python example_usage.py test
```

If all tests pass ✅, you're ready!

## Step 4: Run the Monitor
```bash
python bwin_bet_monitor.py
```

## 🆘 Need Help?

### Getting Telegram Bot Token:
1. Message @BotFather on Telegram
2. Send `/newbot`
3. Follow instructions
4. Copy your token

### Getting Chat ID:
1. Add your bot to a group OR message it directly  
2. Visit: `https://api.telegram.org/botYOUR_TOKEN/getUpdates`
3. Look for "chat":{"id": -1234567890}
4. Use that ID (including minus sign for groups)

### Proxy Issues:
- Test your proxy with a browser first
- Make sure authentication is required
- Check if proxy allows HTTPS

### Quick Test Commands:
```bash
python example_usage.py proxy     # Test proxy only
python example_usage.py browser   # Test browser launch
python example_usage.py telegram  # Test Telegram config
```

## 🎯 What Happens When Running?

1. **Proxy Check** ✅ → Verifies your proxy works
2. **Chrome Launch** 🌐 → Opens browser with proxy
3. **Login** 🔐 → Logs into bwin.com automatically  
4. **Navigation** 📊 → Goes to bet history page
5. **Monitoring** 👀 → Watches for new bets every 30 seconds
6. **Notifications** 📱 → Sends Telegram alerts for new bets

## 🛑 Kill Switches

The script will automatically stop if:
- Proxy connection fails
- Login to bwin.com fails  
- Cannot access bet history
- Browser crashes

This protects you from wasting resources on a broken setup.

## ⚙️ Advanced Options

**Headless Mode** (no browser window):
```env
HEADLESS_MODE=true
```

**Custom Check Interval** (seconds):
```env
CHECK_INTERVAL=60
```

**Stop the Monitor:**
Press `Ctrl+C` to stop gracefully.

---

**Ready?** Run `python bwin_bet_monitor.py` and watch the magic happen! 🎉
