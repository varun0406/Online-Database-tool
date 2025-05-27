import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import re

def detect_ahmedabad_university_ip_access(driver, timeout=20):
    try:
        # Click the institution button to open the popover
        institution_btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="header-institution"]'))
        )
        institution_btn.click()
        print("Clicked institution button.")
        # Wait for the popover and check for the org text
        org_span = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-testid="current-org"]'))
        )
        if "ahmedabad university, ip access" in org_span.text.lower():
            print("Found 'Ahmedabad University, IP Access' in the popover!")
            return True
        else:
            print("Popover did not contain the expected text.")
            return False
    except Exception as e:
        print("'Ahmedabad University, IP Access' NOT found in the popover. Error:", e)
        return False

def check_access(url, save_dir="downloaded_html"):
    """
    Clicks the logo, then checks for 'Ahmedabad University, IP Access' on the page.
    Returns 1 if found, 0 if not.
    """
    os.makedirs(save_dir, exist_ok=True)
    safe_url = re.sub(r'[<>:"/\\\\|?*#]', '_', url.replace("https://", "").replace("http://", ""))
    filename = safe_url + ".html"
    filepath = os.path.join(save_dir, filename)
    
    options = Options()
    options.add_argument('--start-maximized')

    options.add_experimental_option("detach", True)  # Keep browser open
    driver = webdriver.Chrome(options=options)
    
    try:
        print("Opening URL...")
        driver.get(url)
        print("Waiting for page to load (10 seconds)...")
        time.sleep(10)  # Increased initial wait time

        # Try multiple approaches to find and click the logo
        try:
            # First try finding the logo by the specific SVG path
            logo = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//svg[@role='img']/path[@d='M84 98h10v10H12V98h10V52h14v46h10V52h14v46h10V52h14v46zM12 36.86l41-20.84 41 20.84V42H12v-5.14zM104 52V30.74L53 4.8 2 30.74V52h10v36H2v30h102V88H94V52h10z']"))
            )
            print("Found logo by SVG path, clicking...")
            actions = ActionChains(driver)
            actions.move_to_element(logo).click().perform()
        except Exception as e:
            print(f"First attempt failed: {e}")
            try:
                # Try finding by the specific class and structure
                logo_container = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.GlobalHeader-module__oN9fG svg[role='img']"))
                )
                print("Found logo by class structure, clicking...")
                actions = ActionChains(driver)
                actions.move_to_element(logo_container).click().perform()
            except Exception as e:
                print(f"Second attempt failed: {e}")
                try:
                    # Try finding by the organization text
                    org_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "span[data-testid='current-org']"))
                    )
                    print("Found organization text, clicking parent container...")
                    parent = org_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'GlobalHeader-module__')]")
                    actions = ActionChains(driver)
                    actions.move_to_element(parent).click().perform()
                except Exception as e:
                    print(f"Third attempt failed: {e}")
                    # Last resort: try clicking by coordinates
                    try:
                        print("Attempting to click by coordinates...")
                        actions = ActionChains(driver)
                        actions.move_by_offset(100, 50).click().perform()
                    except Exception as e:
                        print(f"All click attempts failed: {e}")

        print("Waiting after click (5 seconds)...")
        time.sleep(5)  # Wait after click

        found = detect_ahmedabad_university_ip_access(driver, timeout=15)
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

if __name__ == "__main__":
    url = "https://www.scopus.com/"
    result = check_access(url)
    print(f"Access check result: {result}")
