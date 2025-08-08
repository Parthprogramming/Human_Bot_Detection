import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from config import CONFIG
from proxy_config import with_proxy
from fingerprint import inject_stealth_js
from human_mouse import replay_mouse_path
from behaviors.enter_usai import enter_usai_id
from behaviors import scroll
from behaviors import idle

# Optional CAPTCHA solver
try:
    from anticaptcha_solver import solve_recaptcha
except ImportError:
    solve_recaptcha = None

behaviors = [scroll, idle]  # mouse behavior handled in human_mouse.py


def random_user_agent():
    return random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.5735.91 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/92.0.4515.159 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/537.36"
    ])


def run_bot():
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--start-maximized")
    options.add_argument(f"--user-agent={random_user_agent()}")

    # Add proxy if configured
    with_proxy(options)

    driver = uc.Chrome(options=options, version_main=137)

    driver.get(CONFIG["url"])
    time.sleep(2)

    # Inject JS for stealth behavior
    inject_stealth_js(driver)

    # Mandatory USAI ID entry
    enter_usai_id(driver)

    # CAPTCHA solving if needed
    if CONFIG.get("use_captcha_solver") and solve_recaptcha:
        site_key = "your_site_key_here"  # update with actual
        token = solve_recaptcha(CONFIG["url"], site_key)
        driver.execute_script(
            'document.getElementById("g-recaptcha-response").innerHTML = arguments[0]', token)
        print("✅ CAPTCHA token injected")

    # Optional human mouse path replay
    replay_mouse_path(driver)

    # Randomized additional behaviors
    selected = random.sample(behaviors, k=random.randint(1, len(behaviors)))
    for behavior in selected:
        behavior(driver)

    time.sleep(2)
    try:
        driver.quit()
    except Exception:
        pass  # Handle WinError gracefully


if __name__ == "__main__":
    run_bot()
