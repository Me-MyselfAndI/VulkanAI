# crawler.py
import compression.scraping.parser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


class Crawler:
    def __init__(self, base_url, gpt_engine):
        self.base_url = base_url
        self.gpt_engine = gpt_engine
        options = Options()
        options.add_argument('--headless=new')
        self.driver = webdriver.Chrome(options=options)

    def navigate_to_relevant_page(self, search_query, menu_items_dict):
        all_menu_items = [item for value in menu_items_dict.values() for item in value.get('items', [])]

        sorted_items = sorted(all_menu_items, key=lambda item: self.gpt_engine.get_response(
            f"How relevant is '{item.get('text', '').strip()}' to the query '{search_query}'?"))

        for item in sorted_items:
            link = item.get('href')
            if not link:
                continue

            try:
                self.driver.get(link)
                self.handle_dropdowns(search_query)
                if self.check_page_relevance(search_query):
                    return self.driver.page_source

            except Exception as e:
                print(f"Error processing {link}: {e}")

        return None

    def handle_dropdowns(self, search_query):
        dropdowns = self.driver.find_elements(By.TAG_NAME, 'select')
        for dropdown in dropdowns:
            options = dropdown.find_elements(By.TAG_NAME, 'option')
            options_texts = [option.text for option in options]
            most_viable_option = self.gpt_engine.get_response(
                f"Given the query '{search_query}', which of these options is most relevant: {options_texts}? Only Answer with the exact option")
            for option in options:
                if option.text == most_viable_option:
                    option.click()
                    break
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*')))

    def check_page_relevance(self, search_query):
        is_relevant = self.gpt_engine.get_response(
            f"Is this page '{self.driver.current_url}' relevant to the query '{search_query}'? Respond with Yes or No")
        return is_relevant == "Yes"
