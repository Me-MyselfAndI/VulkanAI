from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from compression.ai.astica_engine import AsticaEngine
from compression.ai.gemini_engine import GeminiEngine
from compression.ai.gpt_assistants_engine import GPTAssistantsEngine
from compression.ai.gpt_engine import GPTEngine
from compression.ai.mistral_engine import MistralEngine
from compression.scraping.builder import Builder

from compression.scraping.crawler import Crawler
from compression.scraping.parser import Parser


class ScrapingController:
    def __init__(self, llm='gpt', cheap_llm='gemini', verbose=0):
        gpt_codes = {
            'gpt': GPTEngine,
            'gemini': GeminiEngine,
            'mistral': MistralEngine,
            'gpt-assistants': GPTAssistantsEngine,
        }

        self._llm = gpt_codes[llm]()
        self._cheap_llm = gpt_codes[cheap_llm]()
        self._builder = Builder(self._llm, cheap_llm=self._cheap_llm)

    def get_parsed_website_html(self, website, search_query, threshold=3, verbose=0):
        try:
            marketplace_likelihoods = self._llm.get_responses_async(
                f'Is this query {search_query} on this website {website["url"]} likely to be a marketplace? Rate the '
                f'likelihood from 1 to 5, and output nothing other than the number', [{}] * 5)

            for marketplace_likelihood in marketplace_likelihoods:
                if not '1' <= str(marketplace_likelihood) <= '5':
                    marketplace_likelihoods.remove(marketplace_likelihood)

            try:
                for i in range(len(marketplace_likelihoods)):
                    marketplace_likelihoods[i] = int(marketplace_likelihoods[i])
            except Exception as e:
                if verbose >= 1:
                    print(f"\u001b[31m Error encountered while determining marketplace vs non-marketplace: {e}")

            if sum(marketplace_likelihoods) / len(marketplace_likelihoods) >= 4:
                crawler = Crawler(self._llm, cheap_llm_engine=self._cheap_llm, verbose=verbose)
                parser = Parser(website['url'], html=website['html'], verbose=verbose)
                parsing_response = parser.find_container_groups(website['url'])
                product_groups, html_tree = parsing_response['products'], parsing_response['tree']
                filtered_products = crawler.filter_marketplace_products(product_groups, search_query, threshold=threshold)
                return {
                    'status': 'ok',
                    'response': self._builder.generate_ancestral_html(html_tree, filtered_products, verbose=verbose)
                }

            else:
                crawler = Crawler(self._llm, verbose=verbose)
                crawled_page = crawler.navigate_to_relevant_page(search_query, website, threshold=threshold,
                                                                 lang=website.get('lang', 'english'))

                if verbose >= 2:
                    print('crawled page URL:', crawled_page['url'])
                crawled_page_parser = Parser(crawled_page['url'], html=crawled_page['html'], verbose=verbose)

                parsing_response = crawled_page_parser.find_text_content()
                parsed_content, html_tree = parsing_response['items'], parsing_response['tree']

                return {
                    'status': 'ok',
                    'response': self._builder.generate_ancestral_html(html_tree, parsed_content, verbose=verbose)
                }
        except Exception as e:
            return {
                'status': 'error',
                'response': str(e)
            }


def main():
    verbose = 2

    url = 'https://nadezhdin2024.ru/#main'

    scraping_controller = ScrapingController(verbose=verbose)
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument("window-size=19200,10800")
    options.add_argument('--disable-browser-side-navigation')
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    source_html = driver.page_source


    result = scraping_controller.get_parsed_website_html(
        {
            'url': url,
            'html': source_html,
            'lang': None
        },
        'Я хочу поставить подпись за Надеждина в Комсомольске-на-Амуре',
        threshold=3,
        verbose=verbose
    )
    print("\u001b[35m", result['response'])


if __name__ == '__main__':
    main()
