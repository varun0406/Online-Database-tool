import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

def detect_ip_based_user(driver, timeout=20):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: "ip-based-user-" in d.find_element(By.TAG_NAME, "body").text
        )
        print("Found 'ip-based-user-' on the page!")
        return True
    except Exception as e:
        print("'ip-based-user-' NOT found on the page. Error:", e)
        return False

def check_access(url, save_dir="downloaded_html"):
    """
    Checks if 'ip-based-user-' appears on the page.
    Returns 1 if found, 0 if not.
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
        found = detect_ip_based_user(driver, timeout=20)
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
    url = "https://economicoutlook.cmie.com/"
    result = check_access(url)
    print(f"Access check result: {result}")
