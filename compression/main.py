from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from compression.ai.astica_engine import AsticaEngine
from compression.ai.claude_engine import ClaudeEngine
from compression.ai.gemini_engine import GeminiEngine
from compression.ai.gpt_assistants_engine import GPTAssistantsEngine
from compression.ai.gpt_engine import GPTEngine
from compression.ai.mistral_engine import MistralEngine
from compression.scraping.builder import Builder

from compression.scraping.crawler import Crawler
from compression.scraping.parser import Parser

from scraping.driverHTML import DriverHTML


class ScrapingController:
    def __init__(self, llm='gpt', cheap_llm='gemini', verbose=0):
        gpt_codes = {
            'gpt': GPTEngine,
            'claude': ClaudeEngine,
            'gemini': GeminiEngine,
            'mistral': MistralEngine,
            'gpt-assistants': GPTAssistantsEngine,
        }

        self._llm = gpt_codes[llm]()
        self._cheap_llm = gpt_codes[cheap_llm]()
        self._builder = Builder(self._llm, cheap_llm=self._cheap_llm)
        self.verbose = verbose

    def get_parsed_website_html(self, website, search_query, threshold=4):
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
                if self.verbose >= 1:
                    print(f"\u001b[31m Error encountered while determining marketplace vs non-marketplace: {e}")

            if sum(marketplace_likelihoods) / len(marketplace_likelihoods) >= 4:
                crawler = Crawler(self._llm, verbose=self.verbose)
                parser = Parser(website['url'], html=website['html'], verbose=self.verbose)
                parsing_response = parser.find_container_groups(website['url'])
                product_groups, html_tree = parsing_response['products'], parsing_response['tree']
                filtered_products = crawler.filter_marketplace_products(product_groups, search_query, threshold=threshold)
                if len(filtered_products) == 0:
                    return {
                        'status': 'empty-result',
                        'response': self._builder.get_empty_page()
                    }
                result = self._builder.generate_ancestral_html(html_tree, filtered_products, verbose=self.verbose)
                return {
                    'status': 'ok',
                    'response': result
                }

            else:
                crawler = Crawler(self._llm, verbose=self.verbose)
                crawled_page = crawler.navigate_to_relevant_page(search_query, website, threshold=threshold,
                                                                 lang=website.get('lang', 'english'))

                if self.verbose >= 2:
                    print('crawled page URL:', crawled_page['url'])
                crawled_page_parser = Parser(crawled_page['url'], html=crawled_page['html'], verbose=self.verbose)

                parsing_response = crawled_page_parser.find_text_content()
                parsed_content, html_tree = parsing_response['items'], parsing_response['tree']
                if len(parsed_content) == 0:
                    return {
                        'status': 'empty-result',
                        'response': self._builder.get_empty_page()
                    }
                return {
                    'status': 'ok',
                    'response': self._builder.generate_ancestral_html(html_tree, parsed_content, verbose=self.verbose)
                }
        except Exception as e:
            return {
                'status': 'error',
                'response': str(e)
            }


def main():
    verbose = 2

    url = 'https://atlanta.craigslist.org/search/atlanta-ga/cta'

    scraping_controller = ScrapingController(verbose=verbose)
    driver = DriverHTML(url, headless=False)
    source_html = driver.fetch_page_html(scroll_count=5, timeout=10)

    result = scraping_controller.get_parsed_website_html(
        {
            'url': url,
            'html': source_html,
            'lang': None
        },
        'Used Japanese sedan under 150k miles',
        threshold=3
    )
    print("\u001b[35m", result['response'])


if __name__ == '__main__':
    main()
