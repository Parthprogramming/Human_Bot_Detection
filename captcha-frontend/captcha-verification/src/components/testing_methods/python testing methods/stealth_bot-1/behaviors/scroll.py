import time
import random

def scroll(driver):
    print("🌀 Scrolling...")
    for _ in range(random.randint(5, 10)):
        driver.execute_script("window.scrollBy(0, arguments[0]);", random.randint(100, 300))
        time.sleep(random.uniform(0.3, 0.6))
