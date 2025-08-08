import time
import random

def idle(driver):
    delay = random.uniform(2, 5)
    print(f"😴 Idling for {delay:.2f} seconds...")
    time.sleep(delay)
