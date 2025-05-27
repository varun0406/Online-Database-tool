import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def handle_cookie_consent(driver):
    try:
        # Common cookie consent button patterns for Science Direct
        cookie_buttons = [
            "Accept all cookies",
            "Accept Cookies",
            "I accept cookies",
            "Allow all cookies"
        ]
        
        for button_text in cookie_buttons:
            try:
                button = driver.find_element(By.XPATH, f"//*[contains(text(), '{button_text}')]")
                if button.is_displayed():
                    button.click()
                    print(f"Clicked '{button_text}' button")
                    time.sleep(5)
                    return True
            except Exception:
                continue
        
        # Try finding button by ID (Science Direct specific)
        try:
            button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
            if button.is_displayed():
                button.click()
                print("Clicked cookie accept button by ID")
                time.sleep(5)
                return True
        except Exception:
            pass
            
        return False
    except Exception as e:
        print(f"Error handling cookie consent: {e}")
        return False

def check_institution_access(driver, institution_name):
    try:
        # Ensure we're maximized before checking
        driver.maximize_window()
        time.sleep(5)  # Wait for any animations after maximizing
        
        # 1. Look for the institution button in the header
        try:
            institution_btn = driver.find_element(By.XPATH, "//button[contains(@class, 'gh-has-institution')]//span[contains(@class, 'button-link-text')]")
            if institution_name.lower() in institution_btn.text.lower():
                print(f"Institution '{institution_name}' found in Science Direct header button!")
                return True
        except Exception as e:
            print(f"Institution button not found or does not match: {e}")
        
        # 2. Try clicking user menu or profile buttons that might reveal institution name
        try:
            menu_buttons = driver.find_elements(By.XPATH, 
                "//*[contains(@class, 'user-menu') or contains(@class, 'profile') or contains(@class, 'institution')]")
            for button in menu_buttons:
                if button.is_displayed():
                    button.click()
                    print("Clicked potential menu button")
                    time.sleep(3)  # Wait for any dropdowns to appear
        except Exception as e:
            print(f"No menu buttons found or error clicking: {e}")
        
        # 3. Check specific elements where institution name might appear
        try:
            institution_elements = driver.find_elements(By.CLASS_NAME, "institution-name")
            for element in institution_elements:
                if institution_name.lower() in element.text.lower():
                    print(f"Institution '{institution_name}' found in institution element!")
                    return True
        except Exception:
            pass
            
        # 4. Check general page content again after potential menu clicks
        page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        if institution_name.lower() in page_text:
            print(f"Institution '{institution_name}' found on the page!")
            return True
        else:
            print(f"Institution name not found in page content")
            return False
            
    except Exception as e:
        print(f"Error checking institution access: {e}")
        return False

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
    url = "https://www.sciencedirect.com/"
    result = check_access(url)
    print(f"Access check result: {result}")
