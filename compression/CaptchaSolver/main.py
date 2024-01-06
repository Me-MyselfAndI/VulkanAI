import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def main():
    current_working_directory = os.getcwd()
    capsolver_extension_path = current_working_directory + "/extension"
    chrome_driver_path = current_working_directory + "/chromedriver.exe"
    chrome_service = Service(executable_path=chrome_driver_path)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f"--load-extension={capsolver_extension_path}")
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    driver.get("https://www.google.com/recaptcha/api2/demo")
    wait = WebDriverWait(driver, timeout=100)

    # Wait for the reCAPTCHA iframe and switch to it
    frames = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "iframe")))
    driver.switch_to.frame(frames[0])

    # Wait for the reCAPTCHA checkbox to be clickable (which might indicate that the CAPTCHA is solved)
    wait.until(EC.element_to_be_clickable((By.ID, "recaptcha-anchor")))

    # Switch back to the main content if needed
    driver.switch_to.default_content()

    # Additional actions can be performed here after the CAPTCHA is solved

    time.sleep(5)  # Small delay before quitting, adjust as needed
    driver.quit()


main()