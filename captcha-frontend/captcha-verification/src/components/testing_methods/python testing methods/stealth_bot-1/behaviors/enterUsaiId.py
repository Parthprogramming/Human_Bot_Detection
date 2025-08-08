import time 
from config import CONFIG
from selenium.webdriver.common.by import By


def enter_usai_id(driver):
    input_box = driver.find_element(By.CSS_SELECTOR, CONFIG["input_selector"])
    input_box.clear()
    input_box.send_keys(CONFIG["usai_id"])
    print(f"✅ USAI ID entered: {CONFIG['usai_id']}")
    time.sleep(0.5)

    verify_button = driver.find_element(By.XPATH, CONFIG["verify_button_selector"])
    verify_button.click()
    print("✅ Verify button clicked")
    time.sleep(1)
