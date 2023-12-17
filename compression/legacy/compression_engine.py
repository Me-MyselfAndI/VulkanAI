import yaml

from compression.ai.astica_engine import AsticaEngine
from compression.ai.gpt_engine import GPTEngine
from compression.scraping.parser import Parser
from selenium import webdriver
from urllib.parse import urljoin, urlparse


class CompressionEngine:
    def __init__(self, secrets_filename=r'../keys/keys.yaml'):
        with open(secrets_filename) as keys_file:
            keys = yaml.load(keys_file, yaml.FullLoader)['keys']['compression']['ai']

            self.gpt_engine = GPTEngine(keys['gpt-api']['api-url'], keys['gpt-api']['org-url'])
            self.astica_engine = AsticaEngine(keys['astica-api'])

        self.parser = Parser()

    def _get_marketplace_product_info(self, url):
        driver = webdriver.Chrome()
        driver.get(url)
        products = self.parser.find_marketplace_product_groups(html=driver.page_source)
        driver.quit()
        return products

    def generate_container_html(self, url, output_file="test_input.html"):
        html_content = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Amazon Products</title>
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

        products = self._get_marketplace_product_info(url)
        product_titles = self.gpt_engine.get_responses_async(
            "A product in a marketplace has properties: {}. Some of it is the title. Find it, "
            "and print. Give NO other text aside from what I asked. ", [product['text'] for product in products])
        for product, product_tile in zip(products, product_titles):
            product_block = f"""
                <div class="product">
                    <a href="{product['href']}" target="_blank">
                        <img src="{product['img']}" alt="{product['text']}">
                        <p>{product_tile}</p>
                    </a>
                </div>
                """
            html_content += product_block

        html_content += """
                </div>
            </body>
            </html>
            """

        with open(output_file, "w", encoding='utf-8') as file:
            file.write(html_content)
            print("Saved")

        return html_content