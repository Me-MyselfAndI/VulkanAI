import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from compression.scraping.parser import Parser

import sys
import os

chrome_options = Options()
chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument("--headless=new")

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
vulkanai_dir = os.path.dirname(parent_dir)
sys.path.append(vulkanai_dir)#Local Side

#capsolver_extension_path = "/var/www/html/compression/captcha_solver/extension" #Server Side
capsolver_extension_path = vulkanai_dir + "/compression/captcha_solver/extension" #Local Side
#chrome_driver_path = "/var/www/html/compression/captcha_solver/chromedriver" #Server Side
chrome_driver_path = vulkanai_dir + "/compression/captcha_solver/chromedriver.exe" #Local Side
chrome_service = Service(executable_path=chrome_driver_path)
chrome_options.add_argument(f"--load-extension={capsolver_extension_path}")


class Crawler:
    def __init__(self, llm_engine, verbose=0):
        self.verbose = verbose
        self.llm_engine = llm_engine
        self.driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    def get_page_source(self, url):
        self.driver.get(url)
        return self.driver.page_source

    def handle_popup_alert(self, search_query, timeout=10):
        try:
            WebDriverWait(self.driver, timeout).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            alert_text = alert.text

            response = self.llm_engine.get_response(
                f"Given the query '{search_query}', which of these options is most relevant to the alert "
                f"'{alert_text}': accept or dismiss? Only Answer with the exact option")

            decision = response.choices[0].text.strip().lower()

            if "dismiss" in decision:
                alert.dismiss()
            else:
                alert.accept()

            return True
        except TimeoutException:
            return False

    def filter_marketplace_products(self, product_info, search_query, threshold=3, llm_request_batching_quantity=8, num_repeats=4):
        self.handle_popup_alert(search_query)
        if self.verbose >= 2:
            print(f"Products ({len(product_info)}):")
            for i, product in enumerate(product_info):
                print(i, product)

        filtered_products = []
        nonempty_description_products = []
        for i, product in enumerate(product_info):
            # Filter out all fully-empty items
            for text_piece in product['text']:
                if text_piece.strip() != '':
                    break
            else:
                continue
            nonempty_description_products.append(product)

        if self.verbose >= 2:
            print("Products with descriptions:")
            for i, product in enumerate(nonempty_description_products):
                print(i, product)


        args = []
        for product in nonempty_description_products:
            product_str = '['
            for property in product['text']:
                product_str += property + ";"
            if len(product_str) > 0:
                product_str = product_str[:-1] + ']'
            args.append(product_str)

        args = self.llm_engine.get_responses_async(
            f'I give you list of product properties and values: {{}}. You need to compress the number of tokens here'
            f'for the purpose of evaluating relevance for {search_query}. You do this in two primary ways: by removing'
            f'information irrelevant for making this decision and by bundling together properties that belong together '
            f'(such as when a property name is separated from its value). Return compressed description and nothing else',
            args=args,
            use_cheap_model=True
        )
        batched_args = [args[i * llm_request_batching_quantity: (i + 1) * llm_request_batching_quantity] for i in range(len(args) // llm_request_batching_quantity)]

        llm_responses = []
        for i in range(num_repeats):
            batched_llm_responses = self.llm_engine.get_responses_async(
                f'Customer looking for"{search_query}".Rank each and every product in "{{}} " from 1(terrible match for request) to '
                f'5(perfect match). RETURN JSON AND ONLY JSON FOR EACH OBJECT COUNTING FROM 0 LIKE ' + '{{"0":3,"1":4,"2":4,...}}',
                args=batched_args,
                timeout=20 * llm_request_batching_quantity
            )

            curr_llm_responses = []
            for i, curr_batched_llm_responses in enumerate(batched_llm_responses):
                try:
                    curr_batched_llm_responses = json.loads(curr_batched_llm_responses.lower().strip('```').strip('\'').strip('"').strip("json").strip('\n'))
                except Exception as error:
                    # Retrying
                    try:
                        curr_batched_llm_responses = json.loads(
                            curr_batched_llm_responses.lower().strip('```').strip('\'').strip('"').strip("json").strip('\n')
                        )
                    except Exception as error:
                        if self.verbose >= 1:
                            print(f"\u001b[33mError encountered while converting llm responses to json: {error}\u001b[0m")
                        curr_llm_responses.extend(['1'] * llm_request_batching_quantity)
                        continue

                for curr_key in range(llm_request_batching_quantity):
                    if str(curr_key) not in curr_batched_llm_responses:
                        if self.verbose >= 2:
                            print(f"\u001b[33mWarning: llm response {curr_key} could not be found in batch #{i}\u001b[0m")
                        curr_llm_responses.append('1')
                        continue
                    try:
                        curr_llm_responses.append(str(curr_batched_llm_responses[str(curr_key)]))
                    except Exception as error:
                        if self.verbose >= 1:
                            print(f"\u001b[31mError encountered while converting llm response {curr_key} in batch {i}: {error}\u001b[0m")
                        curr_llm_responses.append('1')

            try:
                curr_llm_responses = list(map(lambda x: int(x), curr_llm_responses))
            except Exception:
                if self.verbose >= 1:
                    print(f"\u001b[31mError encountered while making llm response {curr_key} integer in batch {i}: {error}\u001b[0m")
                curr_llm_responses.append('1')

            if len(llm_responses) == 0:
                llm_responses = curr_llm_responses
            else:
                llm_responses_len = len(llm_responses)
                for i in range(len(curr_llm_responses)):
                    llm_responses[i] = (llm_responses[i] * llm_responses_len + curr_llm_responses[i]) / (llm_responses_len + 1)

        for i, (product, llm_response) in enumerate(zip(nonempty_description_products, llm_responses)):
            try:
                if not 0 <= llm_response < 6:
                    if self.verbose >= 1:
                        print(f"\u001b[31mWarning when converting llm responses into kept products! BAD RESPONSE: {llm_response}")
                    llm_response = 0

                llm_response = int(llm_response)
                if self.verbose >= 2:
                    print(product, llm_response, "\n")

                if llm_response >= threshold:
                    filtered_products.append(product)
            except Exception as e:
                if self.verbose >= 1:
                    print(f'\u001b[31mException "{e}" encountered with product {product} and llm response {llm_response}; skipping\u001b[0m')
                continue
        return filtered_products

    def navigate_to_relevant_page(self, search_query, website, threshold=4, min_relevance_rate=0.15, max_recursion_depth=2, lang='english'):
        self.handle_popup_alert(search_query)
        parser = Parser(website['url'], html=website['html'])
        compressed_original_page_tags = parser.find_text_content()['items']
        page_content_relevance = self.query_llm_for_text_relevance(compressed_original_page_tags, search_query)
        curr_page_relevance_rate = len([1 for item in page_content_relevance if item >= threshold]) / len(page_content_relevance)
        if max_recursion_depth == 0 or curr_page_relevance_rate >= min_relevance_rate:
            return {
                'relevance': curr_page_relevance_rate,
                'url': website['url'],
                'html': website['html']
            }

        menu_items = parser.find_website_menu()

        if self.verbose >= 2:
            print('Navigating in menus')
        menu_items_flattened = [
            {'item': item, 'text': item.get('text', '')} for ancestor in menu_items.values()
            for item in ancestor.get('items', [])
        ]
        llm_evaluations = self.query_llm_menus_for_relevance(menu_items_flattened, search_query, lang=lang)
        for i, eval in enumerate(llm_evaluations):
            menu_items_flattened[i]['score'] = eval

        if self.verbose >= 2:
            print(f'Total of {len(menu_items_flattened)} items before purging')
        menu_items_flattened = [
            item for item in menu_items_flattened
            if item['score'] >= threshold and item['item']['href']
        ]

        if self.verbose >= 2:
            print(f'Total of {len(menu_items_flattened)} items after purging')

        menu_items_flattened.sort(key=lambda x: -x['score'])
        # Navigate to the menu item that meets the relevance threshold
        for i, tag in enumerate(menu_items_flattened):
            item, score = tag.get('item'), tag.get('score')
            if self.verbose >= 2:
                print(item, score)
            link = item.get('href', '')
            if not link:
                if self.verbose >= 2:
                    print('NO LINK', item)
                continue

            try:
                self.driver.get(link)
                self.handle_dropdowns(search_query)
                new_website = {
                    'url': link,
                    'html': self.driver.page_source
                }
                result = self.navigate_to_relevant_page(
                    search_query, new_website,
                    max_recursion_depth=max_recursion_depth-1,
                    threshold=threshold,
                    min_relevance_rate=min_relevance_rate, lang=lang
                )

                if result['relevance'] > curr_page_relevance_rate:
                    return result
                else:
                    return {
                        'relevance': curr_page_relevance_rate,
                        'url': website['url'],
                        'html': website['html']
                    }

            except Exception as e:
                if self.verbose >= 1:
                    print(f"\u001b[31mError processing {link}: {e}\u001b[0m")

        if self.verbose >= 2:
            print('\u001b[31mReturned None - staying on the same page\u001b[0m')
        return {
            'relevance': curr_page_relevance_rate,
            'url': website['url'],
            'html': website['html']
        }

    def query_llm_menus_for_relevance(self, menu_items, search_query, lang):
        responses = self.llm_engine.get_responses_async('{}', [
            f"How likely is menu item \"{menu_item['item'].get('text', '')}\" "
            f"answers \"{search_query}\" Non-\"{lang}\" rejected. Respond number 1-5, NOTHING else AT ALL ASIDE FROM NUMBER"
            for menu_item in menu_items
        ])
        for i, response in enumerate(responses):
            try:
                responses[i] = int(response)
            except Exception:
                responses[i] = 0

                if self.verbose >= 1:
                    print(f'\u001b[33mWarning! GPT returned {response} for i = {i}\u001b[0m')

        return responses

    def query_llm_for_text_relevance(self, text_items, search_query):
        responses = self.llm_engine.get_responses_async('{}', [
            f"How relevant is the menu item \"{text_item['text']}\" query \"{search_query}\"? "
            f"Only give number 1-5, NOTHING else"
            for text_item in text_items
        ])
        for i, response in enumerate(responses):
            try:
                responses[i] = int(response)
            except Exception:
                responses[i] = 0
                if self.verbose >= 1:
                    print(f'\u001b[33mWarning! GPT returned {response} for i = {i}\u001b[0m')

        return responses

    def handle_dropdowns(self, search_query):
        dropdowns = self.driver.find_elements(By.TAG_NAME, 'select')
        for dropdown in dropdowns:
            options = dropdown.find_elements(By.TAG_NAME, 'option')
            options_texts = [option.text for option in options]
            most_viable_option = self.llm_engine.get_response(
                f"Given query '{search_query}', which option most relevant: {options_texts}? Only answer with this exact option")
            for option in options:
                if option.text == most_viable_option:
                    option.click()
                    break
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*')))
