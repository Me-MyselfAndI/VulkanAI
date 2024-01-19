import json

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from compression.ai.astica_engine import AsticaEngine
from compression.ai.gemini_engine import GeminiEngine
from compression.ai.gpt_assistants_engine import GPTAssistantsEngine
from compression.ai.gpt_engine import GPTEngine
from compression.ai.mistral_engine import MistralEngine

from compression.scraping.crawler import Crawler
from compression.scraping.parser import Parser


class ScrapingController:
    def __init__(self, gpt=None, astica=None, gemini=None, mistral=None, gpt_assistants=None, verbose=0):
        if gpt is None:
            self._gpt = GPTEngine(verbose=verbose)
        else:
            self._gpt = gpt

        if astica is None:
            self._astica = AsticaEngine(verbose=verbose)
        else:
            self._astica = astica

        if gemini is None:
            self._gemini = GeminiEngine(verbose=verbose)
        else:
            self._gemini = gemini

        if mistral is None:
            self._mistral = MistralEngine(verbose=verbose)
        else:
            self._mistral = mistral

        if gpt_assistants is None:
            self._gpt_assistants = GPTAssistantsEngine(verbose=verbose)
        else:
            self._gpt_assistants = gpt_assistants

    def _generate_container_html(self, products, verbose=0):
        if len(products) == 0:
            return """
            <!DOCTYPE html>
            <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>VulkanAI - Filtered Products</title>
                </head>
                <body>
                    No satisfying products could be found. Try toggling the threshold bar to loosen your requirements, or visit with a different prompt
                </body>
            </html>
            """

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
            """

        product_properties_filtered = self._gemini.get_responses_async(
            "I have a list of some product's properties and values: {}. They got scrambled, and I can't tell if some "
            "of them are property names (i.e. 'price', 'color') or values (i.e. '$55', 'red'), or combinations (i.e. "
            "'price: $55' or 'color: red'). Return this exact list, but all property names removed. The remaining stuff"
            " is to be kept intact, in the exact order. Say nothing else, just return the list",
            [product['text'] for product in products],
            temperature=0.3
        )

        for i in range(len(products)):
            products[i]['text'] = product_properties_filtered[i]

        llm_product_property_responses = self._gemini.get_responses_async(
            'This is a product with some properties I am giving you: {}. You must return me each property'
            'with its respective value, in the JSON format, nothing else. I am another bot and must be able to read '
            'your JSON without any extra efforts. If you can\'t, return 0 and nothing else',
            [product['text'] for product in products],
            temperature=0.3
        )

        product_properties_json = []
        for curr_product_properties in llm_product_property_responses:
            try:
                product_properties_json.append(json.loads(curr_product_properties.strip('```')))
            except ValueError as error:
                if verbose >= 1:
                    print(f"\u001b[33mWarning: jsonifying {curr_product_properties} yielded \"{error}\"\u001b[0m")
        for product, props in zip(products, product_properties_json):
            try:
                product_block = f"""
                    <div class="product">
                        <a href="{product['href']}" target="_blank">
                            <img src="{product['img']}" alt="{product['text']}">
                            {''.join(['<p>' + key.capitalize() + ': ' + str(value) + '</p>' for key, value in props.items()])}
                        </a>
                    </div>
                    """
                html_content += product_block
            except Exception as e:
                print(f"\u001b[31mException while generating new HTML: {e}\u001b[0m")

        html_content += """
                </div>
            </body>
            </html>
            """

        return html_content

    def _generate_text_wesite_html(self, parsed_content, search_query, threshold=3, verbose=0):
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
            if verbose >= 2:
                print(i, element['text'], response)
            if not '1' <= response < '6' or len(response) > 1:
                if verbose >= 1:
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

    def get_parsed_website_html(self, website, search_query, threshold=3, verbose=0):
        try:
            marketplace_likelihoods = self._gpt.get_responses_async(
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
                crawler = Crawler(self._gpt, cheap_llm_engine=self._gemini, verbose=verbose)
                parser = Parser(website['url'], html=website['html'], verbose=verbose)
                product_groups = parser.find_container_groups(website['url'])
                filtered_products = crawler.filter_marketplace_products(product_groups, search_query,
                                                                        threshold=threshold)
                return {
                    'status': 'ok',
                    'response': self._generate_container_html(filtered_products, verbose=verbose)
                }

            else:
                crawler = Crawler(self._gpt, verbose=verbose)
                crawled_page = crawler.navigate_to_relevant_page(search_query, website, threshold=threshold,
                                                                 lang=website.get('lang', 'english'))

                if verbose >= 2:
                    print('crawled page URL:', crawled_page['url'])
                crawled_page_parser = Parser(crawled_page['url'], html=crawled_page['html'], verbose=verbose)
                parsed_content = crawled_page_parser.find_text_content()

                return {
                    'status': 'ok',
                    'response': self._generate_text_wesite_html(parsed_content, search_query, threshold=threshold,
                                                                verbose=verbose)
                }
        except Exception as e:
            return {
                'status': 'error',
                'response': str(e)
            }


def main():
    verbose = 2

    url = 'https://www.allrecipes.com/recipes/17562/dinner/'
    search_query = 'Japanese street food'

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
            'lang': 'english'
        },
        search_query=search_query,
        threshold=3,
        verbose=verbose
    )
    print(result['response'])


if __name__ == '__main__':
    main()
