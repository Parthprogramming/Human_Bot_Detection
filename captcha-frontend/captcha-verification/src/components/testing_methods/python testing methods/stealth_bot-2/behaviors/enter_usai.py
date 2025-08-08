import time
from selenium.webdriver.common.by import By
from config import CONFIG

def enter_usai_id(driver):
    try:
        # Find the input field using the CSS selector from config
        input_box = driver.find_element(By.CSS_SELECTOR, CONFIG["input_selector"])
        input_box.clear()
        input_box.send_keys(CONFIG["usai_id"])
        print(f"✅ USAI ID entered: {CONFIG['usai_id']}")
        time.sleep(0.5)

        # Find and click the verify button
        verify_button = driver.find_element(By.XPATH, CONFIG["verify_button_selector"])
        verify_button.click()
        print("✅ Verify button clicked")
        time.sleep(1)

    except Exception as e:
        print(f"❌ Error in entering USAI ID: {e}")
