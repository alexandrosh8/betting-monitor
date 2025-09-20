#!/usr/bin/env python3
"""
Bwin Betting Monitor - IMPROVED VERSION
Enhanced security, reliability, and functionality
"""

import os
import sys
import time
import json
import logging
import asyncio
import zipfile
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

# Third-party imports with error handling
try:
    import requests
    from dotenv import load_dotenv
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import (
        TimeoutException, 
        NoSuchElementException,
        WebDriverException
    )
    from selenium.webdriver.common.keys import Keys
    from telegram import Bot
    from telegram.error import TelegramError
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Please install requirements: pip install -r requirements.txt")
    sys.exit(1)

# Configure logging with rotation
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Setup comprehensive logging with rotation"""
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        'bwin_monitor.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(log_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return logging.getLogger(__name__)

logger = setup_logging()

@dataclass
class ProxyConfig:
    """Enhanced proxy configuration with validation"""
    host: str
    port: int
    username: str
    password: str
    expected_ip: str
    timeout: int = 10
    verify_ssl: bool = False
    
    def __post_init__(self):
        """Validate proxy configuration"""
        if not self.host or not self.username:
            raise ValueError("Invalid proxy configuration")
        if not 1 <= self.port <= 65535:
            raise ValueError(f"Invalid port number: {self.port}")
    
    @property
    def proxy_url(self) -> str:
        return f"http://{self.username}:{self.password}@{self.host}:{self.port}"
    
    @property
    def proxy_dict(self) -> Dict[str, str]:
        return {
            'http': self.proxy_url,
            'https': self.proxy_url
        }

@dataclass
class LoginCredentials:
    """Login credentials with validation"""
    username: str
    password: str
    
    def __post_init__(self):
        if not self.username or not self.password:
            raise ValueError("Username and password are required")

@dataclass
class TelegramConfig:
    """Telegram configuration with validation"""
    bot_token: str
    chat_id: str
    
    def __post_init__(self):
        if not self.bot_token or not self.chat_id:
            raise ValueError("Bot token and chat ID are required")

@dataclass
class BetInfo:
    """Enhanced bet information"""
    betslip_id: str
    teams: str
    market: str
    stake: str
    odds: str
    possible_winnings: str
    bet_time: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    status: str = "Active"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'betslip_id': self.betslip_id,
            'teams': self.teams,
            'market': self.market,
            'stake': self.stake,
            'odds': self.odds,
            'possible_winnings': self.possible_winnings,
            'bet_time': self.bet_time,
            'status': self.status
        }

class ProxyVerifier:
    """Enhanced proxy verification with multiple checks"""
    
    @staticmethod
    def verify_proxy(proxy_config: ProxyConfig) -> bool:
        """Comprehensive proxy verification"""
        logger.info(f"Verifying proxy connection to {proxy_config.host}:{proxy_config.port}")
        
        # Multiple IP check services for redundancy
        ip_services = [
            'https://api.ipify.org?format=json',
            'https://ifconfig.me/ip',
            'https://api.myip.com'
        ]
        
        for service in ip_services:
            try:
                logger.info(f"Testing proxy with {service}")
                
                response = requests.get(
                    service,
                    proxies=proxy_config.proxy_dict,
                    timeout=proxy_config.timeout,
                    verify=proxy_config.verify_ssl
                )
                
                if response.status_code == 200:
                    # Parse response based on service
                    if 'json' in service:
                        actual_ip = response.json().get('ip', '')
                    else:
                        actual_ip = response.text.strip()
                    
                    logger.info(f"Proxy IP detected: {actual_ip}")
                    logger.info(f"Expected IP: {proxy_config.expected_ip}")
                    
                    if actual_ip == proxy_config.expected_ip:
                        logger.info("Proxy verification successful!")
                        return True
                    else:
                        logger.error(f"IP mismatch! Expected: {proxy_config.expected_ip}, Got: {actual_ip}")
                        
            except requests.exceptions.RequestException as e:
                logger.warning(f"Service {service} failed: {e}")
                continue
        
        logger.error("KILL SWITCH: All proxy verification attempts failed")
        return False

class EnhancedBrowserManager:
    """Enhanced browser manager with better proxy handling"""
    
    def __init__(self, proxy_config: ProxyConfig, headless: bool = False):
        self.proxy_config = proxy_config
        self.headless = headless
        self.driver = None
        # Use unique session directory for complete isolation
        import uuid
        session_id = str(uuid.uuid4())[:8]
        self.user_data_dir = Path(f"./chrome-session-{session_id}")
        self.extension_dir = None
        
    def create_proxy_extension(self) -> Path:
        """Create improved proxy authentication extension"""
        try:
            # Create temporary directory for extension
            self.extension_dir = Path(tempfile.mkdtemp(prefix="proxy_ext_"))
            
            # Manifest for Chrome extension
            manifest = {
                "version": "1.0.0",
                "manifest_version": 2,
                "name": "Proxy Auth Extension",
                "permissions": [
                    "proxy",
                    "tabs",
                    "unlimitedStorage",
                    "storage",
                    "<all_urls>",
                    "webRequest",
                    "webRequestBlocking",
                    "webRequestAuthProvider"
                ],
                "background": {
                    "scripts": ["background.js"],
                    "persistent": True
                },
                "minimum_chrome_version": "22.0.0"
            }
            
            # Background script for proxy authentication
            background_js = f'''
var config = {{
    mode: "fixed_servers",
    rules: {{
        singleProxy: {{
            scheme: "http",
            host: "{self.proxy_config.host}",
            port: {self.proxy_config.port}
        }},
        bypassList: ["localhost", "127.0.0.1"]
    }}
}};

chrome.proxy.settings.set({{
    value: config,
    scope: "regular"
}}, function() {{
    console.log("Proxy settings configured");
}});

function handleAuthRequired(details) {{
    console.log("Providing proxy authentication");
    return {{
        authCredentials: {{
            username: "{self.proxy_config.username}",
            password: "{self.proxy_config.password}"
        }}
    }};
}}

chrome.webRequest.onAuthRequired.addListener(
    handleAuthRequired,
    {{urls: ["<all_urls>"]}},
    ['blocking']
);

chrome.runtime.onInstalled.addListener(function() {{
    console.log("Proxy extension installed successfully");
}});
'''
            
            # Write extension files
            (self.extension_dir / "manifest.json").write_text(
                json.dumps(manifest, indent=2)
            )
            (self.extension_dir / "background.js").write_text(background_js)
            
            logger.info(f"Created proxy extension at: {self.extension_dir}")
            return self.extension_dir
            
        except Exception as e:
            logger.error(f"Failed to create proxy extension: {e}")
            raise
    
    def launch_chrome(self) -> webdriver.Chrome:
        """Launch Chrome with enhanced configuration"""
        logger.info("Launching Chrome browser with proxy")
        
        try:
            options = Options()
            
            # Create proxy extension
            extension_path = self.create_proxy_extension()
            options.add_argument(f'--load-extension={extension_path}')
            
            # User data directory
            self.user_data_dir.mkdir(exist_ok=True)
            options.add_argument(f'--user-data-dir={self.user_data_dir}')
            
            # Standalone Chrome options with consistent unit ID
            options.add_argument('--start-maximized')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Force standalone operation - prevent local Chrome integration
            options.add_argument('--disable-machine-cert-request')
            options.add_argument('--disable-client-side-phishing-detection')
            options.add_argument('--disable-component-update')
            options.add_argument('--disable-default-apps')
            options.add_argument('--disable-domain-reliability')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-renderer-backgrounding')
            options.add_argument('--disable-backgrounding-occluded-windows')
            options.add_argument('--disable-sync')
            options.add_argument('--disable-background-networking')
            options.add_argument('--disable-features=TranslateUI')
            options.add_argument('--disable-ipc-flooding-protection')
            options.add_argument('--no-first-run')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--disable-plugins-discovery')
            options.add_argument('--disable-preconnect')
            
            # Anti-detection measures
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--disable-gpu-sandbox')
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--disable-web-security')
            options.add_argument('--disable-features=VizDisplayCompositor,VizServiceDisplayCompositor')
            
            # Consistent user agent for standalone operation
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 BwinBot/1.0'
            options.add_argument(f'--user-agent={user_agent}')
            
            if self.headless:
                options.add_argument('--headless=new')
                options.add_argument('--window-size=1920,1080')
            
            # Use standalone Chrome binary and ChromeDriver
            driver_path = './chromedriver-win64/chromedriver.exe'
            chrome_binary_path = './chrome-win64/chrome.exe'
            
            if not os.path.exists(driver_path):
                logger.error("ChromeDriver not found at ./chromedriver-win64/chromedriver.exe")
                logger.error("Please ensure ChromeDriver is in the project directory")
                raise FileNotFoundError("ChromeDriver not found in project directory")
            
            # Force standalone operation even with system Chrome
            # These options prevent Chrome from using local profiles and data
            options.add_argument('--disable-extensions-except=' + str(extension_path))
            options.add_argument('--disable-component-extensions-with-background-pages')
            options.add_argument('--disable-extensions-file-access-check')
            options.add_argument('--disable-extensions-http-throttling')
            options.add_argument('--aggressive-cache-discard')
            options.add_argument('--disable-background-mode')
            options.add_argument('--remote-debugging-port=0')
            options.add_argument('--disable-shared-memory-usage')
            options.add_argument('--force-new-instance')
            
            # Check for standalone Chrome binary
            if os.path.exists(chrome_binary_path):
                logger.info(f"Using standalone Chrome binary: {chrome_binary_path}")
                options.binary_location = chrome_binary_path
            else:
                logger.info("Using system Chrome with standalone configuration")
                logger.info("Chrome will run independently from local profiles")
                
            service = Service(driver_path)
            
            # Create driver
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Set timeouts
            self.driver.set_page_load_timeout(60)
            self.driver.implicitly_wait(10)
            
            # Execute CDP commands to mask automation and set consistent fingerprint
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    // Hide webdriver property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Set consistent hardware fingerprint for standalone operation
                    Object.defineProperty(navigator, 'hardwareConcurrency', {
                        get: () => 8
                    });
                    
                    // Override platform info for consistency
                    Object.defineProperty(navigator, 'platform', {
                        get: () => 'Win32'
                    });
                    
                    // Set consistent screen resolution
                    Object.defineProperty(screen, 'width', {
                        get: () => 1920
                    });
                    Object.defineProperty(screen, 'height', {
                        get: () => 1080
                    });
                '''
            })
            
            # Verify proxy in browser
            if not self._verify_browser_proxy():
                raise Exception("Browser proxy verification failed")
            
            logger.info("Chrome launched successfully with proxy")
            return self.driver
            
        except Exception as e:
            logger.error(f"Failed to launch Chrome: {e}")
            self.cleanup()
            raise
    
    def _verify_browser_proxy(self) -> bool:
        """Verify proxy is working in browser"""
        try:
            logger.info("Verifying proxy in browser...")
            self.driver.get('https://api.ipify.org?format=json')
            time.sleep(3)
            
            # Get page source and check for expected IP
            page_source = self.driver.page_source
            if self.proxy_config.expected_ip in page_source:
                logger.info(f"Browser proxy verified: {self.proxy_config.expected_ip}")
                return True
            else:
                logger.error("Browser proxy verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Browser proxy verification error: {e}")
            return False
    
    def cleanup(self):
        """Clean up browser and temporary files"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")
            
            if self.extension_dir and self.extension_dir.exists():
                shutil.rmtree(self.extension_dir, ignore_errors=True)
                logger.info("Cleaned up extension directory")
            
            # Clean up session directory
            if self.user_data_dir and self.user_data_dir.exists():
                shutil.rmtree(self.user_data_dir, ignore_errors=True)
                logger.info(f"Cleaned up session directory: {self.user_data_dir}")
                
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

class EnhancedBwinLogin:
    """Enhanced login handler with better error handling"""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)
        
    def login(self, credentials: LoginCredentials, max_attempts: int = 3) -> bool:
        """Login with retry logic"""
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Login attempt {attempt}/{max_attempts}")
            
            if self._attempt_login(credentials):
                return True
            
            if attempt < max_attempts:
                logger.warning(f"Login failed, retrying in 5 seconds...")
                time.sleep(5)
        
        logger.error("All login attempts failed")
        return False
    
    def _attempt_login(self, credentials: LoginCredentials) -> bool:
        """Single login attempt"""
        try:
            # Navigate to the specified login page
            login_url = 'https://www.bwin.com/en/labelhost/login?rurlauth=1&rurl=https:%2F%2Fwww.bwin.com%2Fen%2Fsports%2Fmy-bets'
            logger.info(f"Navigating to bwin login: {login_url}")
            self.driver.get(login_url)
            
            # Wait for page load
            time.sleep(5)
            
            # Find and fill username field
            username_selectors = [
                'input[name="username"]',
                'input[type="email"]',
                '#userId',
                'input[formcontrolname="username"]'
            ]
            
            username_field = None
            for selector in username_selectors:
                try:
                    username_field = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"Found username field: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not username_field:
                logger.error("Username field not found")
                return False
            
            # Clear and enter username
            username_field.clear()
            username_field.send_keys(credentials.username)
            time.sleep(1)
            
            # Find and fill password field
            password_field = self.driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
            password_field.clear()
            password_field.send_keys(credentials.password)
            time.sleep(1)
            
            # Submit form
            submit_selectors = [
                'button[type="submit"]',
                'button.login-button',
                'input[type="submit"]'
            ]
            
            for selector in submit_selectors:
                try:
                    submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    submit_button.click()
                    break
                except NoSuchElementException:
                    continue
            
            # Wait for login to complete
            logger.info("Waiting for login to complete...")
            time.sleep(10)
            
            # Check if login successful
            current_url = self.driver.current_url
            logger.info(f"Current URL after login: {current_url}")
            
            # Check for login indicators
            if 'login' not in current_url.lower():
                # Additional verification - check for user menu or account elements
                user_indicators = [
                    '.user-menu',
                    '.account-balance',
                    '[class*="balance"]',
                    '[class*="user"]'
                ]
                
                for indicator in user_indicators:
                    try:
                        self.driver.find_element(By.CSS_SELECTOR, indicator)
                        logger.info(f"✅ Login successful - found {indicator}")
                        return True
                    except NoSuchElementException:
                        continue
                
                # If no indicators but URL changed, assume success
                logger.info("✅ Login appears successful")
                return True
            
            logger.warning("Login may have failed - still on login page")
            return False
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

class EnhancedBetMonitor:
    """Enhanced bet monitoring with better detection"""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)
        self.known_bets = set()
        self.bet_history = []
        
    def navigate_to_bet_history(self) -> bool:
        """Navigate to bet history with verification"""
        try:
            # Use the exact bet history URL specified by user
            urls = [
                'https://www.bwin.com/en/sports/my-bets/open',
                'https://www.bwin.com/en/sports/my-bets',
                'https://www.bwin.com/en/mybets'
            ]
            
            for url in urls:
                logger.info(f"Trying URL: {url}")
                self.driver.get(url)
                time.sleep(5)
                
                # Check if we're on a bet-related page
                if self._verify_bet_page():
                    logger.info(f"✅ Successfully navigated to bet history")
                    return True
            
            logger.error("Could not navigate to bet history")
            return False
            
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            return False
    
    def _verify_bet_page(self) -> bool:
        """Verify we're on a bet-related page"""
        try:
            # Check for bet-related elements
            bet_indicators = [
                '[class*="bet"]',
                '[class*="slip"]',
                '[class*="ticket"]',
                '.my-bets',
                '#betHistory'
            ]
            
            for indicator in bet_indicators:
                elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                if elements:
                    logger.info(f"Found bet indicator: {indicator}")
                    return True
            
            # Check page title or URL
            if 'bet' in self.driver.current_url.lower():
                return True
            
            return False
            
        except Exception:
            return False
    
    def scan_for_bets(self) -> List[BetInfo]:
        """Enhanced bet scanning with multiple strategies"""
        logger.info("Scanning for active bets...")
        bets = []
        
        try:
            # Strategy 1: Look for bet slip containers
            bet_selectors = [
                '[class*="betslip"]',
                '[class*="bet-slip"]',
                '[class*="ticket"]',
                '[data-testid*="bet"]',
                '.card',
                '[class*="coupon"]'
            ]
            
            bet_elements = []
            for selector in bet_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    bet_elements.extend(elements)
            
            # Remove duplicates
            bet_elements = list(set(bet_elements))
            
            # Extract bet information
            for i, element in enumerate(bet_elements):
                try:
                    bet_info = self._extract_bet_info(element, i)
                    if bet_info:
                        bets.append(bet_info)
                except Exception as e:
                    logger.debug(f"Could not extract bet info from element {i}: {e}")
                    continue
            
            # Strategy 2: Look for table rows if no cards found
            if not bets:
                logger.info("Trying table-based bet detection...")
                table_rows = self.driver.find_elements(By.CSS_SELECTOR, 'tr[class*="bet"], tbody tr')
                
                for i, row in enumerate(table_rows):
                    try:
                        bet_info = self._extract_bet_from_row(row, i)
                        if bet_info:
                            bets.append(bet_info)
                    except Exception:
                        continue
            
            logger.info(f"Found {len(bets)} total bets")
            return bets
            
        except Exception as e:
            logger.error(f"Bet scanning error: {e}")
            return []
    
    def _extract_bet_info(self, element, index: int) -> Optional[BetInfo]:
        """Extract bet information from element"""
        try:
            text = element.text.strip()
            if not text or len(text) < 10:
                return None
            
            # Try to extract specific fields
            bet_id = element.get_attribute('id') or f"bet_{int(time.time())}_{index}"
            
            # Parse text for bet details
            lines = text.split('\n')
            
            # Create bet info with extracted or placeholder data
            bet_info = BetInfo(
                betslip_id=bet_id,
                teams=self._extract_teams(lines),
                market=self._extract_market(lines),
                stake=self._extract_stake(lines),
                odds=self._extract_odds(lines),
                possible_winnings=self._extract_winnings(lines)
            )
            
            return bet_info
            
        except Exception as e:
            logger.debug(f"Failed to extract bet info: {e}")
            return None
    
    def _extract_bet_from_row(self, row, index: int) -> Optional[BetInfo]:
        """Extract bet information from table row"""
        try:
            cells = row.find_elements(By.TAG_NAME, 'td')
            if len(cells) < 3:
                return None
            
            # Extract cell texts
            cell_texts = [cell.text.strip() for cell in cells]
            
            bet_info = BetInfo(
                betslip_id=f"row_bet_{int(time.time())}_{index}",
                teams=cell_texts[0] if len(cell_texts) > 0 else "Unknown",
                market=cell_texts[1] if len(cell_texts) > 1 else "Unknown",
                stake=cell_texts[2] if len(cell_texts) > 2 else "Unknown",
                odds=cell_texts[3] if len(cell_texts) > 3 else "Unknown",
                possible_winnings=cell_texts[4] if len(cell_texts) > 4 else "Unknown"
            )
            
            return bet_info
            
        except Exception:
            return None
    
    def _extract_teams(self, lines: List[str]) -> str:
        """Extract team names from text lines"""
        for line in lines:
            if ' vs ' in line or ' v ' in line or ' - ' in line:
                return line
        return lines[0] if lines else "Unknown Teams"
    
    def _extract_market(self, lines: List[str]) -> str:
        """Extract market type from text lines"""
        market_keywords = ['1X2', 'Over', 'Under', 'BTTS', 'Handicap', 'Draw']
        for line in lines:
            for keyword in market_keywords:
                if keyword in line:
                    return line
        return "Unknown Market"
    
    def _extract_stake(self, lines: List[str]) -> str:
        """Extract stake amount from text lines"""
        for line in lines:
            if '€' in line or '$' in line or '£' in line:
                return line
        return "Unknown Stake"
    
    def _extract_odds(self, lines: List[str]) -> str:
        """Extract odds from text lines"""
        import re
        for line in lines:
            # Look for decimal odds pattern
            if re.search(r'\d+\.\d{2}', line):
                return line
        return "Unknown Odds"
    
    def _extract_winnings(self, lines: List[str]) -> str:
        """Extract possible winnings from text lines"""
        keywords = ['win', 'return', 'payout']
        for line in lines:
            if any(keyword in line.lower() for keyword in keywords):
                return line
        return "Unknown Winnings"
    
    def check_for_new_bets(self) -> List[BetInfo]:
        """Check for new bets and return them"""
        current_bets = self.scan_for_bets()
        new_bets = []
        
        for bet in current_bets:
            if bet.betslip_id not in self.known_bets:
                new_bets.append(bet)
                self.known_bets.add(bet.betslip_id)
                self.bet_history.append(bet)
                logger.info(f"🎯 New bet detected: {bet.betslip_id}")
        
        return new_bets
    
    def save_bet_history(self, filename: str = "bet_history.json"):
        """Save bet history to JSON file"""
        try:
            history_data = {
                'last_updated': datetime.now().isoformat(),
                'total_bets': len(self.bet_history),
                'bets': [bet.to_dict() for bet in self.bet_history]
            }
            
            with open(filename, 'w') as f:
                json.dump(history_data, f, indent=2)
            
            logger.info(f"Saved bet history to {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save bet history: {e}")

class EnhancedTelegramNotifier:
    """Enhanced Telegram notifier with async support"""
    
    def __init__(self, config: TelegramConfig):
        self.bot = Bot(token=config.bot_token)
        self.chat_id = config.chat_id
        
    async def send_bet_notification_async(self, bet: BetInfo) -> bool:
        """Send bet notification asynchronously"""
        try:
            message = f"""
🎯 <b>NEW BET DETECTED!</b>

🆔 <b>Bet ID:</b> <code>{bet.betslip_id}</code>
⚽ <b>Match:</b> {bet.teams}
📊 <b>Market:</b> {bet.market}
💰 <b>Stake:</b> {bet.stake}
🎲 <b>Odds:</b> {bet.odds}
🏆 <b>Potential Win:</b> {bet.possible_winnings}
🕐 <b>Time:</b> {bet.bet_time}
📌 <b>Status:</b> {bet.status}

🍀 Good luck!
            """.strip()
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            
            logger.info(f"✅ Telegram notification sent for {bet.betslip_id}")
            return True
            
        except TelegramError as e:
            logger.error(f"Telegram error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    def send_bet_notification(self, bet: BetInfo) -> bool:
        """Send bet notification (sync wrapper)"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.send_bet_notification_async(bet)
            )
            loop.close()
            return result
            
        except Exception as e:
            logger.error(f"Notification error: {e}")
            return False
    
    async def send_status_update_async(self, message: str) -> bool:
        """Send status update message"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=f"ℹ️ <b>Status Update:</b>\n{message}",
                parse_mode='HTML'
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send status update: {e}")
            return False
    
    def send_status_update(self, message: str) -> bool:
        """Send status update (sync wrapper)"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.send_status_update_async(message)
            )
            loop.close()
            return result
        except Exception:
            return False

class BwinBetMonitor:
    """Main monitoring application with enhanced features"""
    
    def __init__(self, proxy_config: ProxyConfig, login_creds: LoginCredentials,
                 telegram_config: TelegramConfig, headless: bool = False):
        self.proxy_config = proxy_config
        self.login_creds = login_creds
        self.telegram_config = telegram_config
        self.headless = headless
        
        self.browser_manager = None
        self.driver = None
        self.bet_monitor = None
        self.telegram_notifier = None
        self.monitoring_active = False
        
    def initialize(self) -> bool:
        """Initialize all components with comprehensive checks"""
        logger.info("="*50)
        logger.info("Initializing Bwin Bet Monitor - Enhanced Version")
        logger.info("="*50)
        
        try:
            # Step 1: Verify proxy (KILL SWITCH)
            logger.info("Step 1/4: Verifying proxy connection...")
            if not ProxyVerifier.verify_proxy(self.proxy_config):
                logger.error("❌ KILL SWITCH: Proxy verification failed")
                self.telegram_notifier = EnhancedTelegramNotifier(self.telegram_config)
                self.telegram_notifier.send_status_update(
                    "⚠️ Monitor startup failed: Proxy verification error"
                )
                return False
            
            # Step 2: Launch browser
            logger.info("Step 2/4: Launching browser...")
            self.browser_manager = EnhancedBrowserManager(self.proxy_config, self.headless)
            self.driver = self.browser_manager.launch_chrome()
            
            # Step 3: Initialize Telegram
            logger.info("Step 3/4: Initializing Telegram notifier...")
            self.telegram_notifier = EnhancedTelegramNotifier(self.telegram_config)
            self.telegram_notifier.send_status_update(
                "🚀 Bet monitor starting up..."
            )
            
            # Step 4: Login to Bwin
            logger.info("Step 4/4: Logging in to Bwin...")
            login_handler = EnhancedBwinLogin(self.driver)
            if not login_handler.login(self.login_creds):
                logger.error("❌ KILL SWITCH: Login failed")
                self.telegram_notifier.send_status_update(
                    "⚠️ Monitor startup failed: Login error"
                )
                self.cleanup()
                return False
            
            # Initialize bet monitor
            self.bet_monitor = EnhancedBetMonitor(self.driver)
            if not self.bet_monitor.navigate_to_bet_history():
                logger.error("❌ KILL SWITCH: Could not access bet history")
                self.telegram_notifier.send_status_update(
                    "⚠️ Monitor startup failed: Cannot access bet history"
                )
                self.cleanup()
                return False
            
            # Send success notification
            self.telegram_notifier.send_status_update(
                "✅ Bet monitor initialized successfully!\n"
                f"Proxy IP: {self.proxy_config.expected_ip}\n"
                "Monitoring active bets..."
            )
            
            self.monitoring_active = True
            logger.info("✅ All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            if self.telegram_notifier:
                self.telegram_notifier.send_status_update(
                    f"⚠️ Monitor startup failed: {str(e)}"
                )
            self.cleanup()
            return False
    
    def run_monitoring_loop(self, check_interval: int = 30, max_errors: int = 5):
        """Run monitoring loop with error handling"""
        if not self.monitoring_active:
            logger.error("Cannot start monitoring - initialization failed")
            return
        
        logger.info(f"Starting monitoring loop (checking every {check_interval}s)")
        consecutive_errors = 0
        check_count = 0
        
        try:
            while self.monitoring_active:
                check_count += 1
                logger.info(f"Check #{check_count} - Looking for new bets...")
                
                try:
                    # Refresh page periodically
                    if check_count % 10 == 0:
                        logger.info("Refreshing bet history page...")
                        self.driver.refresh()
                        time.sleep(5)
                    
                    # Check for new bets
                    new_bets = self.bet_monitor.check_for_new_bets()
                    
                    if new_bets:
                        logger.info(f"Found {len(new_bets)} new bet(s)!")
                        for bet in new_bets:
                            self.telegram_notifier.send_bet_notification(bet)
                        
                        # Save bet history
                        self.bet_monitor.save_bet_history()
                    else:
                        logger.info("No new bets found")
                    
                    # Reset error counter on success
                    consecutive_errors = 0
                    
                    # Status update every hour
                    if check_count % (3600 // check_interval) == 0:
                        self.telegram_notifier.send_status_update(
                            f"Monitor active - {check_count} checks completed\n"
                            f"Total bets tracked: {len(self.bet_monitor.known_bets)}"
                        )
                    
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(f"Monitoring error ({consecutive_errors}/{max_errors}): {e}")
                    
                    if consecutive_errors >= max_errors:
                        logger.error("Max errors reached - stopping monitor")
                        self.telegram_notifier.send_status_update(
                            "⚠️ Monitor stopped: Too many errors"
                        )
                        break
                    
                    # Try to recover
                    logger.info("Attempting to recover...")
                    try:
                        self.bet_monitor.navigate_to_bet_history()
                    except Exception:
                        pass
                
                # Wait for next check
                logger.info(f"Waiting {check_interval} seconds until next check...")
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            logger.info("Monitor stopped by user")
            self.telegram_notifier.send_status_update(
                "Monitor stopped by user"
            )
        except Exception as e:
            logger.error(f"Critical error in monitoring loop: {e}")
            self.telegram_notifier.send_status_update(
                f"⚠️ Monitor crashed: {str(e)}"
            )
        finally:
            self.monitoring_active = False
            self.cleanup()
    
    def cleanup(self):
        """Clean up all resources"""
        logger.info("Cleaning up resources...")
        
        try:
            if self.bet_monitor:
                self.bet_monitor.save_bet_history()
            
            if self.browser_manager:
                self.browser_manager.cleanup()
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

def load_configuration() -> Tuple[ProxyConfig, LoginCredentials, TelegramConfig, int, bool]:
    """Load and validate configuration"""
    # Load from .env file
    env_files = ['config.env', '.env']
    for env_file in env_files:
        if os.path.exists(env_file):
            load_dotenv(env_file)
            logger.info(f"Loaded configuration from {env_file}")
            break
    
    # Required environment variables
    required_vars = [
        'PROXY_HOST', 'PROXY_PORT', 'PROXY_USERNAME', 'PROXY_PASSWORD', 'EXPECTED_PROXY_IP',
        'BWIN_USERNAME', 'BWIN_PASSWORD',
        'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID'
    ]
    
    # Check for missing variables
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please create a config.env file with all required variables")
        sys.exit(1)
    
    try:
        # Create configuration objects
        proxy_config = ProxyConfig(
            host=os.getenv('PROXY_HOST'),
            port=int(os.getenv('PROXY_PORT')),
            username=os.getenv('PROXY_USERNAME'),
            password=os.getenv('PROXY_PASSWORD'),
            expected_ip=os.getenv('EXPECTED_PROXY_IP')
        )
        
        login_credentials = LoginCredentials(
            username=os.getenv('BWIN_USERNAME'),
            password=os.getenv('BWIN_PASSWORD')
        )
        
        telegram_config = TelegramConfig(
            bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
            chat_id=os.getenv('TELEGRAM_CHAT_ID')
        )
        
        # Optional settings
        check_interval = int(os.getenv('CHECK_INTERVAL', '30'))
        headless_mode = os.getenv('HEADLESS_MODE', 'false').lower() == 'true'
        
        return proxy_config, login_credentials, telegram_config, check_interval, headless_mode
        
    except ValueError as e:
        logger.error(f"Invalid configuration value: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    print("""
    ╔══════════════════════════════════════════╗
    ║   BWIN BET MONITOR - ENHANCED VERSION   ║
    ║         Proxy-Protected & Secure         ║
    ╚══════════════════════════════════════════╝
    """)
    
    # Load configuration
    try:
        proxy_config, login_creds, telegram_config, check_interval, headless_mode = load_configuration()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Display configuration (without sensitive data)
    logger.info("Configuration loaded:")
    logger.info(f"  Proxy: {proxy_config.host}:{proxy_config.port}")
    logger.info(f"  Expected IP: {proxy_config.expected_ip}")
    logger.info(f"  Check interval: {check_interval} seconds")
    logger.info(f"  Headless mode: {headless_mode}")
    
    # Create and run monitor
    monitor = BwinBetMonitor(
        proxy_config=proxy_config,
        login_creds=login_creds,
        telegram_config=telegram_config,
        headless=headless_mode
    )
    
    if monitor.initialize():
        monitor.run_monitoring_loop(check_interval=check_interval)
    else:
        logger.error("Failed to initialize monitor")
        sys.exit(1)

if __name__ == "__main__":
    main()