import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

def detect_ahduni(driver, timeout=20):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: "ahduni" in d.find_element(By.TAG_NAME, "body").text
        )
        print("Found 'ahduni' on the page!")
        return True
    except Exception as e:
        print("'ahduni' NOT found on the page. Error:", e)
        return False

def check_access(url, save_dir="downloaded_html"):
    """
    Automates clicking the login button and checks if 'ahduni' appears after login.
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
        time.sleep(3)  # Wait for page to load

        # Click the Login dropdown/button
        login_dropdown = driver.find_element(By.XPATH, "//a[contains(@class, 'dropdown-toggle') and contains(text(), 'Login')]")
        login_dropdown.click()
        time.sleep(1)

        # Click the Login button in the form
        login_btn = driver.find_element(By.ID, "btnLogin")
        login_btn.click()
        time.sleep(5)  # Wait for login to process and page to refresh

        found = detect_ahduni(driver, timeout=10)
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
    url = "https://epwrfits.in/Main_screen.aspx?userfeedback=true"
    result = check_access(url)
    print(f"Access check result: {result}")
