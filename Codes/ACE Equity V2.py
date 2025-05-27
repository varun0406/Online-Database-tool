import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

def detect_ahmedabad_university_logo(driver, timeout=20):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.find_element(By.XPATH, "//img[@src='https://www.acekp.in/wimtest/Working/web/103.233.171.34_crop_AU.jpg']")
        )
        print("Found AU logo image on the page!")
        return True
    except Exception as e:
        print("AU logo image NOT found on the page. Error:", e)
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
        found = detect_ahmedabad_university_logo(driver, timeout=20)
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
    url = "https://www.acekp.in/HomePage.aspx"
    result = check_access(url)
    print(f"Access check result: {result}")
