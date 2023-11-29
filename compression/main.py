from compression.scraping.crawler import Crawler
from compression.ai.gpt_engine import GPTEngine
from compression.scraping.parser import Parser


class ScrapingController:
    def __init__(self, gpt=None):
        if gpt is None:
            self._gpt = GPTEngine()
        else:
            self._gpt = gpt

    def get_parsed_website_html(self, website, search_query):
        parser = Parser(html=website['html'])
        menu_items = parser.find_website_menu(website['url'])

        crawler = Crawler(website['url'], self._gpt)
        crawled_page_html = crawler.navigate_to_relevant_page(search_query, menu_items)

        print("Here 1")

        crawled_page_parser = Parser(html=crawled_page_html)
        parsed_content = crawled_page_parser.find_text_content()

        threshold = 3

        html_content = """
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Filtered Website</title>
                    <style>
                        .products {
                            display: flex;
                            flex-wrap: wrap;
                            gap: 20px;
                            justify-content: center;
                        }
                        .product {
                            border: 1px solid #ddd;
                            padding: 10px;
                            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                            width: 150px;
                            text-align: center;
                        }
                        .product img {
                            max-width: 100%;
                            max-height: 100px;
                        }
                    </style>
                </head>
                <body>
                <div class="products">
            """

        # print('Text Content:\n\t', parsed_content)
        # gpt = GPTEngine(keys['gpt-api']['api-url'], keys['gpt-api']['org-url'])

        for i, element in enumerate(parsed_content):
            request = (f"On a scale of 1 to 5, how likely is it that the menu item \"{element['text']}\" contains "
                       f"what the query '{search_query}' is searching for? Make sure the response only consists of a "
                       f"number between 1 to 5, make any assumptions")
            response = self._gpt.get_response(request)
            print(i, response, '\n\t', element['text'])
            if not '1' <= response <= '5':
                print(f"\u001b[31mWARNING! BAD RESPONSE: {response}")
                continue

            if int(response) >= threshold:
                html_content += f"""
                    <div>
                        {element['tag']}
                    </div>
                    """

        html_content += """
                    </div>
                </body>
                </html>
                """

        return html_content
