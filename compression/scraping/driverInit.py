from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
import os
import sys

class DriverInit:
    def __init__(self):

        chrome_options = Options()
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--headless=new")

        current_dir = os.path.dirname(os.path.realpath(__file__))
        parent_dir = os.path.dirname(current_dir)
        vulkanai_dir = os.path.dirname(parent_dir)
        sys.path.append(vulkanai_dir)

        # capsolver_extension_path = vulkanai_dir + "/var/www/html/compression/captcha_solver/extension" #Server Side
        capsolver_extension_path = vulkanai_dir + "/compression/captcha_solver/extension"
        # chrome_driver_path = vulkanai_dir + "/var/www/html/compression/captcha_solver/chromedriver.exe" #Server Side
        chrome_driver_path = vulkanai_dir + "/compression/captcha_solver/chromedriver.exe"

        chrome_options.add_argument(f"--load-extension={capsolver_extension_path}")
        chrome_service = Service(executable_path=chrome_driver_path)

        self.driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    def get_driver(self):
        return self.driver

    def find_selector(self, selectors):
        """Method to find an element by trying multiple selectors.

        Args:
            selectors (list): A list of CSS selectors to try.

        Returns:
            str: The first matching selector, or None if no match is found.
        """
        for selector in selectors:
            try:
                if self.driver.find_element_by_css_selector(selector):
                    return selector
            except NoSuchElementException:
                continue
        return None

    def find_pagination_selector(self):
        """Attempt to find the pagination selector on the page.

        Returns:
            str: The pagination selector if found, None otherwise.
        """
        # Common patterns for pagination elements
        pagination_selectors = [
            '.pagination',  # Common class for pagination containers
            'ul.pagination',  # Unordered list with class pagination
            'nav.pagination',  # Navigation element for pagination
            'div.pagination',  # Div containing pagination
            'ul.pager',  # Another common class for simpler paginations
        ]
        return self.find_selector(pagination_selectors)

    def find_next_button_selector(self):
        """Attempt to find the next button selector on the page.

        Returns:
            str: The next button selector if found, None otherwise.
        """
        # Common patterns for next buttons
        next_button_selectors = [
            'a.next',  # Anchor tag with class next
            'a[rel="next"]',  # Anchor tag with rel attribute set to next
            'li.next > a',  # Next within a list item
            'button.next',  # Button with class next
            'a[title*="Next"]',  # Anchor tag with title containing "Next"
        ]
        return self.find_selector(next_button_selectors)

    def check_pagination(self, pagination_selector):
        """ Check if the current page has pagination.

        Args:
            pagination_selector (str): CSS selector for the pagination element.

        Returns:
            bool: True if pagination exists, False otherwise.1
        """
        try:
            self.driver.find_element_by_css_selector(pagination_selector)
            self.has_pagination = True
        except NoSuchElementException:
            self.has_pagination = False
        return self.has_pagination

    def navigate_pagination(self, max_pages, next_button_selector):
        """ Navigate through pagination.

        Args:
            max_pages (int): The maximum number of pages to navigate.
            next_button_selector (str): CSS selector for the 'Next' button in pagination.

        Yields:
            WebDriver: The driver instance for each new page.
        """
        current_page = 0
        while current_page < max_pages:
            yield self.driver
            try:
                next_button = self.driver.find_element_by_css_selector(next_button_selector)
                next_button.click()
                current_page += 1
            except NoSuchElementException:
                break
