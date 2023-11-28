from compression.scraping.crawler import Crawler
from compression.ai.gpt_engine import GPTEngine


class ScrapingController:
    def __init__(self, gpt=None):
        if gpt is None:
            self._gpt = GPTEngine()
        else:
            self._gpt = gpt

    def get_parsed_website_html(self, website, search_query):
        crawler = Crawler(website['url'], self._gpt)
        result = crawler.navigate_to_relevant_page(search_query)

        return result
def main():
    with open('scraping/test.html') as file:
        website = file.read()

    ScrapingController().get_parsed_website_html()

if __name__ == '__main__':
    main()
