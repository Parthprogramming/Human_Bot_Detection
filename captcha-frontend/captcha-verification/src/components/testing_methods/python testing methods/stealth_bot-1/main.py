import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from config import CONFIG

# Import behavior modules
from behaviors.enterUsaiId import enter_usai_id
from behaviors.scroll import scroll
from behaviors.mouse_move import mouse_move
from behaviors.idle import idle

behaviors = [scroll, mouse_move, idle]

def run_bot():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument(f"--user-agent={random_user_agent()}")
    options.add_argument("--start-maximized")

    driver = uc.Chrome(version_main=137 , options=options)
    driver.get(CONFIG["url"])
    time.sleep(2)

    # Mandatory behavior
    enter_usai_id(driver)

    # Randomized additional behaviors
    selected = random.sample(behaviors, k=random.randint(1, len(behaviors)))
    for behavior in selected:
        behavior(driver)

    time.sleep(2)
    driver.quit()

def random_user_agent():
    return random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.5735.91 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/92.0.4515.159 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/537.36"
    ])

if __name__ == "__main__":
    run_bot()
