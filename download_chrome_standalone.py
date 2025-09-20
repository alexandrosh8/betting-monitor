#!/usr/bin/env python3
"""
Download standalone Chrome binary for the betting bot
This ensures completely standalone operation without using local Chrome
"""

import os
import sys
import zipfile
import requests
from pathlib import Path

def download_chrome_standalone():
    """Download standalone Chrome binary"""
    print("🔽 Downloading standalone Chrome binary...")
    
    # Chrome for Testing API URL for stable version
    chrome_url = "https://storage.googleapis.com/chrome-for-testing-public/139.0.7258.154/win64/chrome-win64.zip"
    chrome_zip_path = "chrome-win64.zip"
    chrome_dir = "chrome-win64"
    
    try:
        # Remove existing directory if it exists
        if os.path.exists(chrome_dir):
            print(f"📂 Removing existing {chrome_dir} directory...")
            import shutil
            shutil.rmtree(chrome_dir)
        
        # Download Chrome binary
        print(f"📥 Downloading Chrome from: {chrome_url}")
        response = requests.get(chrome_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(chrome_zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r📊 Progress: {percent:.1f}% ({downloaded:,}/{total_size:,} bytes)", end='')
        
        print(f"\n✅ Chrome binary downloaded: {chrome_zip_path}")
        
        # Extract Chrome binary
        print("📦 Extracting Chrome binary...")
        with zipfile.ZipFile(chrome_zip_path, 'r') as zip_ref:
            zip_ref.extractall('.')
        
        # Verify extraction
        chrome_exe = os.path.join(chrome_dir, 'chrome.exe')
        if os.path.exists(chrome_exe):
            print(f"✅ Chrome binary extracted successfully: {chrome_exe}")
            file_size = os.path.getsize(chrome_exe)
            print(f"📏 Chrome.exe size: {file_size:,} bytes")
        else:
            print(f"❌ Chrome.exe not found at: {chrome_exe}")
            return False
        
        # Clean up zip file
        os.remove(chrome_zip_path)
        print(f"🗑️ Cleaned up: {chrome_zip_path}")
        
        print("\n🎉 Standalone Chrome setup complete!")
        print(f"📁 Chrome binary location: {os.path.abspath(chrome_exe)}")
        print("🤖 The betting bot will now use this standalone Chrome binary")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Download failed: {e}")
        return False
    except zipfile.BadZipFile as e:
        print(f"❌ Zip extraction failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Chrome Standalone Downloader for Bwin Betting Bot")
    print("=" * 50)
    
    # Check if already exists
    chrome_exe = os.path.join("chrome-win64", "chrome.exe")
    if os.path.exists(chrome_exe):
        file_size = os.path.getsize(chrome_exe)
        print(f"ℹ️ Standalone Chrome already exists: {chrome_exe}")
        print(f"📏 Size: {file_size:,} bytes")
        
        response = input("🤔 Do you want to re-download? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("✅ Using existing Chrome binary")
            return
    
    # Download Chrome
    if download_chrome_standalone():
        print("\n✅ Setup complete! You can now run the betting bot with standalone Chrome.")
    else:
        print("\n❌ Setup failed. Please check your internet connection and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
