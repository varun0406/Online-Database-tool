import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import re

def sanitize_filename(url):
    """Convert URL to a valid filename by removing invalid characters"""
    # Remove protocol and replace invalid characters with underscore
    filename = re.sub(r'^https?://', '', url)
    filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
    # Limit filename length
    return filename[:200] + '.html'

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
    try:
        os.makedirs(save_dir, exist_ok=True)
        filename = sanitize_filename(url)
        filepath = os.path.join(save_dir, filename)
        
        options = Options()
        options.add_argument('--start-maximized')
        # options.add_argument('--headless')  # Run in headless mode
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        try:
            print(f"Accessing URL: {url}")
            driver.get(url)
            time.sleep(10)  # Wait for the page to load
            
            found = detect_ahmedabad_university(driver, timeout=20)
            
            # Save HTML for inspection
            html = driver.page_source
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"Saved HTML to {filepath}")
            
            # Log results
            with open("results.csv", "a", encoding="utf-8") as log:
                log.write(f'"{url}","{filepath}",{found}\n')
            
            return 1 if found else 0
            
        except Exception as e:
            print(f"Error during page access: {e}")
            return 0
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"Error in check_access: {e}")
        return 0

if __name__ == "__main__":
    url = "https://onlinelibrary.wiley.com/action/showPublications?pubType=journal&subject=management"
    result = check_access(url)
    print(f"Access check result: {result}")
