import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def wait_for_text(driver, keyword, timeout=30):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: keyword.lower() in d.find_element(By.TAG_NAME, "body").text.lower()
        )
        print(f"'{keyword}' found in visible page text!")
        return True
    except Exception as e:
        print(f"'{keyword}' NOT found in visible page text. Error: {e}")
        return False

def close_pressreader_popup(driver, timeout=15):
    try:
        # Wait for the popup to appear and find the close (X) button
        close_btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'modal')]//button[contains(@class, 'close') or @aria-label='Close' or @aria-label='close' or text()='×' or text()='✕']"))
        )
        close_btn.click()
        print("Closed PressReader popup.")
        time.sleep(2)
    except Exception as e:
        print(f"Popup close button not found or could not be clicked: {e}")

def wait_for_popup_with_text(driver, text, timeout=20):
    try:
        # Wait for any modal/popup to appear
        popup = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'modal') or contains(@class, 'popup') or contains(@class, 'HotSpot')]"))
        )
        # Check if the popup contains the target text
        if text.lower() in popup.text.lower():
            print(f"Popup with '{text}' detected!")
            return True
        else:
            print(f"Popup detected, but '{text}' not found in popup text.")
            print(popup.text)
            return False
    except Exception as e:
        print(f"Popup with '{text}' NOT detected. Error: {e}")
        return False

def detect_ahmedabad_university(driver, timeout=20):
    target_text = "Welcome to Ahmedabad University. Read or download your favorite titles via PressReader."
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: target_text.lower() in d.find_element(By.TAG_NAME, "body").text.lower()
        )
        print(f"Found the exact welcome message on the page!")
        return True
    except Exception as e:
        print(f"Exact welcome message NOT found on the page. Error: {e}")
        return False

def check_access(url, save_dir="downloaded_html"):
    """
    API function that checks if the given URL is accessible and returns:
    1 if running (accessible)
    0 if not running (not accessible)
    """
    os.makedirs(save_dir, exist_ok=True)
    filename = url.replace("https://", "").replace("http://", "").replace("/", "_") + ".html"
    filepath = os.path.join(save_dir, filename)
    options = Options()
    options.add_argument('--start-maximized')
    
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        time.sleep(10)  # Wait for the page to load
        found = detect_ahmedabad_university(driver, timeout=20)
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
    url = "https://www.pressreader.com/"
    result = check_access(url)
    print(f"Access check result: {result}")
