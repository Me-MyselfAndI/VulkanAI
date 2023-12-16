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

    def navigate_to_relevant_page(self, search_query, menu_items, threshold=5, lang='english'):
        print('Navigating in menus')
        menu_items_flattened = [
            {'item': item, 'text': item.get('text', '')} for ancestor in menu_items.values()
            for item in ancestor.get('items', [])
        ]
        gpt_evaluations = self.query_gpt_for_relevance_async(menu_items_flattened, search_query, lang=lang)
        for i, eval in enumerate(gpt_evaluations):
            menu_items_flattened[i]['score'] = eval

        print(f'Total of {len(menu_items_flattened)} items before purging')
        menu_items_flattened = [
            item for item in menu_items_flattened
            if item['score'] >= threshold and item['item']['href']
        ]

        print(f'Total of {len(menu_items_flattened)} items after purging')

        menu_items_flattened.sort(key=lambda x: -x['score'])
        # Navigate to the menu item that meets the relevance threshold
        for i, tag in enumerate(menu_items_flattened):
            item, score = tag.get('item'), tag.get('score')
            print(item, score)
            link = item.get('href', '')
            if not link:
                print('NO LINK', item)
                continue

            try:
                self.driver.get(link)
                self.handle_dropdowns(search_query)
                if self.check_page_relevance(search_query):
                    return self.driver.page_source
            except Exception as e:
                print(f"\u001b[31mError processing {link}: {e}\u001b[0m")

        print('\u001b[31mReturned None - staying on the same page\u001b[0m')
        return None

    def query_gpt_for_relevance_async(self, menu_items, search_query, lang):
        responses = self.gpt_engine.get_responses_async(
            '{}', [
                f"On a scale of 1 to 5 where 1 is completely irrelevant and 5 is the spot-on answer, how likely is it "
                f"that the menu item \"{menu_item['item'].get('text', '')}\" found in the "
                f"link \"{menu_item['item']['href']}\" contains what the query \"{search_query}\" is searching for? "
                f"Language other than \"{lang}\" automatically reduces the score to 1. Make sure the response only "
                f"consists of a number between 1 to 5, NOTHING else"
                for menu_item in menu_items
            ]
        )
        for i, response in enumerate(responses):
            try:
                responses[i] = int(response)
            except Exception:
                responses[i] = 0
                print(f'\u001b[33mWarning! GPT returned {response} for i = {i}\u001b[0m')

        return responses

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
            f"just answer with a number from 1 to 5 with 5 being a spot-on answer without distractions and 1 being "
            f"completely unrelated")
        print(is_relevant)
        return is_relevant >= "3"


if __name__ == "__main__":
    base_url = "https://www.anichart.net"
    crawler = Crawler(base_url, gpt_engine=GPTEngine())
    relevant_page_html = crawler.navigate_to_relevant_page("I want a horror isekai anime")
    print(relevant_page_html)
