import datetime
import json
import pyautogui
import time
import webbrowser
import random
import sys
import os
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    TimeoutException, 
    ElementNotInteractableException, 
    MoveTargetOutOfBoundsException,
    InvalidSessionIdException,
    WebDriverException
)
import logging
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from retrying import retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        # logging.FileHandler('selenium_test.log'),
        logging.StreamHandler()
    ]
)

def debug_info():
    """Print debugging information about the environment"""
    print("\n=== Debug Information ===")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")
    print(f"PyAutoGUI version: {pyautogui.__version__}")
    print(f"Screen size: {pyautogui.size()}")
    print(f"Files in current directory: {os.listdir('.')}")
    
    # Check for Chrome/ChromeDriver
    try:
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        chrome_version = webdriver.Chrome().capabilities['chrome']['chromedriverVersion']
        print(f"ChromeDriver version: {chrome_version}")
    except Exception as e:
        print(f"ChromeDriver information not available: {str(e)}")
    
    print("=======================\n")

# Configure PyAutoGUI
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

class BotBehaviorTester:
    def __init__(self, browser_type='chrome'):
        self.browser_type = browser_type
        self.driver = None
        self.actions = ActionChains
        self.behavior_data = []
        
    def setup_driver(self):
        """Initialize the web driver based on browser type"""
        if self.browser_type.lower() == 'chrome':
            options = webdriver.ChromeOptions()
            options.add_argument('--start-maximized')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            self.driver = webdriver.Chrome(options=options)
        elif self.browser_type.lower() == 'firefox':
            self.driver = webdriver.Firefox()
        else:
            raise ValueError(f"Unsupported browser type: {self.browser_type}")
            
        # Set page load timeout
        self.driver.set_page_load_timeout(30)
        self.actions = ActionChains(self.driver)
        
    def record_behavior(self, action_type, details):
        """Record bot behavior for analysis"""
        timestamp = datetime.now().isoformat()
        behavior_entry = {
            'timestamp': timestamp,
            'action_type': action_type,
            'details': details
        }
        self.behavior_data.append(behavior_entry)
        
    def simulate_bot_behavior(self, url, num_attempts=5):
        """Simulate various bot-like behaviors"""
        try:
            self.setup_driver()
            logging.info(f"Starting bot behavior simulation with {num_attempts} attempts")
            
            for attempt in range(num_attempts):
                logging.info(f"Attempt {attempt + 1}/{num_attempts}")
                
                # Navigate to page
                self.driver.get(url)
                self.record_behavior('page_load', {'url': url})
                
                # Random mouse movements
                for _ in range(3):
                    x = random.randint(100, 700)
                    y = random.randint(100, 500)
                    self.actions.move_by_offset(x, y).perform()
                    self.record_behavior('mouse_movement', {'x': x, 'y': y})
                    time.sleep(random.uniform(0.1, 0.3))
                    
                print("Scrolling the page vertically before filling form...")
                driver.execute_script("window.scrollBy(0, 400);")  # Scroll down 400px
                time.sleep(1.5)  # Allow frontend to detect scroll

                
                # Find and interact with input field
                try:
                    input_field = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Enter USAI ID']"))
                    )
                    
                    # Rapid typing
                    text = "HelloABC123"
                    input_field.clear()
                    for char in text:
                        input_field.send_keys(char)
                        time.sleep(random.uniform(0.01, 0.05))
                    self.record_behavior('typing', {'text': text})
                    
                    # Find and click verify button
                    verify_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Verify')]"))
                    )
                    verify_button.click()
                    self.record_behavior('button_click', {'button': 'verify'})
                    
                    # Wait for response
                    time.sleep(2)
                    
                except Exception as e:
                    logging.error(f"Error during attempt {attempt + 1}: {str(e)}")
                    self.record_behavior('error', {'error': str(e)})
                
                # Random delay between attempts
                time.sleep(random.uniform(1, 3))
            
            # Save behavior data
            self.save_behavior_data()
            
        except Exception as e:
            logging.error(f"Critical error: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()
                
    def save_behavior_data(self):
        """Save recorded behavior data to a JSON file"""
        filename = f"bot_behavior_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(self.behavior_data, f, indent=2)
        logging.info(f"Behavior data saved to {filename}")

def get_safe_coordinates(driver):
    """Get safe coordinates within the viewport"""
    viewport_width = driver.execute_script("return window.innerWidth;")
    viewport_height = driver.execute_script("return window.innerHeight;")
    # Keep coordinates within 80% of viewport to ensure they're visible
    safe_x = random.randint(int(viewport_width * 0.1), int(viewport_width * 0.9))
    safe_y = random.randint(int(viewport_height * 0.1), int(viewport_height * 0.9))
    return safe_x, safe_y

def create_driver():
    """Create a new Chrome driver with proper options"""
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-browser-side-navigation')
        options.add_argument('--disable-site-isolation-trials')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--window-size=1920,1080')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Add performance logging
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL', 'performance': 'ALL'})
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        driver.set_window_size(1920, 1080)
        driver.set_window_position(0, 0)
        return driver
    except Exception as e:
        logging.error(f"Error creating driver: {str(e)}")
        raise

def check_window_state(driver):
    """Check if the browser window is still open and responsive"""
    try:
        # Try a simple operation to check window state
        driver.current_url
        return True
    except Exception:
        return False

def ensure_window_open(driver):
    """Ensure the browser window is open and responsive"""
    if not check_window_state(driver):
        logging.warning("Browser window not responsive, attempting to recover...")
        try:
            # Try to get a new window handle
            driver.switch_to.window(driver.window_handles[0])
            return True
        except Exception as e:
            logging.error(f"Could not recover window: {str(e)}")
            return False
    return True

def safe_get_page_source(driver):
    """Safely get page source with retry logic"""
    try:
        return driver.page_source
    except Exception as e:
        logging.error(f"Error getting page source: {str(e)}")
        return "Could not get page source"

def wait_for_element_interactable(driver, selectors, timeout=10):
    """Wait for any of the given selectors to be interactable"""
    print(f"\nTrying to find element with selectors: {selectors}")
    start_time = time.time()
    last_error = None
    
    # First, wait for the page to be fully loaded
    try:
        WebDriverWait(driver, 5).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        # Additional wait for React to initialize
        time.sleep(2)
    except Exception as e:
        print(f"Error waiting for page load: {str(e)}")
    
    while time.time() - start_time < timeout:
        for selector in selectors:
            try:
                print(f"\nTrying selector: {selector}")
                # First check if element exists
                element = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                print(f"Element found with selector: {selector}")
                
                # Try to make element visible if it's not
                try:
                    if not element.is_displayed():
                        print("Element not visible, attempting to make it visible...")
                        # Try to scroll element into view
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", element)
                        # Try to remove any overlays
                        driver.execute_script("""
                            var overlays = document.querySelectorAll('div[style*="position: absolute"], div[style*="position:fixed"]');
                            overlays.forEach(function(overlay) {
                                if (overlay.contains(arguments[0])) {
                                    overlay.style.display = 'none';
                                }
                            });
                        """, element)
                        time.sleep(1)
                
                    # Check if element is visible after attempts
                    if not element.is_displayed():
                        print(f"Element still not visible: {selector}")
                        continue
                except Exception as e:
                    print(f"Error making element visible: {str(e)}")
                
                # Check if element is enabled
                if not element.is_enabled():
                    print(f"Element found but not enabled: {selector}")
                    continue
                
                # Try to get element properties
                try:
                    print(f"Element properties:")
                    print(f"- Tag name: {element.tag_name}")
                    print(f"- Class: {element.get_attribute('class')}")
                    print(f"- ID: {element.get_attribute('id')}")
                    print(f"- Type: {element.get_attribute('type')}")
                    print(f"- Value: {element.get_attribute('value')}")
                    print(f"- Is displayed: {element.is_displayed()}")
                    print(f"- Is enabled: {element.is_enabled()}")
                    print(f"- Location: {element.location}")
                    print(f"- Size: {element.size}")
                    print(f"- Style: {element.get_attribute('style')}")
                    print(f"- Parent: {element.find_element(By.XPATH, '..').get_attribute('outerHTML')}")
                except Exception as e:
                    print(f"Could not get all element properties: {str(e)}")
                
                # Try to scroll element into view
                try:
                    driver.execute_script("""
                        arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});
                        // Remove any fixed position elements that might be overlaying
                        var overlays = document.querySelectorAll('div[style*="position: fixed"]');
                        overlays.forEach(function(overlay) {
                            if (overlay.contains(arguments[0])) {
                                overlay.style.display = 'none';
                            }
                        });
                    """, element)
                    print("Scrolled element into view and removed overlays")
                    time.sleep(1)
                except Exception as e:
                    print(f"Could not scroll element into view: {str(e)}")
                
                # Additional wait for element to be clickable
                try:
                    element = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    print(f"Element is clickable: {selector}")
                    return element
                except Exception as e:
                    print(f"Element found but not clickable: {str(e)}")
                    continue
                    
            except Exception as e:
                last_error = e
                print(f"Error with selector {selector}: {str(e)}")
                continue
        
        print("\nWaiting before retry...")
        time.sleep(1)
    
    if last_error:
        print(f"\nLast error encountered: {str(last_error)}")
    print("\nElement not found or not interactable after all attempts")
    return None

def simulate_human_behavior():
    driver = None
    try:
        print("Starting human-like behavior test...")
        
        # Create driver with retry logic
        for attempt in range(3):
            try:
                driver = create_driver()
                break
            except Exception as e:
                if attempt == 2:  # Last attempt
                    raise
                print(f"Failed to create driver (attempt {attempt + 1}/3): {str(e)}")
                time.sleep(2)
        
        actions = ActionChains(driver)
        
        print("\nOpening browser...")
        driver.get('http://localhost:3000')
        
        # Wait for page to be fully loaded
        print("\nWaiting for page to load...")
        try:
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            print("Page load complete")
        except Exception as e:
            print(f"Error waiting for page load: {str(e)}")
        
        # Additional wait for React to initialize
        print("Waiting for React to initialize...")
        time.sleep(3)
        
        # Verify page is loaded and window is responsive
        if not ensure_window_open(driver):
            raise Exception("Browser window not responsive after page load")
        
        print("Scrolling the page vertically before filling form...")
        driver.execute_script("window.scrollBy(0, 400);")  # Scroll down 400px
        time.sleep(1.5)  # Allow frontend to detect scroll

        
        # Print page information
        try:
            print("\nPage Information:")
            print(f"Title: {driver.title}")
            print(f"Current URL: {driver.current_url}")
            print("\nPage source preview:")
            print(driver.page_source[:1000] + "...")
            
            # Try to find any forms on the page
            forms = driver.find_elements(By.TAG_NAME, "form")
            print(f"\nFound {len(forms)} forms on the page")
            for idx, form in enumerate(forms):
                try:
                    print(f"\nForm {idx + 1}:")
                    print(f"- ID: {form.get_attribute('id')}")
                    print(f"- Class: {form.get_attribute('class')}")
                    print(f"- Action: {form.get_attribute('action')}")
                    print(f"- Method: {form.get_attribute('method')}")
                    print("Form HTML:")
                    print(form.get_attribute('outerHTML'))
                except Exception as e:
                    print(f"Error getting form properties: {str(e)}")
            
        except Exception as e:
            print(f"Error getting page information: {str(e)}")
        
        print("\nLooking for input field...")
        # Try multiple possible selectors for the input field
        input_selectors = [
            "input[placeholder='Enter USAI ID']",  # Primary selector - by placeholder
            "input[type='text']",  # Fallback - by type
            "form input",  # Fallback - any input in a form
            "input",  # Last resort - any input
            "[data-testid='captcha-input']"  # Optional - by test ID if present
        ]
        
        # Ensure window is still open before looking for elements
        if not ensure_window_open(driver):
            raise Exception("Browser window closed before element search")
            
        # Print all input elements on the page for debugging
        try:
            print("\nAll input elements on page:")
            inputs = driver.find_elements(By.TAG_NAME, "input")
            for idx, input_elem in enumerate(inputs):
                try:
                    print(f"\nInput {idx + 1}:")
                    print(f"- Type: {input_elem.get_attribute('type')}")
                    print(f"- Class: {input_elem.get_attribute('class')}")
                    print(f"- ID: {input_elem.get_attribute('id')}")
                    print(f"- Name: {input_elem.get_attribute('name')}")
                    print(f"- Placeholder: {input_elem.get_attribute('placeholder')}")
                    print(f"- Is displayed: {input_elem.is_displayed()}")
                    print(f"- Is enabled: {input_elem.is_enabled()}")
                    print(f"- Location: {input_elem.location}")
                    print(f"- Size: {input_elem.size}")
                    print(f"- Parent HTML: {input_elem.find_element(By.XPATH, '..').get_attribute('outerHTML')}")
                except Exception as e:
                    print(f"Could not get input element properties: {str(e)}")
        except Exception as e:
            print(f"Error finding input elements: {str(e)}")
            
        input_field = wait_for_element_interactable(driver, input_selectors)
        
        if input_field:
            print("\nMoving to input field...")
            try:
                if not ensure_window_open(driver):
                    raise Exception("Browser window closed before input field interaction")
                
                # Try multiple methods to interact with the input field
                try:
                    # Method 1: JavaScript click and focus
                    driver.execute_script("""
                        arguments[0].click();
                        arguments[0].focus();
                        // Remove any overlays
                        var overlays = document.querySelectorAll('div[style*="position: fixed"], div[style*="position: absolute"]');
                        overlays.forEach(function(overlay) {
                            if (overlay.contains(arguments[0])) {
                                overlay.style.display = 'none';
                            }
                        });
                    """, input_field)
                    print("Clicked and focused input field using JavaScript")
                except Exception as e:
                    print(f"JavaScript click failed: {str(e)}")
                    try:
                        # Method 2: ActionChains
                        actions.move_to_element(input_field).click().perform()
                        print("Clicked input field using ActionChains")
                    except Exception as e:
                        print(f"ActionChains click failed: {str(e)}")
                        try:
                            # Method 3: Direct click
                            input_field.click()
                            print("Clicked input field directly")
                        except Exception as e:
                            print(f"Direct click failed: {str(e)}")
                
                print("\nTyping text...")
                text = "HelloABC123"
                for char in text:
                    if not ensure_window_open(driver):
                        raise Exception("Browser window closed during typing")
                    try:
                        # Try multiple methods to send keys
                        try:
                            input_field.send_keys(char)
                        except Exception as e:
                            print(f"send_keys failed: {str(e)}")
                            try:
                                # Try JavaScript
                                driver.execute_script(f"""
                                    arguments[0].value += '{char}';
                                    arguments[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    arguments[0].dispatchEvent(new Event('change', {{ bubbles: true }}));
                                """, input_field)
                            except Exception as e:
                                print(f"JavaScript value setting failed: {str(e)}")
                                raise
                        time.sleep(random.uniform(0.1, 0.3))
                    except Exception as e:
                        print(f"Error typing character '{char}': {str(e)}")
                        raise
                print("Finished typing")
                
                print("\nLooking for verify button...")
                if not ensure_window_open(driver):
                    raise Exception("Browser window closed before button search")
                
                # Print all buttons on the page for debugging
                try:
                    print("\nAll buttons on page:")
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    for idx, button in enumerate(buttons):
                        try:
                            print(f"\nButton {idx + 1}:")
                            print(f"- Text: {button.text}")
                            print(f"- Type: {button.get_attribute('type')}")
                            print(f"- Class: {button.get_attribute('class')}")
                            print(f"- ID: {button.get_attribute('id')}")
                            print(f"- Name: {button.get_attribute('name')}")
                            print(f"- Is displayed: {button.is_displayed()}")
                            print(f"- Is enabled: {button.is_enabled()}")
                            print(f"- Location: {button.location}")
                            print(f"- Size: {button.size}")
                            print(f"- Parent HTML: {button.find_element(By.XPATH, '..').get_attribute('outerHTML')}")
                        except Exception as e:
                            print(f"Could not get button properties: {str(e)}")
                except Exception as e:
                    print(f"Error finding buttons: {str(e)}")

                # Try multiple possible selectors for the verify button
                button_selectors = [
                    "button:not([disabled])",  # Any enabled button
                    "button",  # Any button as fallback
                    "input[type='submit']",  # Submit input as fallback
                    "form button"  # Any button in a form
                ]
                
                verify_button = wait_for_element_interactable(driver, button_selectors)
                
                if verify_button:
                    print("\nMoving to verify button...")
                    try:
                        if not ensure_window_open(driver):
                            raise Exception("Browser window closed before button click")
                        
                        # Try to make button visible and clickable
                        try:
                            driver.execute_script("""
                                arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});
                                var overlays = document.querySelectorAll('div[style*="position: fixed"], div[style*="position: absolute"]');
                                overlays.forEach(function(overlay) {
                                    if (overlay.contains(arguments[0])) {
                                        overlay.style.display = 'none';
                                    }
                                });
                            """, verify_button)
                            print("Prepared button for clicking")
                            time.sleep(1)
                        except Exception as e:
                            print(f"Error preparing button: {str(e)}")
                        
                        # Try multiple methods to click the button
                        clicked = False
                        
                        # Verify it's the correct button by checking text
                        button_text = verify_button.text.strip()
                        if not button_text or 'verify' not in button_text.lower():
                            print(f"Found button but text doesn't match: '{button_text}'")
                            # Try to find button specifically by text
                            try:
                                verify_button = driver.find_element(By.XPATH, "//button[contains(translate(text(), 'VERIFY', 'verify'), 'verify')]")
                                print("Found button by text content")
                            except Exception as e:
                                print(f"Could not find button by text: {str(e)}")
                        
                        # Method 1: JavaScript click with event dispatch
                        try:
                            driver.execute_script("""
                                arguments[0].click();
                                arguments[0].dispatchEvent(new MouseEvent('click', {
                                    bubbles: true,
                                    cancelable: true,
                                    view: window
                                }));
                            """, verify_button)
                            print("Clicked button using JavaScript with events")
                            clicked = True
                        except Exception as e:
                            print(f"JavaScript click failed: {str(e)}")
                        
                        # Method 2: ActionChains
                        if not clicked:
                            try:
                                actions.move_to_element(verify_button)
                                actions.click()
                                actions.perform()
                                print("Clicked button using ActionChains")
                                clicked = True
                            except Exception as e:
                                print(f"ActionChains click failed: {str(e)}")
                        
                        # Method 3: Direct click
                        if not clicked:
                            try:
                                verify_button.click()
                                print("Clicked button directly")
                                clicked = True
                            except Exception as e:
                                print(f"Direct click failed: {str(e)}")
                        
                        # Method 4: Form submit
                        if not clicked:
                            try:
                                form = verify_button.find_element(By.XPATH, "./ancestor::form")
                                driver.execute_script("arguments[0].submit();", form)
                                print("Submitted form containing button")
                                clicked = True
                            except Exception as e:
                                print(f"Form submit failed: {str(e)}")
                        
                        if clicked:
                            print("Button click successful!")
                            time.sleep(20)
                            try:
                                print("\nPage after button click:")
                                print(f"Current URL: {driver.current_url}")
                                print(f"Page title: {driver.title}")
                                messages = driver.find_elements(By.CSS_SELECTOR, ".alert, .message, .error, .success, .notification")
                                for msg in messages:
                                    print(f"Found message: {msg.text}")
                            except Exception as e:
                                print(f"Error checking page after click: {str(e)}")
                        else:
                            print("All click methods failed!")
                            
                    except Exception as e:
                        print(f"Error during button interaction: {str(e)}")
                        if ensure_window_open(driver):
                            try:
                                page_source = safe_get_page_source(driver)
                                print("\nPage source after error:")
                                print(page_source[:500] + "...")
                            except Exception as e:
                                print(f"Could not get page source: {str(e)}")
                else:
                    print("Verify button not found or not interactable!")
                    if ensure_window_open(driver):
                        try:
                            page_source = safe_get_page_source(driver)
                            print("\nPage source:")
                            print(page_source[:500] + "...")
                        except Exception as e:
                            print(f"Could not get page source: {str(e)}")
            except Exception as e:
                print(f"Error during interaction: {str(e)}")
                if ensure_window_open(driver):
                    try:
                        page_source = safe_get_page_source(driver)
                        print("\nPage source:")
                        print(page_source[:500] + "...")
                    except Exception as e:
                        print(f"Could not get page source: {str(e)}")
        else:
            print("Input field not found or not interactable!")
            if ensure_window_open(driver):
                try:
                    page_source = safe_get_page_source(driver)
                    print("\nPage source:")
                    print(page_source[:500] + "...")
                except Exception as e:
                    print(f"Could not get page source: {str(e)}")
            
    except Exception as e:
        print("\n=== Error Details ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        print("===================\n")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass



def main():
    # Example usage
    tester = BotBehaviorTester(browser_type='chrome')
    tester.simulate_bot_behavior('http://localhost:3000', num_attempts=5)

if __name__ == "__main__":
    # Print debug information
    debug_info()
    
    # Ask user which test to run
    print("Choose test type:")
    print("1. Human-like behavior")
    print("2. Bot-like behavior")
    choice = 1
    simulate_human_behavior()


# import datetime
# import json
# import pyautogui
# import time
# import webbrowser
# import random
# import sys
# import os
# import traceback
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.action_chains import ActionChains
# from selenium.common.exceptions import (
#     TimeoutException, 
#     ElementNotInteractableException, 
#     MoveTargetOutOfBoundsException,
#     InvalidSessionIdException,
#     WebDriverException
# )
# import logging
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from retrying import retry

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         # logging.FileHandler('selenium_test.log'),
#         logging.StreamHandler()
#     ]
# )

# def debug_info():
#     """Print debugging information about the environment"""
#     print("\n=== Debug Information ===")
#     print(f"Current directory: {os.getcwd()}")
#     print(f"Python version: {sys.version}")
#     print(f"PyAutoGUI version: {pyautogui.__version__}")
#     print(f"Screen size: {pyautogui.size()}")
#     print(f"Files in current directory: {os.listdir('.')}")
    
#     # Check for Chrome/ChromeDriver
#     try:
#         from selenium.webdriver.chrome.service import Service
#         from webdriver_manager.chrome import ChromeDriverManager
#         chrome_version = webdriver.Chrome().capabilities['chrome']['chromedriverVersion']
#         print(f"ChromeDriver version: {chrome_version}")
#     except Exception as e:
#         print(f"ChromeDriver information not available: {str(e)}")
    
#     print("=======================\n")

# # Configure PyAutoGUI
# pyautogui.FAILSAFE = True
# pyautogui.PAUSE = 0.5

# class BotBehaviorTester:
#     def __init__(self, browser_type='chrome'):
#         self.browser_type = browser_type
#         self.driver = None
#         self.actions = ActionChains
#         self.behavior_data = []
        
#     def setup_driver(self):
#         """Initialize the web driver based on browser type"""
#         if self.browser_type.lower() == 'chrome':
#             options = webdriver.ChromeOptions()
#             options.add_argument('--start-maximized')
#             options.add_argument('--disable-blink-features=AutomationControlled')
#             options.add_argument('--disable-dev-shm-usage')
#             options.add_argument('--no-sandbox')
#             options.add_experimental_option("excludeSwitches", ["enable-automation"])
#             options.add_experimental_option('useAutomationExtension', False)
#             self.driver = webdriver.Chrome(options=options)
#         elif self.browser_type.lower() == 'firefox':
#             self.driver = webdriver.Firefox()
#         else:
#             raise ValueError(f"Unsupported browser type: {self.browser_type}")
            
#         # Set page load timeout
#         self.driver.set_page_load_timeout(30)
#         self.actions = ActionChains(self.driver)
        
#     def record_behavior(self, action_type, details):
#         """Record bot behavior for analysis"""
#         timestamp = datetime.now().isoformat()
#         behavior_entry = {
#             'timestamp': timestamp,
#             'action_type': action_type,
#             'details': details
#         }
#         self.behavior_data.append(behavior_entry)
        
#     def simulate_bot_behavior(self, url, num_attempts=5):
#         """Simulate various bot-like behaviors"""
#         try:
#             self.setup_driver()
#             logging.info(f"Starting bot behavior simulation with {num_attempts} attempts")
            
#             for attempt in range(num_attempts):
#                 logging.info(f"Attempt {attempt + 1}/{num_attempts}")
                
#                 # Navigate to page
#                 self.driver.get(url)
#                 self.record_behavior('page_load', {'url': url})
                
#                 # Random mouse movements
#                 for _ in range(3):
#                     x = random.randint(100, 700)
#                     y = random.randint(100, 500)
#                     self.actions.move_by_offset(x, y).perform()
#                     self.record_behavior('mouse_movement', {'x': x, 'y': y})
#                     time.sleep(random.uniform(0.1, 0.3))
                    
#                 print("Scrolling the page vertically before filling form...")
#                 driver.execute_script("window.scrollBy(0, 400);")  # Scroll down 400px
#                 time.sleep(1.5)  # Allow frontend to detect scroll

                
#                 # Find and interact with input field
#                 try:
#                     input_field = WebDriverWait(self.driver, 10).until(
#                         EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
#                     )
                    
#                     # Rapid typing
#                     text = "HelloABC123"
#                     input_field.clear()
#                     for char in text:
#                         input_field.send_keys(char)
#                         time.sleep(random.uniform(0.01, 0.05))
#                     self.record_behavior('typing', {'text': text})
                    
#                     # Find and click verify button
#                     verify_button = WebDriverWait(self.driver, 10).until(
#                         EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
#                     )
#                     verify_button.click()
#                     self.record_behavior('button_click', {'button': 'verify'})
                    
#                     # Wait for response
#                     time.sleep(2)
                    
#                 except Exception as e:
#                     logging.error(f"Error during attempt {attempt + 1}: {str(e)}")
#                     self.record_behavior('error', {'error': str(e)})
                
#                 # Random delay between attempts
#                 time.sleep(random.uniform(1, 3))
            
#             # Save behavior data
#             self.save_behavior_data()
            
#         except Exception as e:
#             logging.error(f"Critical error: {str(e)}")
#         finally:
#             if self.driver:
#                 self.driver.quit()
                
#     def save_behavior_data(self):
#         """Save recorded behavior data to a JSON file"""
#         filename = f"bot_behavior_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
#         with open(filename, 'w') as f:
#             json.dump(self.behavior_data, f, indent=2)
#         logging.info(f"Behavior data saved to {filename}")

# def get_safe_coordinates(driver):
#     """Get safe coordinates within the viewport"""
#     viewport_width = driver.execute_script("return window.innerWidth;")
#     viewport_height = driver.execute_script("return window.innerHeight;")
#     # Keep coordinates within 80% of viewport to ensure they're visible
#     safe_x = random.randint(int(viewport_width * 0.1), int(viewport_width * 0.9))
#     safe_y = random.randint(int(viewport_height * 0.1), int(viewport_height * 0.9))
#     return safe_x, safe_y

# def create_driver():
#     """Create a new Chrome driver with proper options"""
#     try:
#         options = webdriver.ChromeOptions()
#         options.add_argument('--start-maximized')
#         options.add_argument('--disable-blink-features=AutomationControlled')
#         options.add_argument('--disable-dev-shm-usage')
#         options.add_argument('--no-sandbox')
#         options.add_argument('--disable-gpu')
#         options.add_argument('--disable-extensions')
#         options.add_argument('--disable-popup-blocking')
#         options.add_argument('--disable-notifications')
#         options.add_argument('--disable-infobars')
#         options.add_argument('--disable-browser-side-navigation')
#         options.add_argument('--disable-site-isolation-trials')
#         options.add_argument('--ignore-certificate-errors')
#         options.add_argument('--allow-running-insecure-content')
#         options.add_argument('--window-size=1920,1080')
#         options.add_experimental_option("excludeSwitches", ["enable-automation"])
#         options.add_experimental_option('useAutomationExtension', False)
        
#         # Add performance logging
#         options.set_capability('goog:loggingPrefs', {'browser': 'ALL', 'performance': 'ALL'})
        
#         service = Service(ChromeDriverManager().install())
#         driver = webdriver.Chrome(service=service, options=options)
#         driver.set_page_load_timeout(30)
#         driver.set_window_size(1920, 1080)
#         driver.set_window_position(0, 0)
#         return driver
#     except Exception as e:
#         logging.error(f"Error creating driver: {str(e)}")
#         raise

# def check_window_state(driver):
#     """Check if the browser window is still open and responsive"""
#     try:
#         # Try a simple operation to check window state
#         driver.current_url
#         return True
#     except Exception:
#         return False

# def ensure_window_open(driver):
#     """Ensure the browser window is open and responsive"""
#     if not check_window_state(driver):
#         logging.warning("Browser window not responsive, attempting to recover...")
#         try:
#             # Try to get a new window handle
#             driver.switch_to.window(driver.window_handles[0])
#             return True
#         except Exception as e:
#             logging.error(f"Could not recover window: {str(e)}")
#             return False
#     return True

# def safe_get_page_source(driver):
#     """Safely get page source with retry logic"""
#     try:
#         return driver.page_source
#     except Exception as e:
#         logging.error(f"Error getting page source: {str(e)}")
#         return "Could not get page source"

# def wait_for_element_interactable(driver, selectors, timeout=10):
#     """Wait for any of the given selectors to be interactable"""
#     print(f"\nTrying to find element with selectors: {selectors}")
#     start_time = time.time()
#     last_error = None
    
#     # First, wait for the page to be fully loaded
#     try:
#         WebDriverWait(driver, 5).until(
#             lambda d: d.execute_script('return document.readyState') == 'complete'
#         )
#         # Additional wait for React to initialize
#         time.sleep(2)
#     except Exception as e:
#         print(f"Error waiting for page load: {str(e)}")
    
#     while time.time() - start_time < timeout:
#         for selector in selectors:
#             try:
#                 print(f"\nTrying selector: {selector}")
#                 # First check if element exists
#                 element = WebDriverWait(driver, 2).until(
#                     EC.presence_of_element_located((By.CSS_SELECTOR, selector))
#                 )
#                 print(f"Element found with selector: {selector}")
                
#                 # Try to make element visible if it's not
#                 try:
#                     if not element.is_displayed():
#                         print("Element not visible, attempting to make it visible...")
#                         # Try to scroll element into view
#                         driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", element)
#                         # Try to remove any overlays
#                         driver.execute_script("""
#                             var overlays = document.querySelectorAll('div[style*="position: absolute"], div[style*="position:fixed"]');
#                             overlays.forEach(function(overlay) {
#                                 if (overlay.contains(arguments[0])) {
#                                     overlay.style.display = 'none';
#                                 }
#                             });
#                         """, element)
#                         time.sleep(1)
                
#                     # Check if element is visible after attempts
#                     if not element.is_displayed():
#                         print(f"Element still not visible: {selector}")
#                         continue
#                 except Exception as e:
#                     print(f"Error making element visible: {str(e)}")
                
#                 # Check if element is enabled
#                 if not element.is_enabled():
#                     print(f"Element found but not enabled: {selector}")
#                     continue
                
#                 # Try to get element properties
#                 try:
#                     print(f"Element properties:")
#                     print(f"- Tag name: {element.tag_name}")
#                     print(f"- Class: {element.get_attribute('class')}")
#                     print(f"- ID: {element.get_attribute('id')}")
#                     print(f"- Type: {element.get_attribute('type')}")
#                     print(f"- Value: {element.get_attribute('value')}")
#                     print(f"- Is displayed: {element.is_displayed()}")
#                     print(f"- Is enabled: {element.is_enabled()}")
#                     print(f"- Location: {element.location}")
#                     print(f"- Size: {element.size}")
#                     print(f"- Style: {element.get_attribute('style')}")
#                     print(f"- Parent: {element.find_element(By.XPATH, '..').get_attribute('outerHTML')}")
#                 except Exception as e:
#                     print(f"Could not get all element properties: {str(e)}")
                
#                 # Try to scroll element into view
#                 try:
#                     driver.execute_script("""
#                         arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});
#                         // Remove any fixed position elements that might be overlaying
#                         var overlays = document.querySelectorAll('div[style*="position: fixed"]');
#                         overlays.forEach(function(overlay) {
#                             if (overlay.contains(arguments[0])) {
#                                 overlay.style.display = 'none';
#                             }
#                         });
#                     """, element)
#                     print("Scrolled element into view and removed overlays")
#                     time.sleep(1)
#                 except Exception as e:
#                     print(f"Could not scroll element into view: {str(e)}")
                
#                 # Additional wait for element to be clickable
#                 try:
#                     element = WebDriverWait(driver, 2).until(
#                         EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
#                     )
#                     print(f"Element is clickable: {selector}")
#                     return element
#                 except Exception as e:
#                     print(f"Element found but not clickable: {str(e)}")
#                     continue
                    
#             except Exception as e:
#                 last_error = e
#                 print(f"Error with selector {selector}: {str(e)}")
#                 continue
        
#         print("\nWaiting before retry...")
#         time.sleep(1)
    
#     if last_error:
#         print(f"\nLast error encountered: {str(last_error)}")
#     print("\nElement not found or not interactable after all attempts")
#     return None

# def simulate_human_behavior():
#     driver = None
#     try:
#         print("Starting human-like behavior test...")
        
#         # Create driver with retry logic
#         for attempt in range(3):
#             try:
#                 driver = create_driver()
#                 break
#             except Exception as e:
#                 if attempt == 2:  # Last attempt
#                     raise
#                 print(f"Failed to create driver (attempt {attempt + 1}/3): {str(e)}")
#                 time.sleep(2)
        
#         actions = ActionChains(driver)
        
#         print("\nOpening browser...")
#         driver.get('http://localhost:3000')
        
#         # Wait for page to be fully loaded
#         print("\nWaiting for page to load...")
#         try:
#             WebDriverWait(driver, 10).until(
#                 lambda d: d.execute_script('return document.readyState') == 'complete'
#             )
#             print("Page load complete")
#         except Exception as e:
#             print(f"Error waiting for page load: {str(e)}")
        
#         # Additional wait for React to initialize
#         print("Waiting for React to initialize...")
#         time.sleep(3)
        
#         # Verify page is loaded and window is responsive
#         if not ensure_window_open(driver):
#             raise Exception("Browser window not responsive after page load")
        
#         print("Scrolling the page vertically before filling form...")
#         driver.execute_script("window.scrollBy(0, 400);")  # Scroll down 400px
#         time.sleep(1.5)  # Allow frontend to detect scroll

        
#         # Print page information
#         try:
#             print("\nPage Information:")
#             print(f"Title: {driver.title}")
#             print(f"Current URL: {driver.current_url}")
#             print("\nPage source preview:")
#             print(driver.page_source[:1000] + "...")
            
#             # Try to find any forms on the page
#             forms = driver.find_elements(By.TAG_NAME, "form")
#             print(f"\nFound {len(forms)} forms on the page")
#             for idx, form in enumerate(forms):
#                 try:
#                     print(f"\nForm {idx + 1}:")
#                     print(f"- ID: {form.get_attribute('id')}")
#                     print(f"- Class: {form.get_attribute('class')}")
#                     print(f"- Action: {form.get_attribute('action')}")
#                     print(f"- Method: {form.get_attribute('method')}")
#                     print("Form HTML:")
#                     print(form.get_attribute('outerHTML'))
#                 except Exception as e:
#                     print(f"Error getting form properties: {str(e)}")
            
#         except Exception as e:
#             print(f"Error getting page information: {str(e)}")
        
#         print("\nLooking for input field...")
#         # Try multiple possible selectors for the input field
#         input_selectors = [
#             "input#inputfield",  # Based on the actual page structure
#             "input[placeholder='Enter USAI ID']",  # Based on the actual page structure
#             "input[type='text']",
#             "input.captcha-input",
#             "input#captcha-input",
#             "input",
#             "[data-testid='captcha-input']",
#             "form input",
#             "input[placeholder*='captcha']",
#             "input[placeholder*='Captcha']",
#             "input[aria-label*='captcha']",
#             "input[aria-label*='Captcha']"
#         ]
        
#         # Ensure window is still open before looking for elements
#         if not ensure_window_open(driver):
#             raise Exception("Browser window closed before element search")
        
#         # Print all input elements on the page for debugging
#         try:
#             print("\nAll input elements on page:")
#             inputs = driver.find_elements(By.TAG_NAME, "input")
#             for idx, input_elem in enumerate(inputs):
#                 try:
#                     print(f"\nInput {idx + 1}:")
#                     print(f"- Type: {input_elem.get_attribute('type')}")
#                     print(f"- Class: {input_elem.get_attribute('class')}")
#                     print(f"- ID: {input_elem.get_attribute('id')}")
#                     print(f"- Name: {input_elem.get_attribute('name')}")
#                     print(f"- Placeholder: {input_elem.get_attribute('placeholder')}")
#                     print(f"- Is displayed: {input_elem.is_displayed()}")
#                     print(f"- Is enabled: {input_elem.is_enabled()}")
#                     print(f"- Location: {input_elem.location}")
#                     print(f"- Size: {input_elem.size}")
#                     print(f"- Parent HTML: {input_elem.find_element(By.XPATH, '..').get_attribute('outerHTML')}")
#                 except Exception as e:
#                     print(f"Could not get input element properties: {str(e)}")
#         except Exception as e:
#             print(f"Error finding input elements: {str(e)}")
            
#         input_field = wait_for_element_interactable(driver, input_selectors)
        
#         if input_field:
#             print("\nMoving to input field...")
#             try:
#                 if not ensure_window_open(driver):
#                     raise Exception("Browser window closed before input field interaction")
                
#                 # Try multiple methods to interact with the input field
#                 try:
#                     # Method 1: JavaScript click and focus
#                     driver.execute_script("""
#                         arguments[0].click();
#                         arguments[0].focus();
#                         // Remove any overlays
#                         var overlays = document.querySelectorAll('div[style*="position: fixed"], div[style*="position: absolute"]');
#                         overlays.forEach(function(overlay) {
#                             if (overlay.contains(arguments[0])) {
#                                 overlay.style.display = 'none';
#                             }
#                         });
#                     """, input_field)
#                     print("Clicked and focused input field using JavaScript")
#                 except Exception as e:
#                     print(f"JavaScript click failed: {str(e)}")
#                     try:
#                         # Method 2: ActionChains
#                         actions.move_to_element(input_field).click().perform()
#                         print("Clicked input field using ActionChains")
#                     except Exception as e:
#                         print(f"ActionChains click failed: {str(e)}")
#                         try:
#                             # Method 3: Direct click
#                             input_field.click()
#                             print("Clicked input field directly")
#                         except Exception as e:
#                             print(f"Direct click failed: {str(e)}")
                
#                 print("\nTyping text...")
#                 text = "HelloABC123"
#                 for char in text:
#                     if not ensure_window_open(driver):
#                         raise Exception("Browser window closed during typing")
#                     try:
#                         # Try multiple methods to send keys
#                         try:
#                             input_field.send_keys(char)
#                         except Exception as e:
#                             print(f"send_keys failed: {str(e)}")
#                             try:
#                                 # Try JavaScript
#                                 driver.execute_script(f"""
#                                     arguments[0].value += '{char}';
#                                     arguments[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
#                                     arguments[0].dispatchEvent(new Event('change', {{ bubbles: true }}));
#                                 """, input_field)
#                             except Exception as e:
#                                 print(f"JavaScript value setting failed: {str(e)}")
#                                 raise
#                         time.sleep(random.uniform(0.1, 0.3))
#                     except Exception as e:
#                         print(f"Error typing character '{char}': {str(e)}")
#                         raise
#                 print("Finished typing")
                
#                 print("\nLooking for verify button...")
#                 if not ensure_window_open(driver):
#                     raise Exception("Browser window closed before button search")
                
#                 # Print all buttons on the page for debugging
#                 try:
#                     print("\nAll buttons on page:")
#                     buttons = driver.find_elements(By.TAG_NAME, "button")
#                     for idx, button in enumerate(buttons):
#                         try:
#                             print(f"\nButton {idx + 1}:")
#                             print(f"- Text: {button.text}")
#                             print(f"- Type: {button.get_attribute('type')}")
#                             print(f"- Class: {button.get_attribute('class')}")
#                             print(f"- ID: {button.get_attribute('id')}")
#                             print(f"- Name: {button.get_attribute('name')}")
#                             print(f"- Is displayed: {button.is_displayed()}")
#                             print(f"- Is enabled: {button.is_enabled()}")
#                             print(f"- Location: {button.location}")
#                             print(f"- Size: {button.size}")
#                             print(f"- Parent HTML: {button.find_element(By.XPATH, '..').get_attribute('outerHTML')}")
#                         except Exception as e:
#                             print(f"Could not get button properties: {str(e)}")
#                 except Exception as e:
#                     print(f"Error finding buttons: {str(e)}")

#                 # Try multiple possible selectors for the verify button
#                 button_selectors = [
#                     "button[type='submit']",
#                     "button.verify-button",
#                     "button#verify-button",
#                     "button:contains('Verify')",
#                     "[data-testid='verify-button']",
#                     "form button",
#                     "button",
#                     "button.btn",
#                     "button.btn-primary",
#                     "button[class*='verify']",
#                     "button[class*='submit']",
#                     "input[type='submit']",
#                     "input[value='Verify']",
#                     "input[value='Submit']",
#                     "button:not([disabled])"
#                 ]
                
#                 verify_button = wait_for_element_interactable(driver, button_selectors)
                
#                 if verify_button:
#                     print("\nMoving to verify button...")
#                     try:
#                         if not ensure_window_open(driver):
#                             raise Exception("Browser window closed before button click")
                        
#                         # Try to make button visible and clickable
#                         try:
#                             driver.execute_script("""
#                                 arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});
#                                 var overlays = document.querySelectorAll('div[style*="position: fixed"], div[style*="position: absolute"]');
#                                 overlays.forEach(function(overlay) {
#                                     if (overlay.contains(arguments[0])) {
#                                         overlay.style.display = 'none';
#                                     }
#                                 });
#                             """, verify_button)
#                             print("Prepared button for clicking")
#                             time.sleep(1)
#                         except Exception as e:
#                             print(f"Error preparing button: {str(e)}")
                        
#                         # Try multiple methods to click the button
#                         clicked = False
                        
#                         # Method 1: JavaScript click with event dispatch
#                         try:
#                             driver.execute_script("""
#                                 arguments[0].click();
#                                 arguments[0].dispatchEvent(new MouseEvent('click', {
#                                     bubbles: true,
#                                     cancelable: true,
#                                     view: window
#                                 }));
#                             """, verify_button)
#                             print("Clicked button using JavaScript with events")
#                             clicked = True
#                         except Exception as e:
#                             print(f"JavaScript click failed: {str(e)}")
                        
#                         # Method 2: ActionChains
#                         if not clicked:
#                             try:
#                                 actions.move_to_element(verify_button)
#                                 actions.click()
#                                 actions.perform()
#                                 print("Clicked button using ActionChains")
#                                 clicked = True
#                             except Exception as e:
#                                 print(f"ActionChains click failed: {str(e)}")
                        
#                         # Method 3: Direct click
#                         if not clicked:
#                             try:
#                                 verify_button.click()
#                                 print("Clicked button directly")
#                                 clicked = True
#                             except Exception as e:
#                                 print(f"Direct click failed: {str(e)}")
                        
#                         # Method 4: Form submit
#                         if not clicked:
#                             try:
#                                 form = verify_button.find_element(By.XPATH, "./ancestor::form")
#                                 driver.execute_script("arguments[0].submit();", form)
#                                 print("Submitted form containing button")
#                                 clicked = True
#                             except Exception as e:
#                                 print(f"Form submit failed: {str(e)}")
                        
#                         if clicked:
#                             print("Button click successful!")
#                             time.sleep(20)
#                             try:
#                                 print("\nPage after button click:")
#                                 print(f"Current URL: {driver.current_url}")
#                                 print(f"Page title: {driver.title}")
#                                 messages = driver.find_elements(By.CSS_SELECTOR, ".alert, .message, .error, .success, .notification")
#                                 for msg in messages:
#                                     print(f"Found message: {msg.text}")
#                             except Exception as e:
#                                 print(f"Error checking page after click: {str(e)}")
#                         else:
#                             print("All click methods failed!")
                            
#                     except Exception as e:
#                         print(f"Error during button interaction: {str(e)}")
#                         if ensure_window_open(driver):
#                             try:
#                                 page_source = safe_get_page_source(driver)
#                                 print("\nPage source after error:")
#                                 print(page_source[:500] + "...")
#                             except Exception as e:
#                                 print(f"Could not get page source: {str(e)}")
#                 else:
#                     print("Verify button not found or not interactable!")
#                     if ensure_window_open(driver):
#                         try:
#                             page_source = safe_get_page_source(driver)
#                             print("\nPage source:")
#                             print(page_source[:500] + "...")
#                         except Exception as e:
#                             print(f"Could not get page source: {str(e)}")
#             except Exception as e:
#                 print(f"Error during interaction: {str(e)}")
#                 if ensure_window_open(driver):
#                     try:
#                         page_source = safe_get_page_source(driver)
#                         print("\nPage source:")
#                         print(page_source[:500] + "...")
#                     except Exception as e:
#                         print(f"Could not get page source: {str(e)}")
#         else:
#             print("Input field not found or not interactable!")
#             if ensure_window_open(driver):
#                 try:
#                     page_source = safe_get_page_source(driver)
#                     print("\nPage source:")
#                     print(page_source[:500] + "...")
#                 except Exception as e:
#                     print(f"Could not get page source: {str(e)}")
            
#     except Exception as e:
#         print("\n=== Error Details ===")
#         print(f"Error type: {type(e).__name__}")
#         print(f"Error message: {str(e)}")
#         print("\nFull traceback:")
#         traceback.print_exc()
#         print("===================\n")
#     finally:
#         if driver:
#             try:
#                 driver.quit()
#             except:
#                 pass



# def main():
#     # Example usage
#     tester = BotBehaviorTester(browser_type='chrome')
#     tester.simulate_bot_behavior('http://localhost:3000', num_attempts=5)

# if __name__ == "__main__":
#     # Print debug information
#     debug_info()
    
#     # Ask user which test to run
#     print("Choose test type:")
#     print("1. Human-like behavior")
#     print("2. Bot-like behavior")
#     choice = 1
#     simulate_human_behavior()
    
  
        