# reproduce.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# Setup headless Chrome
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

try:
    # 1. Load the evo.ninja app (adjust if hosted locally or via Docker)
    driver.get("http://localhost:3000")  # Replace with the actual URL if needed
    time.sleep(2)

    # 2. Select an existing chat with a goal
    chat_selector = driver.find_element(By.XPATH, "//div[contains(text(), 'Goal')]")  # Simplified selector
    chat_selector.click()
    time.sleep(1)

    # 3. Navigate to the root (e.g., home button or logo click)
    root_nav = driver.find_element(By.XPATH, "//a[contains(@href, '/')]")
    root_nav.click()
    time.sleep(1)

    # 4. Click on an example prompt
    prompt = driver.find_element(By.XPATH, "//div[contains(text(), 'Example Prompt')]")
    prompt.click()
    time.sleep(2)

    # 5. Check workspace file state
    workspace_files = driver.execute_script("return window.__STORE__?.workspace?.files || null;")
    print("Workspace files:", workspace_files)

    if not workspace_files:
        print("❌ Issue reproduced: Workspace files are not properly applied.")
    else:
        print("✅ Workspace files loaded:", workspace_files)

finally:
    driver.quit()
