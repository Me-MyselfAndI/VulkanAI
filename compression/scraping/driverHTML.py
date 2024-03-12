from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options


class DriverHTML:
    def __init__(self, url, headless=True):
        self.url = url

        chrome_options = Options()
        chrome_options.add_argument("--ignore-certificate-errors")
        if headless:
            chrome_options.add_argument("--headless=new")
        self.driver = webdriver.Chrome(options=chrome_options)

    def wait_for_page_load(self, timeout=30):
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )

    def close_modal_popups(self):
        close_button_selectors = [
            ".modal-close", ".close", ".dismiss", "[aria-label='Close']", "[aria-label='close']",
            "button.close", "div[role='dialog'] button[aria-label='Close']", "div[aria-label='Close'][role='button']",
            ".icon-close", ".icon-dismiss", "svg[aria-label='Close']", "svg.close-icon",
            "button[title='Close']", "button[title='Dismiss']", "[data-dismiss='modal']",
            "div[role='button'][aria-label='Close']", "div[role='button'][aria-label='close']", "div.close-modal",
            "span.close-modal", "a.close-modal", "i.close-modal", ".modal-header button.close",
            "button[data-dismiss='modal']", "button[data-action='close']", "a[data-action='close']",
            ".modal-content .close", ".lightbox-close", ".overlay-close", "button[aria-label='Dismiss']",
        ]

        for selector in close_button_selectors:
            try:
                close_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for button in close_buttons:
                    self.driver.execute_script("arguments[0].click();", button)
                if close_buttons:
                    break
            except Exception as e:
                continue

    def get_scrolled_html(self, scroll_count, timeout=10):
        self.driver.get(self.url)
        self.wait_for_page_load(timeout=timeout)
        self.close_modal_popups()
        initial_html = self.driver.page_source
        for _ in range(scroll_count):
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            try:
                WebDriverWait(self.driver, timeout).until(
                    lambda d: len(d.page_source) != len(initial_html)
                )
                new_html = self.driver.page_source
                initial_html = new_html
            except TimeoutException:
                break
        return self.driver.page_source

    def quit_driver(self):
        self.driver.quit()

    def fetch_page_html(self, scroll_count=0, timeout=10):
        html_content = self.get_scrolled_html(scroll_count, timeout)
        self.quit_driver()
        return html_content
