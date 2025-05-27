import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def close_popup_if_present(driver, timeout=10):
    try:
        close_btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'modal') or contains(@class, 'popup')]//button[contains(@class, 'close') or @aria-label='Close' or @aria-label='close' or text()='×' or text()='✕' or text()='X']"))
        )
        close_btn.click()
        print("Closed popup.")
        time.sleep(1)
    except Exception as e:
        print(f"Popup close button not found or could not be clicked: {e}")

def detect_logged_in(driver, timeout=15):
    try:
        # Click the profile icon (avatar) using the new selector
        profile_icon = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "img.h-9.w-9.rounded-full.cursor-pointer"))
        )
        profile_icon.click()
        print("Clicked profile icon.")
        time.sleep(1)
        # Look for 'Logout' in the dropdown
        dropdown = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Logout') or contains(text(), 'logout') or contains(text(), 'LOGOUT')]"))
        )
        if dropdown:
            print("'Logout' found in profile dropdown. User is logged in.")
            return True
        else:
            print("'Logout' NOT found in profile dropdown.")
            return False
    except Exception as e:
        print(f"Profile or logout detection failed: {e}")
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
        time.sleep(5)  # Wait for the page to load
        close_popup_if_present(driver, timeout=10)
        found = detect_logged_in(driver, timeout=10)
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
    url = "https://www.ventureintelligence.com/setting/"
    result = check_access(url)
    print(f"Access check result: {result}")
