import json
import os
import time
from selenium.webdriver.common.action_chains import ActionChains

def replay_mouse_path(driver):
    print("🖱️ Replaying mouse path...")

    path_file = "mouse_path.json"
    
    if not os.path.exists(path_file):
        print(f"⚠️ Mouse path file '{path_file}' not found.")
        return
    
    if os.stat(path_file).st_size == 0:
        print(f"⚠️ Mouse path file '{path_file}' is empty.")
        return

    with open(path_file, "r") as f:
        try:
            path = json.load(f)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON decode error: {e}")
            return

    actions = ActionChains(driver)
    for point in path:
        x, y = point.get("x"), point.get("y")
        if x is not None and y is not None:
            try:
                actions.move_by_offset(x, y).perform()
                time.sleep(0.01)
            except Exception as e:
                print(f"⚠️ Mouse move failed: {e}")
