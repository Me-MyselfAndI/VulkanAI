from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from compression.scraping.parser import Parser

from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument("--headless")

import sys
import os

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
vulkanai_dir = os.path.dirname(parent_dir)
sys.path.append(vulkanai_dir)

from compression.ai.gpt_engine import GPTEngine


class Crawler:
    def __init__(self, base_url, gpt_engine):
        self.base_url = base_url
        self.gpt_engine = gpt_engine
        options = Options()
        options.add_argument('--headless=new')
        self.driver = webdriver.Chrome(options=options)

    def get_page_source(self, url):
        self.driver.get(url)
        return self.driver.page_source

    def navigate_to_relevant_page(self, search_query):
        html_content = self.get_page_source(self.base_url)
        print(0)
        parser = Parser(html=html_content)
        print(1)
        menu_items_dict = parser.find_website_menu(self.base_url)

        print(2)
        all_menu_items = [item for ancestor in menu_items_dict.values() for item in ancestor.get('items', [])]
        print(3, len(all_menu_items))

        best_score = -1
        all_menu_items.sort(key=lambda x: -self.query_gpt_for_relevance(x.get('text', ''), search_query))
        # Navigate to the menu item that meets the relevance threshold
        for i, item in enumerate(all_menu_items):
            menu_text = item.get('text', '').strip()
            print(item)
            link = item.get('href')
            if not link:
                print('NO LINK', item)
                continue

            try:
                print(4)
                self.driver.get(link)
                print(5)
                self.handle_dropdowns(search_query)
                print(6)
                if self.check_page_relevance(search_query):
                    print(7)
                    return self.driver.page_source
            except Exception as e:
                print(f"\u001b[31mError processing {link}: {e}\u001b[0m")

        return None

    def query_gpt_for_relevance(self, menu_text, search_query):
        response = self.gpt_engine.get_response(
            f"On a scale of 1 to 5, how likely is it that the menu item '{menu_text}' contains what the query '{search_query}' is searching for? Make sure the response only consists of a number between 1 to 5, make any assumptions")

        print('\t', menu_text, response)
        try:
            response = int(response)
        except Exception:
            return 0

        return response

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
            f"Is this page '{self.driver.current_url}' relevant to the query '{search_query}'? Do not type anything, "
            f"just answer with a number from 1 to 5 with 5 being a spot-on answer and 1 being completely unrelated")
        return is_relevant >= "3"


if __name__ == "__main__":
    base_url = "https://www.anichart.net"
    crawler = Crawler(base_url, gpt_engine=GPTEngine())
    relevant_page_html = crawler.navigate_to_relevant_page("I want a horror isekai anime")
    print(relevant_page_html)
