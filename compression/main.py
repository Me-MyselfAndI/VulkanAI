from compression.scraping.parser import Parser
from compression.scraping.crawler import Crawler
from compression.ai.gpt_engine import GPTEngine

class ScrapingController:
    def __init__(self):
        self.gpt = GPTEngine()
        # self.astica = AsticaEngine()

    def get_parsed_website_html(self, website, search_query):
        # website: {
        #     'url': website,
        #     'html': html
        # }
        parser = Parser(website['html'])
        menu_items = parser.find_website_menu(website['url'])

        crawler = Crawler(website['url'], self.gpt)
        return crawler.navigate_to_relevant_page(search_query, menu_items)
