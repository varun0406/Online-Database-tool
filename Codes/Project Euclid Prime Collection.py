import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

def detect_access_provided(driver, timeout=20):
    try:
        elem = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "accessByCopy"))
        )
        text = elem.text.strip().lower()
        if "access provided by" in text:
            print("Found 'Access provided by' message!")
            return True
        else:
            print("'Access provided by' message NOT found.")
            return False
    except Exception as e:
        print("Error while checking access message:", e)
        return False

def check_access(url, save_dir="downloaded_html"):
    os.makedirs(save_dir, exist_ok=True)
    safe_url = re.sub(r'[<>:"/\\|?*#]', '_', url.replace("https://", "").replace("http://", ""))
    filename = safe_url + ".html"
    filepath = os.path.join(save_dir, filename)
    options = Options()
    options.add_argument('--start-maximized')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    # options.add_argument('--headless')  # Uncomment to run headless
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined})
        """
    })
    try:
        driver.get(url)
        time.sleep(5)  # Wait for the page to load
        found = detect_access_provided(driver, timeout=20)
        # Save HTML for inspection
        html = driver.page_source
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Saved HTML to {filepath}")
        with open("results.csv", "a", encoding="utf-8") as log:
            log.write(f'"{url}","{filepath}",{found}\n')
        return 1 if found else 0
    except Exception as e:
        print(f"Error: {e}")
        return 0
    finally:
        driver.quit()

if __name__ == "__main__":
    url = "https://projecteuclid.org/"
    result = check_access(url)
    print(f"Access check result: {result}")
