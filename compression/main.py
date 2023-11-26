from compression.scraping.parser import Parser
from compression.scraping.crawler import Crawler
from compression.ai.gpt_engine import GPTEngine

class ScrapingController:
    def __init__(self):
        self.gpt = GPTEngine('')

    def get_parsed_website_html(self, website, search_query):
        # website: {
        #     'url': website,
        #     'html': html
        # }
