from compression.ai.astica_engine import AsticaEngine
from compression.scraping.crawler import Crawler
from compression.ai.gpt_engine import GPTEngine
from compression.scraping.parser import Parser


class ScrapingController:
    def __init__(self, gpt=None, astica=None):
        if gpt is None:
            self._gpt = GPTEngine()
        else:
            self._gpt = gpt

        if astica is None:
            self._astica = AsticaEngine()
        else:
            self._astica = astica

    def _filter_marketplace_products(self, product_info, search_query, threshold=3):
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

        print("Products with descriptions:")
        for i, product in enumerate(nonempty_description_products):
            print(i, product)

        astica_descriptions = []
        for i, (product, (astica_response_code, astica_result)) in enumerate(
            zip(
                nonempty_description_products,
                self._astica.get_image_descriptions_async(list(map(lambda x: x['img'], nonempty_description_products)))
            )
        ):
            try:
                if astica_response_code != 200:
                    print(f'\u001b[31mAstica returned code {astica_response_code} on this product; error message: {astica_result}\n skipping\u001b[0m')
                    astica_descriptions.append(f'NO IMAGE-BASED DESCRIPTION: {astica_result}')
                else:
                    astica_descriptions.append(astica_result)
            except Exception as e:
                print(f'\u001b[31mException {e} encountered with this product; skipping\u001b[0m')
                astica_descriptions.append(
                    f'NO IMAGE-BASED DESCRIPTION')

        args = []
        for product, astica_description in zip(nonempty_description_products, astica_descriptions):
            prompt = (f"Given the user's preference of '{search_query}', how well does the product "
                      f"with data '{product['text']}' and described as '{astica_description}' match the "
                      f"criteria? Answer from 1 to 5 where 5 is the exact match and 1 is completely irrelevant. "
                      f"You are only allowed to give the number, nothing else")
            args.append(prompt)
        gpt_responses = self._gpt.get_responses_async('{}', args=args)

        for i, (product, gpt_response) in enumerate(zip(nonempty_description_products, gpt_responses)):
            try:
                if not '1' <= gpt_response <= '5' or len(gpt_response) > 1:
                    print(f"\u001b[31mWARNING! BAD RESPONSE: {gpt_response}")
                    gpt_response = 0

                gpt_response = int(gpt_response)
                print(product, gpt_response, "\n")

                if gpt_response >= threshold:
                    filtered_products.append(product)
            except Exception as e:
                print(f'\u001b[31mException {e} encountered with this product; skipping\u001b[0m')
                continue
        return filtered_products

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

        product_titles = self._gpt.get_responses_async(
            "A product in a marketplace has properties: {}. Some of it is the title. Find it, "
            "and print. Give NO other text aside from what I asked. ", [product['text'] for product in products]
        )
        for product, product_title in zip(products, product_titles):
            product_block = f"""
                <div class="product">
                    <a href="{product['href']}" target="_blank">
                        <img src="{product['img']}" alt="{product['text']}">
                        <p>{product_title}</p>
                    </a>
                </div>
                """
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
            response = self._gpt.get_response(request)
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

    def get_parsed_website_html(self, website, search_query):
        parser = Parser(html=website['html'])

        marketplace_likelihood = self._gpt.get_response(
            f'Is this query {search_query} on this website {website["url"]} likely to be a marketplace? Rate the '
            f'likelihood from 1 to 5, and output nothing other than the number')
        if marketplace_likelihood >= '4':
            product_groups = parser.find_container_groups(website['url'])
            filtered_products = self._filter_marketplace_products(product_groups, search_query)
            return self._generate_container_html(filtered_products)

        else:
            menu_items = parser.find_website_menu(website['url'])

            crawler = Crawler(website['url'], self._gpt)
            crawled_page_html = crawler.navigate_to_relevant_page(search_query, menu_items, lang=website.get('lang', 'english'))

            if crawled_page_html is None:
                crawled_page_html = website['html']

            print('crawled page:', crawled_page_html)
            crawled_page_parser = Parser(html=crawled_page_html)
            parsed_content = crawled_page_parser.find_text_content()

            threshold = 3

            return self._generate_text_wesite_html(parsed_content, search_query, threshold=threshold)


def main():
    scraping_controller = ScrapingController()
    with open('compression/test_input.html', encoding='utf-8') as file:
        products_html = file.read()
    print(scraping_controller.get_parsed_website_html(
        {
            'url': 'https://www.coolmathgames.com/blog/how-to-play-snake-mastering-a-classic',
            'html': products_html,
            'lang': 'english'
        },
        'Snake game - how to play it in depth and what is it'
    ))


if __name__ == '__main__':
    main()
