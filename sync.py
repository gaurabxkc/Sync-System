import os
import json
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# --- CONFIG ---
FACEBOOK_URL = "https://www.facebook.com/fsupulchowk"
GIST_ID = os.environ.get("GIST_ID")
GH_PAT = os.environ.get("GH_PAT")
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

# GitHub Gist API Headers
HEADERS = {
    "Authorization": f"token {GH_PAT}",
    "Accept": "application/vnd.github.v3+json"
}

def get_last_saved_post():
    """Fetch content from GitHub Gist"""
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            content = response.json()["files"]["status.json"]["content"]
            data = json.loads(content)
            return data.get("last_post", "")
        else:
            print(f"Gist Read Error: {response.status_code}")
    except Exception as e:
        print(f"Gist Error: {e}")
    return ""

def save_new_post(text):
    """Update GitHub Gist"""
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        # Gist update format is specific
        payload = {
            "files": {
                "status.json": {
                    "content": json.dumps({"last_post": text})
                }
            }
        }
        requests.patch(url, headers=HEADERS, json=payload)
    except Exception as e:
        print(f"Gist Save Error: {e}")

def send_discord(text, link):
    print("🔔 Sending to Discord...")
    data = {
        "content": "🔔 **New Post**", 
        "embeds": [{
            "title": "🏛️ Click here to view on Facebook",
            "url": link,
            "description": text[:3500],
            "color": 3447003,
            "footer": {"text": "FSU Pulchowk • gaurabxkc"}
        }]
    }
    requests.post(DISCORD_WEBHOOK, json=data)

def run_bot():
    # Setup Headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        print(f"Checking {FACEBOOK_URL}...")
        driver.get(FACEBOOK_URL)
        
        # 1. Handle Login Popup
        try:
            close_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div[aria-label='Close']"))
            )
            close_btn.click()
        except:
            pass 

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(4) 

        # 2. Try to expand "See more"
        try:
            see_more = driver.find_elements(By.XPATH, "//div[contains(text(), 'See more')]")
            if see_more:
                driver.execute_script("arguments[0].click();", see_more[0])
                time.sleep(2)
        except:
            pass

        # 3. Find Posts
        posts = driver.find_elements(By.CSS_SELECTOR, "div[dir='auto']")
        
        if posts:
            latest_text = ""
            for p in posts:
                txt = p.text.strip()
                if len(txt) > 30: 
                    latest_text = txt
                    break 
            
            if latest_text:
                print(f"Latest Post: {latest_text[:50]}...")
                last_saved = get_last_saved_post()
                
                if latest_text[:50] != last_saved[:50]:
                    print("🚀 New content!")
                    send_discord(latest_text, FACEBOOK_URL)
                    save_new_post(latest_text)
                else:
                    print("💤 No updates.")
            else:
                print("No valid text found.")
        else:
            print("⚠️ HTML changed?")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_bot()
