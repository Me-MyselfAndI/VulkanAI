from compression.scraping.parser import Parser
from compression.scraping.crawler import Crawler
from compression.ai.gpt_engine import GPTEngine


class ScrapingController:
    def __init__(self, gpt=None):
        if gpt is None:
            self._gpt = GPTEngine()
        else:
            self._gpt = gpt

    def get_parsed_website_html(self, website, search_query):
        parser = Parser(website['html'])
        print("HERE1")
        menu_items = parser.find_website_menu(website['url'])
        print("HERE2")

        crawler = Crawler(website['url'], self._gpt)
        print("HERE3")
        result = crawler.navigate_to_relevant_page(search_query, menu_items)
        print("HERE4")

        return result
def main():
    with open('scraping/test.html') as file:
        website = file.read()

    ScrapingController().get_parsed_website_html()

if __name__ == '__main__':
    main()
