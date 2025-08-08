import random
import time
from selenium.webdriver.common.action_chains import ActionChains

def mouse_move(driver):
    print("🖱️ Simulating mouse movement...")

    actions = ActionChains(driver)
    
    # Get the window size to avoid going out of bounds
    window_size = driver.get_window_size()
    width = window_size['width']
    height = window_size['height']

    # Choose safe offsets (within visible window)
    x_offset = random.randint(10, width // 2)
    y_offset = random.randint(10, height // 2)

    try:
        actions.move_by_offset(x_offset, y_offset).perform()
        print(f"✅ Moved mouse by offset: ({x_offset}, {y_offset})")
    except Exception as e:
        print(f"⚠️ Failed to move mouse: {e}")
    
    time.sleep(random.uniform(0.5, 1.5))
