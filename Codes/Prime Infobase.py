import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def click_my_account(driver, timeout=10):
    try:
        my_account_btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'My Account')]"))
        )
        my_account_btn.click()
        print("Clicked 'My Account' button.")
        time.sleep(2)
    except Exception as e:
        print(f"'My Account' button not found or could not be clicked: {e}")

def detect_ahmedabad_university(driver, timeout=20):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: "Ahmedabad University" in d.find_element(By.TAG_NAME, "body").text
        )
        print("Found 'Ahmedabad University' on the page!")
        return True
    except Exception as e:
        print("'Ahmedabad University' NOT found on the page. Error:", e)
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
        click_my_account(driver, timeout=10)
        found = detect_ahmedabad_university(driver, timeout=10)
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
    url = "https://www.primeinfobase.com/index.aspx"

    result = check_access(url)
    print(f"Access check result: {result}")
