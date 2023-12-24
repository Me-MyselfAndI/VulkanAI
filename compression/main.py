import json

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from compression.ai.astica_engine import AsticaEngine
from compression.ai.gemini_engine import GeminiEngine
from compression.ai.gpt_engine import GPTEngine

from compression.scraping.crawler import Crawler
from compression.scraping.parser import Parser


class ScrapingController:
    def __init__(self, gpt=None, astica=None, gemini=None):
        if gpt is None:
            self._gpt = GPTEngine()
        else:
            self._gpt = gpt

        if astica is None:
            self._astica = AsticaEngine()
        else:
            self._astica = astica

        if gemini is None:
            self._gemini = GeminiEngine()
        else:
            self._gemini = gemini



    def _generate_container_html(self, products):
        html_content = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>VulkanAI - Filtered Products</title>
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

        product_properties = self._gemini.get_responses_async(
            "This is a product with some properties I am giving you: {}. You must return me each property"
            "with its respective value, in the JSON format, nothing else", [product['text'] for product in products])

        for i in range(len(product_properties)):
            product_properties[i] = json.loads(product_properties[i].strip('```'))
        for product, props in zip(products, product_properties):
            try:
                product_block = f"""
                    <div class="product">
                        <a href="{product['href']}" target="_blank">
                            <img src="{product['img']}" alt="{product['text']}">
                            {''.join(['<p>' + key.capitalize() + ': ' + value + '</p>' for key, value in props.items()])}
                        </a>
                    </div>
                    """
            except Exception as e:
                print(e)
            html_content += product_block

        html_content += """
                </div>
            </body>
            </html>
            """

        return html_content

    def _generate_text_wesite_html(self, parsed_content, search_query, threshold=3):
        html_content = """
                        <!DOCTYPE html>
                        <html lang="en">
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>VulkanAI - Filtered Website</title>
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

        for i, element in enumerate(parsed_content):
            request = (f"On a scale of 1 to 5, how likely is it that the menu item \"{element['text']}\" contains "
                       f"what the query '{search_query}' is searching for? Make sure the response only consists of a "
                       f"number between 1 to 5, NOTHING else")
            response = self._gemini.get_response(request)
            print(i, element['text'], response)
            if not '1' <= response <= '5' or len(response) > 1:
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

    def get_parsed_website_html(self, website, search_query, threshold=4):
        try:
            marketplace_likelihood = self._gpt.get_response(
                f'Is this query {search_query} on this website {website["url"]} likely to be a marketplace? Rate the '
                f'likelihood from 1 to 5, and output nothing other than the number')

            if marketplace_likelihood >= '4':
                crawler = Crawler(self._gemini)
                parser = Parser(website['url'], html=website['html'])
                product_groups = parser.find_container_groups(website['url'])
                filtered_products = crawler.filter_marketplace_products(product_groups, search_query, threshold=3)
                return self._generate_container_html(filtered_products)

            else:
                crawler = Crawler(self._gpt)
                crawled_page = crawler.navigate_to_relevant_page(search_query, website, threshold=threshold, lang=website.get('lang', 'english'))

                print('crawled page URL:', crawled_page['url'])
                crawled_page_parser = Parser(crawled_page['url'], html=crawled_page['html'])
                parsed_content = crawled_page_parser.find_text_content()

                return {
                    'status': 'ok',
                    'response': self._generate_text_wesite_html(parsed_content, search_query, threshold=threshold)
                }
        except Exception as e:
            return {
                'status': 'error',
                'response': str(e)
            }


def main():
    scraping_controller = ScrapingController()
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument("window-size=19200,10800")
    driver = webdriver.Chrome(options=options)
    driver.get('https://www.lenovo.com/us/en/d/deals/quick-ship/')
    products_html = driver.page_source
    # with open('compression/test_input.html', encoding='utf-8') as file:
    #     products_html = file.read()

    print(scraping_controller.get_parsed_website_html(
        {
            'url': 'https://www.lenovo.com/us/en/d/deals/quick-ship/',
            'html': products_html,
            'lang': 'english'
        },
        'Laptop under 1000 usd fast delivery',
        threshold=3
    ))


if __name__ == '__main__':
    main()
