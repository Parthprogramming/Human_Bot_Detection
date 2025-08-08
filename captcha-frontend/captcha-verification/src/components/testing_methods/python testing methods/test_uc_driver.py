import random, time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# --- launch a driver whose major version matches the local Chrome ---
driver = uc.Chrome(version_main=137)          # <-- adjust if you’ve updated Chrome
actions = ActionChains(driver)

try:
    driver.get("http://localhost:3000/")
    time.sleep(2)

    # ────────────────────────────────────────────────────────────────
    # 1) Scroll down as a human would: wheel + small pauses
    # ────────────────────────────────────────────────────────────────
    total_scroll = 500
    for delta in range(0, total_scroll, 60):
        driver.execute_script(f"window.scrollTo(0, {delta});")
        time.sleep(random.uniform(0.05, 0.25))

    # ────────────────────────────────────────────────────────────────
    # 2) Move cursor to the input, click to focus, then type
    # ────────────────────────────────────────────────────────────────
    input_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Enter USAI ID']")

    # smooth cursor glide to the centre of the field
    actions.move_to_element(input_field).pause(0.15).click().perform()

    username = "jupiter5002"
    for ch in username:
        actions.send_keys(ch).pause(random.uniform(0.1, 0.25))
    actions.perform()

    # ────────────────────────────────────────────────────────────────
    # 3) Hover to the submit button, click, linger a moment
    # ────────────────────────────────────────────────────────────────
    submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Verify')]")
    actions.move_to_element(submit_button).pause(0.2).click().perform()

    time.sleep(8)

finally:
    driver.quit()



# --------------------------------------------------------


"""
import random, time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# --- launch a driver whose major version matches the local Chrome ---
driver = uc.Chrome(version_main=137)          # <-- adjust if you’ve updated Chrome
actions = ActionChains(driver)

try:
    driver.get("http://localhost:3000/")
    time.sleep(2)

    # ────────────────────────────────────────────────────────────────
    # 1) Scroll down as a human would: wheel + small pauses
    # ────────────────────────────────────────────────────────────────
    total_scroll = 500
    for delta in range(0, total_scroll, 60):
        driver.execute_script(f"window.scrollTo(0, {delta});")
        time.sleep(random.uniform(0.05, 0.25))

    # ────────────────────────────────────────────────────────────────
    # 2) Move cursor to the input, click to focus, then type
    # ────────────────────────────────────────────────────────────────
    input_field = driver.find_element(By.Placeholder, "Enter USAI ID")

    # smooth cursor glide to the centre of the field
    actions.move_to_element(input_field).pause(0.15).click().perform()

    username = "jupiter5002"
    for ch in username:
        actions.send_keys(ch).pause(random.uniform(0.1, 0.25))
    actions.perform()

    # ────────────────────────────────────────────────────────────────
    # 3) Hover to the submit button, click, linger a moment
    # ────────────────────────────────────────────────────────────────
    submit_button = driver.find_element(By.ID, "tosubmitform")
    actions.move_to_element(submit_button).pause(0.2).click().perform()

    time.sleep(8)

finally:
    driver.quit()


"""